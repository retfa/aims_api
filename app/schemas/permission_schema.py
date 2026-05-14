#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PermissionQuery(BaseModel):
    function: Optional[str] = None
    up_function: Optional[str] = None
    progm_id: Optional[str] = None

class PermissionCopyQuery(BaseModel):
    source_id: str
        
class PermissionItem(BaseModel):
    sid: Optional[str] = None
    user_id: str

    # 基本欄位
    mname: Optional[str] = None
    progm_id: Optional[str] = None
    up_code: Optional[str] = None
    f_code: Optional[str] = None

    # 權限欄位
    st_func: Optional[str] = None
    sp_func: Optional[str] = None
    func_print: Optional[str] = None
    func_add: Optional[str] = None
    func_edit: Optional[str] = None
    func_delete: Optional[str] = None
    func_sign: Optional[str] = None
    func_detail: Optional[str] = None
    func_download: Optional[str] = None
    func_other: Optional[str] = None

    # 建立/修改資訊
    busr: Optional[str] = None
    bdtm: Optional[datetime] = None
    musr: Optional[str] = None
    mdtm: Optional[datetime] = None

    # 使用者資訊
    user_name: Optional[str] = None
    dept_name: Optional[str] = None

    # 系統/功能資訊
    pname: Optional[str] = None
    f_name: Optional[str] = None
    pm: Optional[str] = None
    station: Optional[str] = None

# FtaResult 結構
class PermissionResponse(BaseModel):
    Action: str = ""
    Content: List[PermissionItem]
    ExecutionDto: str = ""
    ExecutionTime: str
    Length: int

class FtaResponsePermission(BaseModel):
    data: PermissionResponse
    status_code: int
    success: bool

