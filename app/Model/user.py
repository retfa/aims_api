from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


# =======================
# User Models (Pydantic)
# =======================

class UserLogin(BaseModel):
    login_id: str
    password: str


class UserSignedIn(BaseModel):
    FTAId: str
    YFYId: str
    Name: str
    FTASn: int


class UserFilter(BaseModel):
    FTAId: Optional[str] = None
    YFYId: Optional[str] = None
    Name: Optional[str] = None


class UserAdd(BaseModel):
    user_id: str
    user_id_hris: str
    user_name: str
    original_name: Optional[str] = None
    department_id: Optional[str] = None
    dept_no: Optional[str] = None
    email: EmailStr
    group_id: Optional[str] = None
    pwd: Optional[str] = None
    shift: Optional[str] = None
    assume_date: Optional[str] = None
    job_title: Optional[str] = None
    job_rank: int


class ImplicitUserAdd(UserAdd):
    prt: str = 'Y'
    busr: str


class UserEdit(BaseModel):
    user_id_hris: Optional[str] = None
    user_name: Optional[str] = None
    original_name: Optional[str] = None
    department_id: Optional[str] = None
    dept_no: Optional[str] = None
    email: Optional[EmailStr] = None
    group_id: Optional[str] = None
    prt: Optional[str] = None
    status: Optional[str] = None
    shift: Optional[str] = None
    accession_state: Optional[int] = None
    no_pay_status: Optional[int] = None
    assume_date: Optional[str] = None
    leave_date: Optional[datetime] = None
    job_title: Optional[str] = None
    job_rank: Optional[int] = None


class ImplicitUserEdit(UserEdit):
    user_id: str
    musr: str


class UserPasswordEdit(BaseModel):
    old_password: str
    new_password: str


class ImplicitUserPasswordEdit(UserPasswordEdit):
    user_id: str
    musr: str


class UserStatusEdit(BaseModel):
    status: str


class ImplicitUserStatusEdit(UserStatusEdit):
    user_id: str
    musr: str


class User(BaseModel):
    user_id: str
    user_id_hris: str
    user_name: str
    original_name: str
    department_id: str
    dept_no: Optional[str] = None
    email: EmailStr
    group_id: str
    prt: str
    pmdtm: datetime
    status: str
    shift: str
    accession_state: int
    no_pay_status: int
    assume_date: datetime
    leave_date: Optional[datetime] = None
    job_title: str
    job_rank: int
    last_sync: datetime