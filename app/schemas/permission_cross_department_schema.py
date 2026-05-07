#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 查詢用 DTO
class PermissionCrossDepartmentQuery(BaseModel):
    user_id: Optional[str] = None
    progm_id: Optional[str] = None

class PermissionCrossDepartmentEdit(BaseModel):
    progm_id: str
    departments: str

# 單筆權限項目
class PermissionCrossDepartmentItem(BaseModel):
    Sn: Optional[int] = None
    user_id: str
    progm_id: Optional[str] = None
    departments: Optional[str] = None
    IsEnabled: Optional[bool] = None
    busr: Optional[str] = None
    bdtm: Optional[datetime] = None
    musr: Optional[str] = None
    mdtm: Optional[datetime] = None        

# 回傳結構
class PermissionCrossDepartmentResponse(BaseModel):
    Action: str
    Content: List[PermissionCrossDepartmentItem]
    ExecutionTime: str
    ExecutionDto: str
    Length: int

class FtaResponsePermissionCrossDepartment(BaseModel):
    data: PermissionCrossDepartmentResponse
    status_code: int
    success: bool

