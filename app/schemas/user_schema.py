#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime


class UserQuery(BaseModel):
    user_id: Optional[str] = None
    user_id_hris: Optional[str] = None
    user_name: Optional[str] = None


class UserAdd(BaseModel):
    user_id: str
    user_id_hris: Optional[str] = None
    user_name: Optional[str] = None
    original_name: Optional[str] = None
    pwd: Optional[str] = None
    department_id: Optional[str] = None
    dept_no: Optional[str] = None
    email: Optional[str] = None
    group_id: Optional[str] = None
    shift: Optional[str] = None
    assume_date: Optional[str] = None  # 如果想用 datetime 可改成: Optional[datetime]
    job_title: Optional[str] = None
    job_rank: Optional[int] = 0

class UserEdit(BaseModel):
    user_name: Optional[str]


class UserPasswordEdit(BaseModel):
    password: str


class UserStatusEdit(BaseModel):
    status: str


class UserItem(BaseModel):
    user_id: str
    user_id_hris: Optional[str]
    user_name: Optional[str]
    original_name: Optional[str]
    department_id: Optional[str]
    dept_no: Optional[str]
    email: Optional[str]
    group_id: Optional[str]
    prt: Optional[str]
    pmdtm: Optional[str]
    status: Optional[str]
    shift: Optional[str]
    accession_state: Optional[int]
    no_pay_status: Optional[int]
    assume_date: Optional[str]
    leave_date: Optional[str]
    job_title: Optional[str]
    job_rank: Optional[int]
    last_sync: Optional[str]
    busr: Optional[str]
    bdtm: Optional[str]
    musr: Optional[str]
    mdtm: Optional[str]
    busr_name: Optional[str]
        
    # 新增 DB 裏原本缺少的欄位
    emp_guid: Optional[str]
    com: Optional[str]
    cellphone1: Optional[str]
    cellphone2: Optional[str]
    officephone: Optional[str]
    create_date: Optional[str] 
        
class UserResult(BaseModel):
    user_id: Optional[str]
    success: bool
    message: str

class UserResponse(BaseModel):
    Action: str
    Content: List[Union[UserItem, UserResult]]
    ExecutionTime: str
    ExecutionDto: str
    Length: int


class FtaResponseUser(BaseModel):
    data: UserResponse
    status_code: int
    success: bool
        
        
class EmploeeItem(BaseModel):
    Emp_Guid: str
    COM: Optional[str]
    Emp_ID: str
    Email: Optional[str]
    Emp_Name: Optional[str]
    Emp_EName: Optional[str]
    Department_ID: Optional[str]
    Department_ID2: Optional[str]
    Job_Title: Optional[str]
    Assume_Date: Optional[str]          # 如果想要 datetime 可改成 Optional[datetime]
    Leave_Date: Optional[str]           # 同上
    CreateDate: Optional[str]           # 同上
    AccessionState: Optional[int]
    NoPayStatus: Optional[int]
    jobrank: Optional[int]
    cellphone1: Optional[str]
    cellphone2: Optional[str]
    officephone: Optional[str]
    emp_id_hr: Optional[str]
    last_sync: Optional[str]            # 同上
    shift: Optional[str]
        
class EmploeeResponse(BaseModel):
    Action: str
    Content: List[EmploeeItem]
    ExecutionTime: str
    ExecutionDto: str
    Length: int


class FtaResponseEmploee(BaseModel):
    data: EmploeeResponse
    status_code: int
    success: bool        

