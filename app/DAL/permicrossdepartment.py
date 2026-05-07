import logging
import datetime
import pandas as pd

from sqlalchemy import Column, Integer, String, DateTime, text, Boolean
from sqlalchemy.dialects.mssql import DATETIMEOFFSET
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import and_
from sqlalchemy.sql import func

from utils.db_engine import get_session
from common import add_to_dict

logger = logging.getLogger("MES_API")

Base = declarative_base()

@add_to_dict
class ZdPermCrossDept(Base):
    __tablename__ = 'zdpermicrossdept'
    Sn = Column(Integer, primary_key=True)
    user_id = Column(String(9))
    progm_id = Column(String(20))
    departments = Column(String(100))
    IsEnabled = Column(Boolean)
    busr = Column(String(5))
    bdtm = Column(DateTime)
    musr = Column(String(5))
    mdtm = Column(DateTime)


class PermissionCrossDepartmentDal:
    def __init__(self):
        try:
            # 透過 utils 統一管理 session 工廠
            self.session_factory = get_session("SRVMESDBA1_AMIS")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | init error: {e}")

    def query(self, filter):
        """
        篩選資料，回傳 list[dict]
        filter = {"user_id": "A001", "progm_id": "P01"}
        """
        session = self.session_factory()        
        try:
            cond = []
            if getattr(filter, 'user_id', None):
                cond.append(ZdPermCrossDept.user_id == filter.user_id)
            if getattr(filter, 'progm_id', None):
                cond.append(ZdPermCrossDept.progm_id == filter.progm_id)
            cond.append(ZdPermCrossDept.IsEnabled == True)
            
            query = session.query(ZdPermCrossDept)
            if cond:
                query = query.filter(and_(*cond))
            result_df = pd.read_sql(query.statement, session.bind)
            
            # 轉換 datetime 欄位格式
            for col in result_df.select_dtypes(include=['datetime64[ns]']).columns:
                result_df[col] = result_df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else None)

            return result_df.to_dict(orient='records')
        except OperationalError as e:
            logger.error(f"{self.__class__.__name__} | DB connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | query error: {e}")
            return []
        finally:
            session.close()

    def insert(self, user):
        try:
            session = self.session_factory()

        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)

        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)

        finally:
            session.close()

    def update(self, data): 
        session = self.session_factory()
        try:
            zpermicrossdept = session.query(zdpermicrossdept).filter_by(
                user_id=data["user_id"],
                progm_id=data["progm_id"]
            ).first()
            if zpermicrossdept:
                zpermicrossdept.departments = data["departments"]
                if hasattr(data, "IsEnabled"):
                    zpermicrossdept.IsEnabled = data["IsEnabled"]
                zpermicrossdept.musr = data["musr"]
                zpermicrossdept.mdtm = func.sysdatetime()
                session.merge(zpermicrossdept)
            session.commit()
            return data

        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)

        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)

        finally:
            session.close()

    def upsert(self, data):
        session = self.session_factory()
        """
        如果存在就更新，不存在就新增
        data = {"user_id":"A001","progm_id":"P01","departments":"D01","busr":"ADMIN"}
        """       
        try:
            record = session.query(ZdPermCrossDept).filter_by(
                user_id=data["user_id"],
                progm_id=data["progm_id"]
            ).first()

            if record:
                record.departments = data.get("departments", record.departments)
                if "IsEnabled" in data:
                    record.IsEnabled = data["IsEnabled"]
                record.musr = data.get("musr", record.musr)
                record.mdtm = func.sysdatetime()
                session.merge(record)
            else:
                record = ZdPermCrossDept()
                record.user_id = data["user_id"]
                record.progm_id = data["progm_id"]
                record.departments = data.get("departments")
                record.IsEnabled = True
                record.busr = data.get("busr")
                record.musr = data.get("musr")
                record.mdtm = func.sysdatetime()
                session.add(record)

            session.commit()
            return 1

        except OperationalError as e:
            logger.error(f"{self.__class__.__name__} | DB connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | upsert error: {e}")
            return None
        finally:
            session.close()

    def select(self, filter):
        try:
            session = self.session_factory()
            filter_conditions = []

            if getattr(filter, 'user_id', None):                
                filter_conditions.append(ZdPermCrossDept.user_id == filter.user_id)

            if getattr(filter, 'progm_id', None):                    
                filter_conditions.append(ZdPermCrossDept.progm_id == filter.progm_id)

            filter_conditions.append(ZdPermCrossDept.IsEnabled == 1)
            final_filter_condition = and_(*filter_conditions)
            query = session.query(ZdPermCrossDept).filter(final_filter_condition)
            result_df = pd.read_sql(query.statement, session.bind)
            datetime_columns = result_df.select_dtypes(include=['datetime64[ns]']).columns
            for column in datetime_columns:
                result_df[column] = result_df.apply(lambda x: x[column].strftime('%Y-%m-%d %H:%M:%S')
                                                    if not pd.isna(x[column]) else None, axis=1)
            session.close()

            # Convert DataFrame to a list of dictionaries
            result_dict_list_df = result_df.to_dict(orient='records')

            return result_dict_list_df
        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)
        finally:
            session.close()
