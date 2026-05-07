#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import logging
import datetime
from sqlalchemy import text

from resources.Staff_meal_ordering_system import Staff_meal_ordering_query
from resources.Staff_meal_ordering_system import Staff_meal_ordering_query_guest_meal


logger = logging.getLogger("MES_API")


class StaffMealOrderingService:

    def __init__(self, servers, server_name="SRVMESDBA1", redis_client=None): # 20260323 歐陽憲毅 由SRVAD6改為SRVMESDBA1
        self.servers = servers

        if server_name not in servers:
            raise RuntimeError(f"Server {server_name} not found")

        self.server_df = servers[server_name]

        self.fetcher = Staff_meal_ordering_query(servers=servers, redis_client=redis_client)
        self.guest_fetcher = Staff_meal_ordering_query_guest_meal(servers=servers, redis_client=redis_client)

    # -------------------------
    # 查詢
    # -------------------------
    def fetch(self, year, month, day, cardno, code, dn, food, OG_name):

        try:
            return self.fetcher.fetch(
                year=year,
                month=month,
                day=day,
                cardno=cardno,
                code=code,
                dn=dn,
                food=food,
                OG_name=OG_name
            )

        except Exception as e:
            logger.error(f"StaffMealOrdering fetch error: {e}")
            return {"success": False, "message": str(e), "data": []}
        
    # 刪除當日快取
    def invalidate_day_cache(self, bdate):
        self.fetcher.invalidate_day_cache(bdate)

    # -------------------------
    # 新增
    # -------------------------
    def create(self, payload):
        """
        新增員工餐點資料，並刪除當天 Redis 快取      
        payload 範例：
        {
          "Category": "01",
          "cardno": "A5558",
          "cktime": "2025-11-11 08:03:01.000",
          "loca": "10.10.1.62",
          "locaName": "舊廠便當機",
          "nad": "01"
        }
        """        

        data = payload.dict()
        
        # 自動計算 bdate
        # 假設 cktime 是 datetime 字串，取日期部分作 bdate
        if "cktime" in data:
            bdate = datetime.datetime.strptime(data["cktime"], "%Y-%m-%d %H:%M:%S.%f").date()
        else:
            bdate = datetime.date.today()

        try:

            with self.server_df['create_engine'][0].begin() as conn:

                fields = ", ".join(data.keys())
                values = ", ".join(f":{k}" for k in data.keys())

                sql = f"""
                INSERT INTO [HR].[dbo].[erp_eat_log]
                ({fields})
                VALUES ({values})
                """

                conn.execute(text(sql), data)
                
            # 刪除當日 Redis 快取
            self.invalidate_day_cache(bdate)

            return {"success": True, "message": "Inserted successfully"}

        except Exception as e:
            logger.error(f"StaffMealOrdering create error: {e}")
            return {"success": False, "message": str(e)}

    # -------------------------
    # 刪除
    # -------------------------
    def delete(self, sid: int):
        """
        刪除 hdeatlog 與 erp_eat_log 資料，並刪除當日 Redis 快取
        """
        try:

            with self.server_df['create_engine'][0].begin() as conn:

                sid_sql = """
                SELECT TOP 1 cardno,dn,bdate
                FROM [HR].[dbo].[hdeatlog]
                WHERE sid = :sid
                """

                row = conn.execute(text(sid_sql), {"sid": sid}).mappings().first()

                if not row:
                    return {"success": False, "message": f"sid {sid} not found"}

                cardno = row["cardno"]
                dn = row["dn"]
                bdate = row["bdate"]
                
                if bdate:
                    if isinstance(bdate, str):
                        try:
                            bdate = datetime.datetime.strptime(bdate[:10], "%Y-%m-%d").date()
                        except Exception as e:
                            logger.error(f"Failed to parse bdate from string: {bdate}, error: {e}")
                            bdate = datetime.date.today()
                    elif isinstance(bdate, datetime.datetime):
                        bdate = bdate.date()                

                sids_to_delete = conn.execute(
                    text("""
                    SELECT sid
                    FROM [HR].[dbo].[hdeatlog]
                    WHERE cardno=:cardno
                    AND dn=:dn
                    AND bdate=:bdate
                    """),
                    {"cardno": cardno, "dn": dn, "bdate": bdate}
                ).scalars().all()

                conn.execute(
                    text("""
                    DELETE FROM [HR].[dbo].[hdeatlog]
                    WHERE cardno=:cardno
                    AND dn=:dn
                    AND bdate=:bdate
                    """),
                    {"cardno": cardno, "dn": dn, "bdate": bdate}
                )

                for s in sids_to_delete:
                    conn.execute(
                        text("""
                        DELETE FROM [HR].[dbo].[erp_eat_log]
                        WHERE sid = :sid
                        """),
                        {"sid": s}
                    )
                    
            # 刪除當日 Redis 快取
            self.invalidate_day_cache(bdate)

            return {"success": True, "message": "Deleted successfully"}

        except Exception as e:
            logger.error(f"StaffMealOrdering delete error: {e}")
            return {"success": False, "message": str(e)} 
        
    def fetch_guest_meal(self, year, month, day, cardno, code, mtype, ogname):

        try:

            return self.guest_fetcher.fetch(
                year=year,
                month=month,
                day=day,
                cardno=cardno,
                code=code,
                mtype=mtype,
                ogname=ogname
            )

        except Exception as e:

            logger.error(f"GuestMeal fetch error: {e}")

            return {"success": False, "message": str(e), "data": []}   
        
    def create_guest_meal(self, payload):

        data = payload.dict()

        required_fields = ["cardno", "code", "cktime"]

        missing = [f for f in required_fields if not data.get(f)]

        if missing:

            return {
                "success": False,
                "message": f"Missing parameter(s): {', '.join(missing)}"
            }

        try:

            cardno = data["cardno"]
            code = data["code"]
            cktime_str = data["cktime"]

            bdate = None

            if cktime_str:

                cktime = datetime.datetime.strptime(
                    cktime_str,
                    "%Y-%m-%d %H:%M:%S"
                )

                bdate = datetime.datetime(
                    cktime.year,
                    cktime.month,
                    cktime.day
                )

            memo = data.get("memo", "")

            with self.server_df['create_engine'][0].begin() as conn:

                staff_sql = """
                SELECT TOP 1 emp_id AS cardno, chsnm, team_sn
                FROM [SRVAD6].[HR].[dbo].[hmstaff]
                WHERE emp_id = :cardno
                """

                staff_row = conn.execute(
                    text(staff_sql),
                    {"cardno": cardno}
                ).mappings().first()

                if not staff_row:

                    return {
                        "success": False,
                        "message": f"找不到卡號 {cardno}"
                    }

                ID_sql = """
                SELECT TOP 1 ID
                FROM [HR].[dbo].[hdeatlog_KB]
                WHERE bdate=:bdate
                ORDER BY ID DESC
                """

                ID_row = conn.execute(
                    text(ID_sql),
                    {"bdate": bdate}
                ).mappings().first()

                ID_name = int(ID_row["ID"]) + 1 if ID_row else 1

                insert_data = {
                    **data,
                    "ID": str(ID_name),
                    "team_sn": staff_row["team_sn"],
                    "bdate": bdate,
                    "memo": memo,
                    "musr": cardno
                }

                fields = ", ".join(insert_data.keys())
                values = ", ".join(f":{k}" for k in insert_data.keys())

                sql = f"""
                INSERT INTO [HR].[dbo].[hdeatlog_KB]
                ({fields})
                VALUES ({values})
                """

                conn.execute(text(sql), insert_data)
                
            # -------------------------
            # 刪除 Redis 快取
            # -------------------------
            if bdate:
                self.guest_fetcher.invalidate_day_cache(bdate.date() if isinstance(bdate, datetime.datetime) else bdate)                

            return {"success": True, "message": "Inserted successfully"}

        except Exception as e:

            logger.error(f"GuestMeal create error: {e}")

            return {"success": False, "message": str(e)}   
        
    def delete_guest_meal(self, sn: int):

        try:

            with self.server_df['create_engine'][0].begin() as conn:

                row = conn.execute(
                    text("""
                    SELECT TOP 1
                    code,cardno,team_sn,bdate,mtype,
                    con_name,cnt_02,cnt_03,memo
                    FROM [HR].[dbo].[hdeatlog_KB]
                    WHERE sn = :sn
                    """),
                    {"sn": sn}
                ).mappings().first()

                if not row:

                    return {
                        "success": False,
                        "message": f"sn {sn} not found"
                    }

                conn.execute(
                    text("""
                    DELETE FROM [HR].[dbo].[hdeatlog_KB]
                    WHERE code=:code
                    AND cardno=:cardno
                    AND team_sn=:team_sn
                    AND bdate=:bdate
                    AND mtype=:mtype
                    AND con_name=:con_name
                    AND cnt_02=:cnt_02
                    AND cnt_03=:cnt_03
                    AND memo=:memo
                    """),
                    row
                )
                
            # -------------------------
            # 刪除 Redis 快取
            # -------------------------
            bdate = row["bdate"]
            if bdate:
                self.guest_fetcher.invalidate_day_cache(bdate.date() if isinstance(bdate, datetime.datetime) else bdate)

            return {"success": True, "message": "Deleted successfully"}

        except Exception as e:

            logger.error(f"GuestMeal delete error: {e}")

            return {"success": False, "message": str(e)}        
        
    def fetch_department(self, emp_id_hr: str):
        try:
            with self.server_df['create_engine'][0].connect() as conn:

                sql = """
                SELECT e.Emp_ID,
                       e.Emp_Name,
                       e.Department_ID,
                       e.emp_id_hr,
                       d.dept_name
                FROM [HR].[dbo].[emploee] e
                LEFT JOIN [HR].[dbo].[department] d
                       ON e.Department_ID = d.Dept_ID
                WHERE e.emp_id_hr = :emp_id_hr
                """

                rows = conn.execute(text(sql), {"emp_id_hr": emp_id_hr}).mappings().all()

                data = [dict(row) for row in rows]

                return {"success": True, "message": "OK", "data": data}

        except Exception as e:
            logger.error(f"StaffMealOrdering fetch_department error: {e}")
            return {"success": False, "message": str(e), "data": []}        

