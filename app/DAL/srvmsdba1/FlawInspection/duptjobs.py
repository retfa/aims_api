import logging
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
    LastPosition = Column(Float, nullable=False)
    LastSpeed = Column(Float, nullable=False)
    LastLeftEdge = Column(Float, nullable=False)
    LastRightEdge = Column(Float, nullable=False)
    Status = Column(SmallInteger, nullable=False)
    JobEnd = Column(DateTime, nullable=True)
    SourceDB = Column(VARCHAR(10), nullable=True)
    FetchDate = Column(DateTime, nullable=True)
    JobIDModifiedDate = Column(DateTime, nullable=True)
    ModifiedBy = Column(Integer, nullable=True)
    ModifiedDate = Column(DateTime, nullable=True)
    ModifiedDateOffset = Column(DATETIMEOFFSET, nullable=True)


class duptjobsDal:
    def __init__(self):
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
            logging.debug(msg)
        finally:
            session.close()
