import logging
<<<<<<< HEAD
import pandas as pd
from sqlalchemy import Column, Integer, String, SmallInteger, Float, DateTime, VARCHAR, text
from sqlalchemy.dialects.mssql import DATETIMEOFFSET
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base

from utils.db_engine import get_session
from common import add_to_dict

Base = declarative_base()

@add_to_dict
class duptjobs(Base):
    __tablename__ = 'duptjobs'

    klKey = Column(Integer, primary_key=True, nullable=False)
    Operator = Column(String(50), nullable=True)
    CompanyName = Column(String(50), nullable=True)
    InspectionType = Column(String(50), nullable=True)
    MaterialType = Column(String(50), nullable=True)
    OrderNumber = Column(String(50), nullable=True)
    JobID = Column(String(50), nullable=False)
    StartingDoffSerialNumber = Column(Integer, nullable=True)
    Date = Column(DateTime, nullable=False)
    fkMCS = Column(Integer, nullable=False)
    Comment = Column(String(255), nullable=True)
=======
import os
import pandas as pd
# from flask import current_app
from sqlalchemy import create_engine, text, DateTime, Integer, String, Boolean, DECIMAL, SmallInteger, VARCHAR, DateTime, DateTime, Float
from sqlalchemy.dialects.mssql import DATETIMEOFFSET
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from app.common import add_to_dict, get_connection_string
# from icecream import ic

from urllib.parse import quote_plus as urlquote

Base = declarative_base()


@add_to_dict
class duptjobs(Base):
    __tablename__ = "duptjobs"

    klKey = Column(Integer, primary_key=True, nullable=False)
    Operator = Column(String(50))
    CompanyName = Column(String(50))
    InspectionType = Column(String(50))
    MaterialType = Column(String(50))
    OrderNumber = Column(String(50))
    JobID = Column(String(50), nullable=False)
    StartingDoffSerialNumber = Column(Integer)
    Date = Column(DateTime, nullable=False)
    fkMCS = Column(Integer, nullable=False)
    Comment = Column(String(255))
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
    LastPosition = Column(Float, nullable=False)
    LastSpeed = Column(Float, nullable=False)
    LastLeftEdge = Column(Float, nullable=False)
    LastRightEdge = Column(Float, nullable=False)
    Status = Column(SmallInteger, nullable=False)
<<<<<<< HEAD
    JobEnd = Column(DateTime, nullable=True)
    SourceDB = Column(VARCHAR(10), nullable=True)
    FetchDate = Column(DateTime, nullable=True)
    JobIDModifiedDate = Column(DateTime, nullable=True)
    ModifiedBy = Column(Integer, nullable=True)
    ModifiedDate = Column(DateTime, nullable=True)
    ModifiedDateOffset = Column(DATETIMEOFFSET, nullable=True)
=======
    JobEnd = Column(DateTime)
    SourceDB = Column(VARCHAR(10))
    FetchDate = Column(DateTime)
    JobIDModifiedDate = Column(DateTime)
    ModifiedBy = Column(Integer)
    ModifiedDate = Column(DateTime)
    ModifiedDateOffset = Column(DATETIMEOFFSET)
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d


class duptjobsDal:
    def __init__(self):
<<<<<<< HEAD
        try:
            self.session = get_session("SRVMSDBA1_FlawInspection")  # 透過 utils 統一管理
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | init error: {e}")

    def currentLenth(self,filter):
        try:
            # 自定義 SQL 查詢語句
            sql_query = f"""
            SELECT TOP (1)
            [LastPosition]
            FROM [FlawInspection].[dbo].[duptjobs]
            order by Date desc
            """
            with self.session() as s:
                df = pd.read_sql(text(sql_query), s.connection())
                return df.to_dict(orient='records')
        except OperationalError as e:
            logging.error(f'{self.__class__.__name__} |Connection error: {str(e)}')
            return []
        except Exception as e:
            logging.error(f'{self.__class__.__name__} |Error: {str(e)}')
            return []


    def query(self, query_obj):
        try:
            with self.get_session() as session:
                result_df = pd.read_sql(query.statement, session.bind)
                df = pd.read_sql(query_obj.statement, session.bind)
                datetime_columns = df.select_dtypes(include=['datetime64[ns]']).columns
                for col in datetime_columns:
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                return df.to_dict(orient='records')
        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
            logging.debug(msg)
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
=======
        trace_msg = f'{self.__class__.__name__}'
