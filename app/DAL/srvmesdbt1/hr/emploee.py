import logging
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from utils.db_engine import get_session
from common import add_to_dict
from Kernel.Helpers import Exclude_Fields

logger = logging.getLogger("MES_API")

Base = declarative_base()


@add_to_dict
class Emploee(Base):
    __tablename__ = 'emploee'

    Emp_Guid = Column(String(36))
    COM = Column(String(1))
    Emp_ID = Column(String(9))
    Email = Column(String(255))
    Emp_Name = Column(String(20))
    Emp_EName = Column(String(100))
    Department_ID = Column(String(24))
    Department_ID2 = Column(String(1024))
    Job_Title = Column(String(100))
    Assume_Date = Column(DateTime)
    Leave_Date = Column(DateTime)
    CreateDate = Column(DateTime)
    AccessionState = Column(Integer)
    NoPayStatus = Column(Integer)
    jobrank = Column(Integer)
    cellphone1 = Column(String(100))
    cellphone2 = Column(String(100))
    officephone = Column(String(100))
    emp_id_hr = Column(String(5), primary_key=True)
    last_sync = Column(DateTime)
    shift = Column(String(1))
    CreateBy = Column(String(5))
    ModifyDate = Column(DateTime)
    ModifyBy = Column(String(5))


class EmploeeDal:

    def __init__(self):
        try:
            # 🔥 統一 DB
            self.session_factory = get_session("SRVMESDBA1_HR")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | init error: {e}")

    # 🔹 新增
    def insert(self, data: dict):
        try:
            session = self.session_factory()

            obj = Emploee()
            for key, value in data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            obj.CreateDate = func.sysdatetime()

            session.add(obj)
            session.commit()

            return 1

        except OperationalError as e:
            logger.error(f"{self.__class__.__name__} | DB error: {e}")
            return -1

        except Exception as e:
            logger.error(f"{self.__class__.__name__} | error: {e}")
            return -1

        finally:
            session.close()

    # 🔹 更新
    def update(self, data: dict):
        try:
            session = self.session_factory()

            obj = session.query(Emploee).filter_by(Emp_ID=data["Emp_ID"]).one_or_none()

            if not obj:
                return 0

            for key, value in data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            obj.ModifyDate = func.sysdatetime()

            session.commit()

            return 1

        except OperationalError as e:
            logger.error(f"{self.__class__.__name__} | DB error: {e}")
            return -1

        except Exception as e:
            logger.error(f"{self.__class__.__name__} | error: {e}")
            return -1

        finally:
            session.close()

    # 🔹 單筆查詢
    def select(self, emp_id: str):
        try:
            session = self.session_factory()

            obj = session.query(Emploee).filter_by(Emp_ID=emp_id).one_or_none()

            if not obj:
                return None

            return obj.to_dict()

        except OperationalError as e:
            logger.error(f"{self.__class__.__name__} | DB error: {e}")
            return None

        except Exception as e:
            logger.error(f"{self.__class__.__name__} | error: {e}")
            return None

        finally:
            session.close()

    # 🔹 多條件查詢
    def query(self, filter):
        try:
            session = self.session_factory()

            cond = []

            if filter.user_id and filter.user_id.strip():
                cond.append(Emploee.emp_id_hr == filter.user_id.strip())

            if filter.user_id_hris and filter.user_id_hris.strip():
                cond.append(Emploee.Emp_ID == filter.user_id_hris.strip())

            if filter.user_name and filter.user_name.strip():
                cond.append(Emploee.Emp_Name == filter.user_name.strip())

            query_obj = session.query(Emploee)
            if cond:
                query_obj = query_obj.filter(*cond)

            result = query_obj.all()

            data_list = [obj.to_dict() for obj in result]

            # 🔥 排除欄位
            exclude_fields = ['CreateBy', 'ModifyDate', 'ModifyBy']
            return Exclude_Fields(data_list, exclude_fields)

        except OperationalError as e:
            logger.error(f"{self.__class__.__name__} | DB error: {e}")
            return []

        except Exception as e:
            logger.error(f"{self.__class__.__name__} | error: {e}")
            return []

        finally:
            session.close()