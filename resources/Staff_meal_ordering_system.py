#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import timedelta
from flask import request, Response
from flask_restful import Resource
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
    def __init__(self, servers):
        self.servers = servers       
    
    def fetch(self, year: str, month: str, day: str, cardno: str, code: str, dn: str, food: str): 
        startTime = time.time()

        if not year:
            return {'success': False, 'message': 'Missing year parameter'}
        if not month:
            return {'success': False, 'message': 'month year parameter'}
              
        try:
            srv_SRVAD6 = self.servers['SRVAD6']
            with srv_SRVAD6['create_engine'][0].connect() as conn:
                base_sql =   """
                    SELECT cardno,chsnm,place,code,category,cktime,dn, OG_name, food ,sid
                    FROM
                    (
                        SELECT *,ROW_NUMBER() OVER (PARTITION BY [YEAR], [MONTH], [DAY], cardno,dn Order By cktime DESC) as amount
                        FROM
                        (
                            SELECT [YEAR], [MONTH], [DAY], cardno, id, chsnm, place , code, category, dn, OG_name, food, max(cktime) as cktime, max(sid) as sid
                            FROM
                            (
                                SELECT a.*,b.chsnm,c.chsnm as place, c.code, d.OG_name,
                                    CASE WHEN right(a.category,1) = 2 THEN 2
                                         WHEN right(a.category,1) = 3 THEN 3 ELSE right(b.food,1) END AS food
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
                                    AND YEAR(bdate) = :year
                                    AND MONTH(bdate) = :month
                                    {extra_conditions}
                                ) a
                                left join hmstaff b on a.cardno = b.emp_id
                                left join hdMfood_place c on b.food_place=c.code
                                left join hdtree d on b.team_sn=d.OG_MID
                                where 1=1
                                and b.chsnm is not null
                            ) t
                            group by [YEAR], [MONTH], [DAY], cardno, id, chsnm, place , code, category, dn, OG_name, food
                        ) m
                    )n
                    where amount=1
                    {extra_conditions_2}
                    order by cktime
                """

                # 動態條件部分
                conditions = []
                conditions_2 = []
                params = {"year": year, "month": month}

                if day:
                    conditions.append("AND DAY(bdate) = :day")
                    params["day"] = day

                if cardno:
                    conditions.append("AND cardno = :cardno")
                    params["cardno"] = cardno

                if code:
                    conditions_2.append("AND code = :code")
                    params["code"] = code
                if dn:
                    conditions_2.append("AND dn = :dn")
                    params["dn"] = dn
                if food:
                    conditions_2.append("AND food = :food")
                    params["food"] = food                    

                # 合併條件
                extra_conditions = "\n".join(conditions)
                extra_conditions_2 = "\n".join(conditions_2)
                
                sql = base_sql.format(extra_conditions=extra_conditions,
                                      extra_conditions_2=extra_conditions_2)
                
                query = conn.execute(text(sql), params)  
                df_hdeatlog = pd.DataFrame([dict(i) for i in query])

        except:
            df_hdeatlog = pd.DataFrame()
            
        if not df_hdeatlog.empty:
            df_hdeatlog["cktime"] = df_hdeatlog["cktime"].astype(str)

            # 建立 JSON 結構
            result_json = {
                "data": [
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
                    for _, row in df_hdeatlog.iterrows()
                ]
            }                   
        else:
            result_json = {
                "data":[]
            }


        ExecutionTime = time.time() - startTime   

        return result_json


# In[ ]:


class Staff_meal_ordering_query_guest_meal:
    def __init__(self, servers):
        self.servers = servers       
    
    def fetch(self, year: str, month: str,day: str, cardno: str, code: str, mtype: str): 
        startTime = time.time()      

        if not year:
            return {'success': False, 'message': 'Missing year parameter'}
        if not month:
            return {'success': False, 'message': 'month year parameter'}
        
        try:
            srv_SRVAD6 = self.servers['SRVAD6']
            with srv_SRVAD6['create_engine'][0].connect() as conn:
                base_sql =   """
                      select a.sn,a.cardno, a.mtype, a.cnt_02, a.cnt_03, b.chsnm, 
                      a.code,c.chsnm as loc, a.cktime, d.OG_name, a.con_name, a.memo
                      from hdeatlog_KB a
                      left join hmstaff b on a.cardno=b.emp_id 
                      left join hdMfood_place c on a.code=c.code
                      left join hdtree d on b.team_sn=d.OG_MID
                      where 1=1
                      AND YEAR(bdate) = :year
                      AND MONTH(bdate) = :month
                      {extra_conditions}
                      order by cktime
                """
                # 動態條件部分
                conditions = []
                params = {"year": year, "month": month}

                if day:
                    conditions.append("AND DAY(bdate) = :day")
                    params["day"] = day

                if cardno:
                    conditions.append("AND cardno = :cardno")
                    params["cardno"] = cardno

                if code:
                    conditions.append("AND a.code = :code")
                    params["code"] = code
                if mtype:
                    conditions.append("AND a.mtype = :mtype")
                    params["mtype"] = mtype                    

                # 合併條件
                extra_conditions = "\n".join(conditions)

                sql = base_sql.format(extra_conditions=extra_conditions)

                query = conn.execute(text(sql), params)  
                df_hdeatlog_gm = pd.DataFrame([dict(i) for i in query])                  

        except:
            df_hdeatlog_gm = pd.DataFrame() 
            
        if not df_hdeatlog_gm.empty:
            df_hdeatlog_gm["cktime"] = df_hdeatlog_gm["cktime"].astype(str)

            # 建立 JSON 結構
            result_json = {
                "data": [
                    {
                        "sn": row["sn"],
                        "cardno": row["cardno"],
                        "mtype": row["mtype"],
                        "cnt_02": row["cnt_02"],
                        "cnt_03": row["cnt_03"],
                        "chsnm": row["chsnm"],
                        "code": row["code"],
                        "loc": row["loc"],
                        "cktime": row["cktime"],
                        "OG_name": row["OG_name"],
                        "con_name": row["con_name"],
                        "memo": row["memo"]
                                      
                    }
                    for _, row in df_hdeatlog_gm.iterrows()
                ]
            }   
        else:
            result_json = {
                "data":[]
            }


        ExecutionTime = time.time() - startTime   

        return result_json


# In[ ]:




