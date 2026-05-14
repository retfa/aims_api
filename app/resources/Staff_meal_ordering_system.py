#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import timedelta
from sqlalchemy import text

import requests
import json

from collections import defaultdict


# In[ ]:


import logging
logger = logging.getLogger(__name__)  # 取得和主程式共用的 logger


# In[ ]:


# 員工訂餐系統


# In[ ]:


# 入口HC050I1
# 客飯查詢 HC051I2 小視窗HC051I6 客飯訂購 HC022A2
# 個人匯總 HC051I1
# 彙總用餐文字檔 HC051I8


# In[ ]:


class Staff_meal_ordering_query:
    def __init__(self, servers, redis_client=None):
        self.servers = servers     
        self.redis_client = redis_client
        
    # -------------------------
    # Redis key helper
    # -------------------------
    def _day_cache_key(self, bdate: datetime.date):
        return f"staff_meal_order:day:{bdate.strftime('%Y-%m-%d')}"

    def _month_cache_key(self, year: int, month: int):
        return f"staff_meal_order:month:{year}-{month:02d}" 

    # -------------------------
    # 取/存快取
    # -------------------------
    def _get_cache(self, key):
        if not self.redis_client:
            return None
        data = self.redis_client.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except Exception:
            logger.error(f"Invalid JSON in Redis key: {key}")
            return None

    def _set_cache(self, key, data, ttl):
        if self.redis_client:
            self.redis_client.set(key, json.dumps(data), ex=ttl)
            logger.info(f"Set Redis cache: {key}")
            
    # -------------------------
    # 刪除當日快取
    # -------------------------
    def invalidate_day_cache(self, bdate: datetime.date):
        if not self.redis_client:
            return
        key = self._day_cache_key(bdate)
        self.redis_client.delete(key)
        logger.info(f"Deleted Redis cache: {key}")
            
    # -------------------------
    # 過濾資料
    # -------------------------            
            
    def _filter_data(self, data, cardno, code, dn, food, OG_name):
        def match(row):
            if cardno and row.get("cardno") != cardno:
                return False
            if code and row.get("code") != code:
                return False
            if dn and row.get("dn") != dn:
                return False
            if food and str(row.get("food")) != str(food):
                return False
            if OG_name and str(row.get("OG_name")) != str(OG_name):
                return False            
            return True

        return [row for row in data if match(row)]            

    def fetch(self, year: str, month: str, day: str, cardno: str, code: str, dn: str, food: str, OG_name: str): 
        """
        查詢員工餐點資料，支援 Redis 快取 + SQL 備援 + Python 條件篩選
        """        
        startTime = time.time()

        # 基本參數檢查        
        if not year:
            return {'success': False, 'message': 'Missing year parameter'}
        if not month:
            return {'success': False, 'message': 'month year parameter'}
        
        try:
            year = int(year)
            month = int(month)
            if day:
                day = int(day)
        except Exception as e:
            return {'success': False, 'message': f'Invalid date parameter: {e}'}        
        
        now = datetime.datetime.now()
        today_date = now.date()

        month_key = self._month_cache_key(year, month)
        
        if day:
            query_date = datetime.date(year, month, day)
            day_key = self._day_cache_key(query_date)
        else:
            query_date = None
            day_key = None

        data = []     
        
        # =========================
        # Case 1：查「指定日」
        # =========================      
        if day:
            cached = self._get_cache(day_key)

            if cached:
                logger.info(f"Hit day cache: {day_key}")
                data = cached["data"]

            else:
                data = self._query_db(year, month, day, cardno=None, code=None, dn=None, food=None, OG_name=None)

                # 👉 今日資料短 TTL，其它長 TTL
                # 只存非未來日期
                if query_date <= today_date:
                    ttl = 120 if query_date == today_date else 28800
                    self._set_cache(day_key, {"data": data}, ttl)
                
        # =========================
        # Case 2：查「整月」
        # =========================
        else:
            cached = self._get_cache(month_key)

            if cached:
                logger.info(f"Hit month cache: {month_key}")
                data = cached["data"]

            else:
                # 👉 只查到昨天
                data = self._query_db(year, month, day=None,
                                      cardno=None, code=None, dn=None, food=None, OG_name=None,
                                      until_yesterday=True)

                self._set_cache(month_key, {"data": data}, 28800)

            # 👉 如果是當月 → 補今天
            if int(year) == now.year and int(month) == now.month:
                
                today_key = self._day_cache_key(today_date)
                today_cache = self._get_cache(today_key)

                if today_cache:
                    logger.info(f"Hit today cache: {today_key}")
                    data += today_cache["data"]
                else:
                    today_data = self._query_db(year, month, day=today_date.day,
                                                cardno=None, code=None, dn=None, food=None, OG_name=None)

                    self._set_cache(today_key, {"data": today_data}, 120)
                    data += today_data

        # =========================
        # 🔥 最後才 filter（關鍵）
        # =========================
        data = self._filter_data(data, cardno, code, dn, food, OG_name)

        ExecutionTime = time.time() - startTime
        logger.info(f"ExecutionTime: {ExecutionTime:.3f} sec")

        return {"data": data}  
    
    def _query_db(self, year, month, day=None, cardno=None, code=None, dn=None, food=None, OG_name=None, until_yesterday=False):

        df = pd.DataFrame()

        try:
            srv = self.servers['SRVMESDBA1']
            with srv['create_engine'][0].connect() as conn:
                
                # 動態條件部分
                conditions = []
                conditions_2 = []
                params = {"year": year, "month": month}

                if day:
                    conditions.append("AND DAY(bdate) = :day")
                    params["day"] = day

                if until_yesterday:
                    conditions.append("AND bdate < CAST(GETDATE() AS DATE)")
                    
                if code:
                    conditions_2.append("AND code = :code")
                    params["code"] = code
                if dn:
                    conditions_2.append("AND dn = :dn")
                    params["dn"] = dn
                if food is not None and food != "":
                    conditions_2.append("AND food = :food")
                    params["food"] = int(food)       
                    
                if OG_name is not None and OG_name != "":
                    conditions_2.append("AND OG_Name = :OG_name")
                    params["OG_name"] = int(OG_name)                       

                # ❗注意：這裡不要加 cardno/code（避免 cache 失效）

                extra_conditions = "\n".join(conditions)
                extra_conditions_2 = "\n".join(conditions_2)

                sql = f"""
;WITH raw_data AS
(
    SELECT [YEAR], [MONTH], [DAY],cardno,chsnm,place,code,Category as category,cktime,dn, OG_Name as OG_name, food ,sid
    FROM
    (
        SELECT *,ROW_NUMBER() OVER (PARTITION BY [YEAR], [MONTH], [DAY], cardno,dn Order By cktime DESC) as amount
        FROM
        (
            SELECT [YEAR], [MONTH], [DAY], cardno, ID, chsnm, place , code, Category, dn, OG_Name, food, max(cktime) as cktime, max(sid) as sid
            FROM
            (
                SELECT a.*,b.chsnm,c.chsnm as place, c.code, d.OG_Name,
                    CASE WHEN right(a.Category,1) = 2 THEN 2
                            WHEN right(a.Category,1) = 3 THEN 3 ELSE right(b.food,1) END AS food
                FROM
                (
                    SELECT
                        YEAR(bdate) AS [YEAR],MONTH(bdate) AS [MONTH], DAY(bdate) AS [DAY],
                        [idx],[sid],
                        CASE WHEN [cardno] IN ('A0005','A0010','A0000') THEN 'A' + [ID] ELSE [cardno] END AS [cardno],
                        [dn],[cktime],[bdate],[loca],[locaName],[Category],[ID],
                        [nad],[CardSN],[DateTime]
                    FROM [HR].[dbo].[hdeatlog]
                    where 1=1
                    AND len(cardno)>1
                    AND [dn] != '99'
                    AND YEAR(bdate) = :year
                    AND MONTH(bdate) = :month
                    {extra_conditions}
                ) a
                left join [SRVAD6].[HR].[dbo].[hmstaff] b on a.cardno = b.emp_id COLLATE Chinese_Taiwan_Stroke_CI_AS
                left join [SRVAD6].[HR].[dbo].[hdMfood_place] c on b.food_place=c.code COLLATE Chinese_Taiwan_Stroke_CI_AS
                left join [SRVAD6].[HR].[dbo].[hdtree] d on b.team_sn=d.OG_MID COLLATE Chinese_Taiwan_Stroke_CI_AS
                where 1=1
                and b.chsnm is not null
            ) t
            group by [YEAR], [MONTH], [DAY], cardno, ID, chsnm, place , code, Category, dn, OG_Name, food
        ) m
    )n
    WHERE amount=1
    {extra_conditions_2}
)
SELECT cardno, chsnm, place, code, category, cktime, dn, OG_name, food, [sid]
FROM
(
    SELECT *,ROW_NUMBER() OVER (PARTITION BY [YEAR], [MONTH], [DAY], cardno Order By dn ASC) AS rn_day
    FROM raw_data
) t
WHERE rn_day = 1  -- 每個人一天只能吃一餐
ORDER BY cktime
OPTION (RECOMPILE);
                """

                query = conn.execute(text(sql), params)
                df = pd.DataFrame([dict(i) for i in query])

        except Exception as e:
            logger.error(f"SQL Error: {e}")

        if df.empty:
            return []

        df["cktime"] = df["cktime"].astype(str)
        df["food"] = df["food"].fillna("").astype(str)

        return [
            {
                "sid": row["sid"],
                "cardno": row["cardno"],
                "chsnm": row["chsnm"],
                "place": row["place"],
                "code": row["code"],
                "category": row["category"],
                "cktime": row["cktime"],
                "dn": row["dn"],
                "OG_name": row["OG_name"],
                "food": row["food"],
            }
            for _, row in df.iterrows()
        ]     


