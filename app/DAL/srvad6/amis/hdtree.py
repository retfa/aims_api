import logging
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base

from utils.db_engine import get_session

logger = logging.getLogger("MES_API")

Base = declarative_base()


# ✅ ORM Model（如果未來要用 ORM 查詢會用到）
class hdtree(Base):
    __tablename__ = 'hdtree'

    Sn = Column(Integer, primary_key=True)
    IDX = Column(Integer)
    OG_MType = Column(Integer)
    OG_Msn = Column(Integer)
    OG_MID = Column(String(50))
    OG_MID_HRIS = Column(String(50))
    OG_Name = Column(String(100))
    OG_Parent = Column(Integer)
    OG_Son = Column(Integer)
    OG_level = Column(String(100))
    OG_team_sn = Column(String(100))
    OG_dept = Column(String(100))
    OG_mag = Column(String(10))
    OG_Grade = Column(Integer)
    OG_status = Column(Integer)


# ✅ DAL
class hdtreeDal:

    def __init__(self):
        try:
            # 🔥 統一 DB 來源（取代 appsettings + connections.json）
            self.session_factory = get_session("srvad6_hr")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | init error: {e}")

    # 🔹 查詢 HR AD6
    def select(self, user_id: str):
        try:
            session = self.session_factory()

            query_sql = '''
SELECT 
    a.og_name AS chsnm,
    a.og_dept AS dept,
    a.og_team_sn AS team_no,
    a.og_status,
    b.og_name AS dept_name
FROM [srvad6].[hr].[dbo].[hdtree] a
LEFT JOIN [srvad6].[hr].[dbo].[hdtree] b 
    ON b.og_mtype = '3' 
    AND b.og_mid = a.og_team_sn
WHERE 
    a.og_mtype NOT IN ('2', '3')
    AND a.og_mid = :user_id
            '''

            sql_query = text(query_sql)

            try:
                result = session.execute(sql_query, {"user_id": user_id})

                # ✅ 新寫法（不用 to_dict）
                result_list = [dict(row._mapping) for row in result]

                return result_list

            finally:
                session.close()

        except OperationalError as e:
            msg = f'{self.__class__.__name__} | DB connection error: {str(e)}'
            logger.error(msg)
            return []

        except Exception as e:
            msg = f'{self.__class__.__name__} | error: {str(e)}'
            logger.error(msg)
            return []