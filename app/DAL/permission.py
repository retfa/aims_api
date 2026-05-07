import logging
import datetime
import pandas as pd

from sqlalchemy import Column, Integer, String, DateTime, text
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
class zpermission(Base):
    __tablename__ = 'zdpermi'
    sid = Column(Integer, primary_key=True)
    user_id = Column(String(5), primary_key=True)
    mname = Column(String(2), primary_key=True)
    progm_id = Column(String(20))
    up_code = Column(String(50))
    f_code = Column(String(20), primary_key=True)
    st_func = Column(String(1))
    sp_func = Column(String(1))
    func_print = Column(String(1))
    func_add = Column(String(1))
    func_edit = Column(String(1))
    func_delete = Column(String(1))
    func_sign = Column(String(1))
    func_detail = Column(String(1))
    func_download = Column(String(1))
    func_other = Column(String(1))
    busr = Column(String(5))
    bdtm = Column(DateTime)
    musr = Column(String(5))
    mdtm = Column(DateTime)


class PermissionDal:
    def __init__(self):
        try:
            self.session_factory = get_session("SRVMESDBA1_AMIS")  # 透過 utils 統一管理
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | init error: {e}")

    def query(self, filter):
        try:
            cond = []
            params = {}

            if getattr(filter, 'user_id', None):
                cond.append("perm.user_id = :user_id")
                params['user_id'] = filter.user_id

            if getattr(filter, 'progm_id', None):
                cond.append("progm.progm_id = :progm_id")
                params['progm_id'] = filter.progm_id

            if getattr(filter, 'up_function', None) is not None:
                cond.append("perm.up_code = :up_code")
                params['up_code'] = filter.up_function

            if getattr(filter, 'function', None):
                cond.append("perm.f_code = :f_code")
                params['f_code'] = filter.function
                
            if not cond:
                raise ValueError("查詢條件不可為空")                

            query_sql = '''
SELECT perm.*,usr.user_name, dept.dept_name, progm.pname , tree.f_name, machine.pm, machine.station
FROM [AMIS].[dbo].[zdpermi] perm
LEFT JOIN [AMIS].[dbo].[zdprogm] progm on perm.f_code=progm.f_code
LEFT JOIN [AMIS].[dbo].[zdtree] tree on perm.up_code=tree.f_code
LEFT JOIN [AMIS].[dbo].[ampudmc] machine on perm.mname=machine.mname
LEFT JOIN [AMIS].[dbo].[zmuser] usr on perm.user_id=usr.user_id
LEFT JOIN [HR].[dbo].[department] dept on usr.department_id collate Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS =dept.Dept_ID
                '''
            if cond:
                query_sql += " WHERE " + " AND ".join(cond) + " ORDER BY perm.user_id"               
                
            sql_query = text(query_sql)
            
            session = self.session_factory()
            try:
                rst = session.execute(sql_query, params)
                result_list = [dict(row._mapping) for row in rst]
                return result_list
            finally:
                session.close()            

        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
            logging.debug(msg)
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            logging.debug(msg)

    def insert(self, data):
        try:
            session = self.session_factory()
            zpermi = zpermission()
            zpermi.sid = 1
            zpermi.user_id = data["user_id"]
            if getattr(data, 'mname', "") is not None:
                zpermi.mname = data["mname"]
            zpermi.up_code = data["up_function"]
            zpermi.f_code = data["f_code"]
            zpermi.st_func = data["st_func"]
            zpermi.sp_func = data["sp_func"]
            zpermi.func_print = data["func_print"]
            zpermi.func_add = data["func_add"]
            zpermi.func_edit = data["func_edit"]
            zpermi.func_delete = data["func_delete"]
            zpermi.func_sign = data["func_sign"]
            zpermi.func_detail = data["func_detail"]
            zpermi.func_download = data["func_download"]
            zpermi.func_other = data["func_other"]
            session.add(zpermi)
            session.commit()

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
        try:
            session = self.session_factory()
            zpermi = zpermission()
            zpermi.user_id = data["user_id"]
            zpermi.st_func = data["st_func"]
            zpermi.sp_func = data["sp_func"]
            zpermi.func_print = data["func_print"]
            zpermi.func_edit = data["func_edit"]
            zpermi.func_sign = data["func_sign"]
            zpermi.func_detail = data["func_detail"]
            zpermi.func_download = data["func_download"]
            zpermi.func_other = data["func_other"]
            zpermi.musr = data["musr"]
            zpermi.mdtm = func.sysdatetime()
            session.merge(zpermi)
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


    def select(self, user_id):
        try:
            session = self.session_factory()
            # zmusr=zmuser_edit()
            rst = session.query(zpermission).filter_by(user_id=user_id).first()
            session.commit()
            return self.to_dict(rst)

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


    def delete_by_upcode(self, data):
        try:
            session = self.session_factory()
            filter_condition = and_(
                zpermission.user_id == data['user_id'],
                zpermission.up_code == data['up_function']
            )
            matched_data = session.query(zpermission).filter(filter_condition).all()

            for data in matched_data:
                session.delete(data)

            session.commit()
            return None
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


    def insert_by_upcode(self, data):
        try:
            session = self.session_factory()
            user_id = data["user_id"]
            print(user_id)
            print(type(data["Content"]))
            for index, value in enumerate(data["Content"]):
                print(f'Index: {index}, Value: {value}')
                zpermi = zpermission()
                zpermi.sid = 1
                zpermi.user_id = data["user_id"]
                if value.get("mname") is not None:
                    zpermi.mname = value["mname"]
                zpermi.up_code = data["up_function"]
                zpermi.f_code = value["f_code"]
                zpermi.st_func = value["st_func"]
                zpermi.sp_func = value["sp_func"]
                zpermi.func_print = value["func_print"]
                zpermi.func_add = value["func_add"]
                zpermi.func_edit = value["func_edit"]
                zpermi.func_delete = value["func_delete"]
                zpermi.func_sign = value["func_sign"]
                zpermi.func_detail = value["func_detail"]
                zpermi.func_download = value["func_download"]
                zpermi.func_other = value["func_other"]
                zpermi.busr = data.get("busr", "")
                zpermi.musr = data.get("musr", "")
                zpermi.mdtm = func.sysdatetime()
                session.add(zpermi)

            session.commit()
            return len(data["Content"])

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


    def copy(self, data):
        """
        複製來源使用者權限到目標使用者
        data: dict
            {
                "source_id": "來源使用者ID",
                "destination_id": "目標使用者ID",
                "busr": "操作使用者ID"
            }
        回傳:
            int - 複製的權限筆數（來源使用者權限數量）
        """        
        try:
            session = self.session_factory()
            # 先計算來源使用者權限筆數
            source_count = session.execute(
                text("SELECT COUNT(*) FROM [AMIS].[dbo].[zdpermi] WHERE user_id=:source_id"),
                {"source_id": data["source_id"]}
            ).scalar()  # 會回傳 int

            # 刪掉目標使用者原有權限
            session.execute(
                text("DELETE FROM [AMIS].[dbo].[zdpermi] WHERE user_id=:destination_id"),
                {"destination_id": data["destination_id"]}
            )

            # 複製來源使用者權限到目標使用者
            session.execute(
                text('''
    INSERT INTO [AMIS].[dbo].[zdpermi] (
        sid, user_id, mname, progm_id, up_code, f_code,
        st_func, sp_func, func_print, func_edit, func_sign,
        func_detail, func_download, func_other, busr
    )
    SELECT
        sid, :destination_id, mname, progm_id, up_code, f_code,
        st_func, sp_func, func_print, func_edit, func_sign,
        func_detail, func_download, func_other, :busr
    FROM [AMIS].[dbo].[zdpermi]
    WHERE user_id=:source_id
                '''),
                {
                    "destination_id": data["destination_id"],
                    "source_id": data["source_id"],
                    "busr": data["busr"]
                }
            )

            # 提交交易
            session.commit()

            # 回傳來源使用者權限筆數，作為 Length
            return source_count

        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
            logging.debug(msg)
            return 0

        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            logging.debug(msg)
            return 0

        finally:
            session.close()


    def delete(self, datum):
        try:
            session = self.session_factory()
            permi = session.query(zpermission).filter_by(
                        user_id=datum['user_id'],
                        mname=datum['machine'],
                        f_code=datum['function']
            ).one_or_none()  # 改成 one_or_none
            if permi:
                session.delete(permi)
                session.commit()
                return datum  # 刪除成功回傳刪除資料
            else:
                # 找不到資料，回傳空列表或自訂訊息
                logging.info(f"PermissionDal | No permission found for {datum}")
                return None
        except OperationalError as e:
            msg = f'{self.__class__.__name__} |An connection error occurred: {str(e)}'
            logging.debug(msg)
            return -1
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            logging.debug(msg)
            return -1
        finally:
            session.close()        
