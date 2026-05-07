# from flask import current_app
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
import pyodbc
import json
import os
import logging
import re
from ldap3 import ALL_ATTRIBUTES, SUBTREE, Server, Connection, ALL, KERBEROS, SAFE_SYNC

from Model.user import UserLogin, UserSignedIn
from utils.db_engine import get_session

logger = logging.getLogger("MES_API")

class Authentication:
    def __init__(self, folders):
        trace_msg = f'{self.__class__.__name__}'
        logging.info(trace_msg)
        
        try:
            SessionLocal = get_session("SRVMESDBA1_AMIS")
            self.session = SessionLocal()  # ← 建立一個 session 實例
            self.engine = self.session.get_bind()
        except Exception as e:
            logger.error(f"auth.py | An error occurred: {e}")        

    def Auth(self, data: UserLogin):
        user = self.CheckByAd(data)
        if user is None:
            user = self.CheckByLocal(data)
        return user

    def CheckByAd(self, data):
        AD_SERVER = 'ldap://10.10.1.1'
        server = Server(AD_SERVER, get_info=ALL)
        try:
            conn = Connection(server, fr"yfy\{data.login_id}", data.password, auto_bind=True)
            if conn.bind():

                base_dns = [
                    "OU=久堂廠,OU=纖維材料事業部,OU=總經理,OU=中華紙漿股份有限公司,OU=永豐餘控股,OU=Company,DC=yfy,DC=corp",
                    "OU=久堂廠,OU=Group,OU=TW-久堂廠,OU=YFY_TW,OU=YFY,DC=yfy,DC=corp"
                ]

                search_filter = f"(sAMAccountName={data.login_id})"  # 用戶名的篩選條件
                attributes = ['displayname', 'employeeID']  # 欲取得的屬性            

                results = []  # 儲存查詢結果
                for base_dn in base_dns:
                    # 執行查詢
                    conn.search(search_base=base_dn,
                                search_filter=search_filter,
                                search_scope=SUBTREE,
                                attributes=attributes,
                                size_limit=1
                                )
                    results.extend(conn.entries)
                    if results:
                        break  # 找到就停止                

                if len(results) == 1:
                    entry = results[0]
                    try:
                        with self.session.begin():
                            query = text('''
                    SELECT mes.*, AIMS.Sn
                    FROM [AMIS].[dbo].[zmuser] mes
                    LEFT JOIN [SRVMSDBA1].[AIMSFTAZ].[dbo].[zuser_m] aims
                    ON mes.user_id_hris collate Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS = aims.IdHris
                    WHERE mes.user_id_hris=:login_id and mes.status='Y'
                ''')
                            # 用 employeeID 查 local DB
                            login_id_for_db = str(entry.employeeID)
                            # 用 employeeID 查 local DB
                            login_id_for_db = str(entry.employeeID)
                            result = self.session.execute(query, {'login_id': login_id_for_db})
                            row = result.fetchone()
                            if row:
                                # 確保回傳 user_signedIn 物件
                                user_data = UserSignedIn(
                                    FTAId=row.user_id,
                                    YFYId=row.user_id_hris,
                                    Name=row.user_name,
                                    FTASn=row.Sn
                                )
                                self.reset_error_counter(data)
                                return user_data
                            else:
                                self.increase_error_counter(data)                        
                    except OperationalError as e:
                        logging.error(f"DB query failed: {e}")
                        return None
        except Exception as e:
            logging.error(f"AD connection/search failed: {e}")
        finally:
            if 'conn' in locals():
                conn.unbind()
        return None
                
    def CheckByLocal(self, data):
        try:
            patternHirs = r"^\d{9}$"  # 匹配9碼工號9個數字

            if re.match(patternHirs, data.login_id):
                query = text('''
    SELECT mes.*, AIMS.Sn
    FROM [AMIS].[dbo].[zmuser] mes
    LEFT JOIN [SRVMSDBA1].[AIMSFTAZ].[dbo].[zuser_m] aims
    ON mes.user_id_hris collate Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS = aims.IdHris
    WHERE mes.user_id_hris=:login_id and mes.pwd=:password and mes.status='Y'
''')
            else:
                query = text('''
    SELECT mes.*, AIMS.Sn
    FROM [AMIS].[dbo].[zmuser] mes
    LEFT JOIN [SRVMSDBA1].[AIMSFTAZ].[dbo].[zuser_m] aims
    ON mes.user_id_hris collate Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS = aims.IdHris
    WHERE mes.user_id=:login_id and mes.pwd=:password and mes.status='Y'
''')
            result = self.session.execute(query, {'login_id': data.login_id, 'password': data.password})
            row = result.fetchone()
            if row:
                # 確保回傳 user_signedIn 物件
                user_data = UserSignedIn(
                    FTAId=row.user_id,
                    YFYId=row.user_id_hris,
                    Name=row.user_name,
                    FTASn=row.Sn
                )
                self.reset_error_counter(data)
                return user_data
            else:
                self.increase_error_counter(data)
                return None

        except OperationalError as e:
            return None

    def increase_error_counter(self, data: UserLogin):
        try:
            # patternLocal = r"^[A-Za-z]\d{4}$"  # 匹配5碼工號一個英文字母後接4個數字
            patternHris = r"^\d{9}$"  # 匹配9碼工號9個數字
            error_limit = 4
            if re.match(patternHris, data.login_id):
                query = text(
                    f"Update [AMIS].[dbo].[zmuser] SET pwderrcount = pwderrcount + 1, status= CASE WHEN pwderrcount >={str(error_limit)} THEN 'L' ELSE status END WHERE user_id_hris=:login_id")
            # elif re.match(patternLocal, data.login_id):
            else:
                query = text(
                    f"Update [AMIS].[dbo].[zmuser] SET pwderrcount = pwderrcount + 1, status= CASE WHEN pwderrcount >={str(error_limit)} THEN 'L' ELSE status END WHERE user_id=:login_id")

            with self.engine.connect() as conn:          # ← 獨立 connection
                conn.execute(query, {'login_id': data.login_id, 'password': data.password})
                conn.execute(text("COMMIT"))  # ← 改這樣
        except OperationalError as e:
            print("Database connection error:", str(e))

    def reset_error_counter(self, data: UserLogin):
        try:
            # patternLocal = r"^[A-Za-z]\d{4}$"  # 匹配5碼工號一個英文字母後接4個數字
            patternHris = r"^\d{9}$"  # 匹配9碼工號9個數字

            if re.match(patternHris, data.login_id):
                query = text(
                    "Update [AMIS].[dbo].[zmuser] SET pwderrcount = 0 WHERE user_id_hris=:login_id and pwd=:password")
            else:
                query = text(
                    "Update [AMIS].[dbo].[zmuser] SET pwderrcount = 0 WHERE user_id=:login_id and pwd=:password")
            with self.engine.connect() as conn:          # ← 獨立 connection，不共用 session
                conn.execute(query, {'login_id': data.login_id, 'password': data.password})
                conn.execute(text("COMMIT"))  # ← 改這樣                      # ← 一定要 commit
        except OperationalError as e:
            print("Database connection error:", str(e))
        except Exception as e:
            print("reset_error_counter error:", str(e))