#         ic(trace_msg)
        logging.info(trace_msg)
        try:
            # 直接用你的固定連線方式
            server = "10.10.1.115"
            database = "FlawInspection"
            password = urlquote("yfyoljk@")
            conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
            self.engine = create_engine(
                conn_str,
                fast_executemany=True,
                pool_pre_ping=True,
                pool_recycle=1800,
                pool_size=5,
                max_overflow=10
            )
            self.Session = sessionmaker(bind=self.engine)
            logging.info("Engine and sessionmaker created successfully.")

        except Exception as e:
            logging.exception(f"{self.__class__.__name__} | Failed to create engine/session: {e}")
            raise  # 必須 raise，否則 self.engine 不會存在

    def currentLenth(self, filter):
        try:
            sql_query = """
            SELECT TOP (1)
            LastPosition
            FROM FlawInspection.dbo.duptjobs
            ORDER BY Date DESC
            """
            import logging
            logging.basicConfig(level=logging.DEBUG)
            logging.debug("Running SQL query...")

            # 用 engine 直接讀取
            df = pd.read_sql(sql_query, self.engine)
            logging.debug(f"Query result:\n{df}")

            return df.to_dict(orient='records')

        except Exception as e:
            logging.exception("DAL query failed")
            return []     
        
        session = None
        try:
            session = self.Session()
            # 自定義 SQL 查詢語句
            sql_query = f"""
SELECT TOP (1)
[LastPosition]
FROM [FlawInspection].[dbo].[duptjobs]
order by Date desc
        """
            # 執行 SQL 查詢
            cond = []
            # cond.append("klKey= @jobKey")
            # cond.append("job.dtTime between @queryStartTime and @queryEndTime")
            params = {}
            # params['JobID'] = f"{data.ReelNo}"
            print(pd.read_sql(sql_query, self.engine))
            try:
                where_clause = ""
                if cond and len(cond) > 0:
                    # 使用 AND 運算符將條件組合在一起
                    where_clause = "WHERE " + " AND ".join(cond)
                order_clause = ""
                sql_query = f"{sql_query} {where_clause} {order_clause}"

                result_df = pd.read_sql(text(sql_query), session.bind, params=params)
            except OperationalError as e:
                msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
    #             ic(msg)
                logging.debug(msg)
            except Exception as e:
                raise e
#                 msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
#     #             ic(msg)
#                 logging.debug(msg)

            results = []
            session.close()
            # 使用範例：
            results = result_df.to_dict(orient='records')
            return results
    
    
        #     result_dict_list_df = result_df.to_dict(orient='records')

        #     return result_dict_list_df
        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
#             ic(msg)
            logging.debug(msg)
            return []
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
#             ic(msg)
            logging.debug(msg)
            return []
        finally:
            if session:
                session.close()


    def query(self, filter):
        try:
            session = self.Session()

            result_df = pd.read_sql(query.statement, session.bind)
            ic(f'records: {len(result_df.index)}')
            datetime_columns = result_df.select_dtypes(include=['datetime64[ns]']).columns
            ic(datetime_columns)
            for column in datetime_columns:
                result_df[column] = result_df.apply(lambda x: x[column].strftime('%Y-%m-%d %H:%M:%S')
                                                    if not pd.isna(x[column]) else None, axis=1)
            session.close()

            # Convert DataFrame to a list of dictionaries
            result_dict_list_df = result_df.to_dict(orient='records')

            return result_dict_list_df
        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
#             ic(msg)
            logging.debug(msg)
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
#             ic(msg)
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
            logging.debug(msg)
        finally:
            session.close()