# In[ ]:


class Staff_meal_ordering_query_guest_meal:
    def __init__(self, servers, redis_client=None):
        self.servers = servers
        self.redis_client = redis_client
        
    # -------------------------
    # Redis key helper
    # -------------------------
    def _day_cache_key(self, bdate: datetime.date):
        return f"guest_meal_order:day:{bdate.strftime('%Y-%m-%d')}"

    def _month_cache_key(self, year: int, month: int):
        return f"guest_meal_order:month:{year}-{month:02d}"

    # -------------------------
    # 取/存快取
    # -------------------------
    def _get_cache(self, key):
        if not self.redis_client:
            return None
        data = self.redis_client.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except Exception:
            logger.error(f"Invalid JSON in Redis key: {key}")
            return None

    def _set_cache(self, key, data, ttl):
        if self.redis_client:
            self.redis_client.set(key, json.dumps(data), ex=ttl)
            logger.info(f"Set Redis cache: {key}")   
            
    # -------------------------
    # 刪除當日快取
    # -------------------------
    def invalidate_day_cache(self, bdate: datetime.date):
        if not self.redis_client:
            return
        key = self._day_cache_key(bdate)
        self.redis_client.delete(key)
        logger.info(f"Deleted Redis cache: {key}")
        
    # -------------------------
    # 過濾資料
    # -------------------------            
    def _filter_data(self, data, cardno=None, code=None, mtype=None, ogname=None):
        def match(row):
            if cardno and row.get("cardno") != cardno:
                return False
            if code and row.get("code") != code:
                return False
            if mtype and row.get("mtype") != mtype:
                return False
            if ogname and row.get("OG_name") != ogname:
                return False
            return True

        return [row for row in data if match(row)]        
        
    def fetch(self, year: str, month: str, day: str, cardno: str, code: str, mtype: str, ogname: str): 
        startTime = time.time()
        
        # 基本參數檢查        
        if not year:
            return {'success': False, 'message': 'Missing year parameter'}
        if not month:
            return {'success': False, 'message': 'month year parameter'}  
        
        try:
            year = int(year)
            month = int(month)
            if day:
                day = int(day)
        except Exception as e:
            return {'success': False, 'message': f'Invalid date parameter: {e}'}

        now = datetime.datetime.now()
        today_date = now.date()

        month_key = self._month_cache_key(year, month)
        
        if day:
            query_date = datetime.date(year, month, day)
            day_key = self._day_cache_key(query_date)
        else:
            query_date = None
            day_key = None

        data = []     

        # =========================
        # Case 1：查「指定日」
        # =========================
        if day:
            cached = self._get_cache(day_key)
            
            if cached:
                logger.info(f"Hit guest day cache: {day_key}")
                data = cached["data"]
                
            else:
                data = self._query_db(year, month, day, cardno=None, code=None, mtype=None, ogname=None)
                # TTL：今天資料短，其他長
                # 只存非未來日期
                if query_date <= today_date:
                    ttl = 600 if query_date == today_date else 28800
                    self._set_cache(day_key, {"data": data}, ttl)

        # =========================
        # Case 2：查「整月」
        # =========================
        else:
            cached = self._get_cache(month_key)
            
            if cached:
                logger.info(f"Hit guest month cache: {month_key}")
                data = cached["data"]
                
            else:
                data = self._query_db(year, month, day=None, 
                                      cardno=None, code=None, mtype=None, ogname=None, 
                                      until_yesterday=True)
                
                self._set_cache(month_key, {"data": data}, 28800)

            # 👉 當月補今天資料
            if int(year) == now.year and int(month) == now.month:
                today_key = self._day_cache_key(today_date)
                today_cache = self._get_cache(today_key)
                
                if today_cache:
                    logger.info(f"Hit guest today cache: {today_key}")
                    data += today_cache["data"]
                else:
                    today_data = self._query_db(year, month, day=now.day, 
                                                cardno=None, code=None, mtype=None, ogname=None)
                    
                    self._set_cache(today_key, {"data": today_data}, 600)
                    data += today_data

        # =========================
        # 🔥 最後才 filter（Python 過濾）
        # =========================
        data = self._filter_data(data, cardno, code, mtype, ogname)

        ExecutionTime = time.time() - startTime
        logger.info(f"Guest fetch ExecutionTime: {ExecutionTime:.3f} sec")

        return {"data": data}       
        
    
    def _query_db(self, year, month, day=None, cardno=None, code=None, mtype=None, ogname=None, until_yesterday=False):
        """
        查詢來賓訂餐資料，回傳 list of dict
        """        
        df = pd.DataFrame()
        try:
            srv = self.servers['SRVMESDBA1']
            with srv['create_engine'][0].connect() as conn:
                base_sql = """
                    select a.sn,a.cardno, a.mtype, a.cnt_02, a.cnt_03, b.chsnm, 
                           a.code,c.chsnm as loc, a.cktime, d.OG_Name as OG_name, a.con_name, a.memo
                    from [HR].[dbo].[hdeatlog_KB] a
                    left join [SRVAD6].[HR].[dbo].[hmstaff] b on a.cardno=b.emp_id COLLATE Chinese_Taiwan_Stroke_CI_AS 
                    left join [SRVAD6].[HR].[dbo].[hdMfood_place] c on a.code=c.code COLLATE Chinese_Taiwan_Stroke_CI_AS
                    left join [SRVAD6].[HR].[dbo].[hdtree] d on b.team_sn=d.OG_MID COLLATE Chinese_Taiwan_Stroke_CI_AS
                    where 1=1
                      AND YEAR(bdate) = :year
                      AND MONTH(bdate) = :month
                      {extra_conditions}
                    order by cktime
                """
                conditions = []
                params = {"year": year, "month": month}
                if day:
                    conditions.append("AND DAY(bdate) = :day")
                    params["day"] = day
                if until_yesterday:
                    conditions.append("AND bdate < CAST(GETDATE() AS DATE)")                    
                if cardno:
                    conditions.append("AND cardno = :cardno")
                    params["cardno"] = cardno
                if code:
                    conditions.append("AND a.code = :code")
                    params["code"] = code
                if mtype:
                    conditions.append("AND a.mtype = :mtype")
                    params["mtype"] = mtype
                if ogname:
                    conditions.append("AND d.OG_Name = :ogname")
                    params["ogname"] = ogname
                extra_conditions = "\n".join(conditions)
                sql = base_sql.format(extra_conditions=extra_conditions)
                query = conn.execute(text(sql), params)
                df = pd.DataFrame([dict(i) for i in query])
        except Exception as e:
            logger.error(f"GuestMeal SQL Error: {e}")
            df = pd.DataFrame()

        if df.empty:
            return []

        df["cktime"] = df["cktime"].astype(str)
        return df.to_dict(orient="records")

