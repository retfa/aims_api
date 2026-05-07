import logging
import datetime
import pandas as pd

from sqlalchemy import Column, Integer, String, DateTime, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from utils.db_engine import get_session
from common import add_to_dict

logger = logging.getLogger("MES_API")

Base = declarative_base()


# =========================
# Entity
# =========================
@add_to_dict
class zmuser(Base):
    __tablename__ = 'zmuser'

    user_id = Column(String(5), primary_key=True)
    user_id_hris = Column(String(9))
    user_name = Column(String(50))
    original_name = Column(String(50))
    pwd = Column(String(10))
    department_id = Column(String(50))
    dept_no = Column(String(50))
    email = Column(String(50))
    group_id = Column(String(5))
    prt = Column(String(1))
    pmdtm = Column(DateTime)
    status = Column(String(1))
    busr = Column(String(5))
    bdtm = Column(DateTime)
    musr = Column(String(5))
    mdtm = Column(DateTime)
    pwderrcount = Column(Integer)
    accession_state = Column(Integer)
    no_pay_status = Column(Integer)
    assume_date = Column(DateTime)
    leave_date = Column(DateTime)
    job_title = Column(String(20))
    job_rank = Column(Integer)
    last_sync = Column(DateTime)


# =========================
# DAL
# =========================
class UserDal:

    def __init__(self):
        try:
            self.session_factory = get_session("SRVMESDBA1_AMIS")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} | init error: {e}")

    # =========================
    # 查詢
    # =========================
    def query(self, filter):
        try:
            cond = []
            params = {}

            if getattr(filter, "user_id", None):
                cond.append("a.user_id LIKE :id")
                params["id"] = f"%{filter.user_id}%"

            if getattr(filter, "user_id_hris", None):
                cond.append("a.user_id_hris LIKE :idhris")
                params["idhris"] = f"%{filter.user_id_hris}%"

            if getattr(filter, "user_name", None):
                cond.append("a.user_name LIKE :name")
                params["name"] = f"%{filter.user_name}%"

            query_sql = """
SELECT a.*, b.user_name as busr_name
FROM zmuser a
JOIN zmuser b ON a.busr = b.user_id
            """

            if cond:
                query_sql += " WHERE " + " AND ".join(cond)

            session = self.session_factory()
            try:
                rst = session.execute(text(query_sql), params)

                df = pd.DataFrame(rst.fetchall(), columns=rst.keys())

                # 數值欄位處理
                for col in ['accession_state', 'no_pay_status', 'job_rank']:
                    if col in df.columns:
                        df[col] = df[col].astype('Int64')

                # datetime 格式轉字串
                datetime_cols = df.select_dtypes(include=['datetime64[ns]']).columns
                datetime_cols = datetime_cols.union(pd.Index(['bdtm', 'last_sync']))

                for col in datetime_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(
                            lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None
                        )

                # 移除敏感欄位
                drop_cols = [c for c in ['pwd', 'pwderrcount'] if c in df.columns]
                df = df.drop(columns=drop_cols)
                
                df = df.replace({pd.NA: None})
                df = df.where(pd.notnull(df), None)

                return df.to_dict(orient='records')

            finally:
                session.close()

        except OperationalError as e:
            logger.debug(f"{self.__class__.__name__} | DB error: {e}")
        except Exception as e:
            logger.debug(f"{self.__class__.__name__} | error: {e}")

    # =========================
    # 新增
    # =========================
    def insert(self, data):
        try:
            session = self.session_factory()
            
            # 保證 data 是 dict
            data = dict(data)

            # optional 欄位補 None
            for k in ["original_name", "department_id", "shift", "dept_no"]:
                data.setdefault(k, None)

            sql = text("""
INSERT INTO zmuser (
    user_id, user_id_hris, user_name, original_name, pwd,
    department_id, dept_no, group_id, email,
    assume_date, job_title, job_rank, prt, busr
)
VALUES (
    :user_id, :user_id_hris, :user_name, :original_name, :pwd,
    :department_id, :dept_no, :group_id, :email,
    :assume_date, :job_title, :job_rank, :prt, :busr
)
            """)

            session.execute(sql, data)
            session.commit()
            return data["user_id"]

        except Exception as e:
            print(e)
            logger.debug(f"{self.__class__.__name__} | insert error: {e}")
            return -1
        finally:
            session.close()

    # =========================
    # 重設密碼
    # =========================
    def reset_password(self, data):
        try:
            session = self.session_factory()

            session.execute(text("""
UPDATE zmuser
SET pwd = 'a0000000',
    musr = :musr,
    mdtm = SYSDATETIME()
WHERE user_id = :user_id
            """), data)

            session.commit()

        finally:
            session.close()

    # =========================
    # 修改密碼
    # =========================
    def update_password(self, data):
        try:
            session = self.session_factory()

            session.execute(text("""
UPDATE zmuser
SET pwd = :new_password,
    musr = :musr,
    mdtm = SYSDATETIME()
WHERE user_id = :user_id
            """), data)

            session.commit()

        finally:
            session.close()

    # =========================
    # 狀態更新
    # =========================
    def update_status(self, data):
        try:
            session = self.session_factory()

            session.execute(text("""
UPDATE zmuser
SET status = :status,
    musr = :musr,
    mdtm = SYSDATETIME()
WHERE user_id = :user_id
            """), {
                "status": 'Y' if data["status"] == 'Y' else 'N',
                "musr": data["musr"],
                "user_id": data["user_id"]
            })

            session.commit()

        finally:
            session.close()

    # =========================
    # 更新
    # =========================
    def update(self, data):
        try:
            session = self.session_factory()

            update_fields = []
            params = {"user_id": data["user_id"]}

            allow_fields = [
                "user_id_hris", "user_name", "original_name",
                "department_id", "dept_no", "group_id", "prt",
                "email", "accession_state", "no_pay_status",
                "assume_date", "leave_date",
                "job_title", "job_rank"
            ]

            for field in allow_fields:
                if field in data:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = data[field]

            update_fields.append("musr = :musr")
            update_fields.append("mdtm = SYSDATETIME()")
            params["musr"] = data["musr"]

            sql = f"""
UPDATE zmuser
SET {', '.join(update_fields)}
WHERE user_id = :user_id
            """

            session.execute(text(sql), params)
            session.commit()

        finally:
            session.close()

    # =========================
    # 單筆查詢
    # =========================
    def select(self, user_id):
        try:
            session = self.session_factory()

            rst = session.execute(
                text("SELECT * FROM zmuser WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()

            if rst:
                return dict(rst._mapping)
            return None

        finally:
            session.close()