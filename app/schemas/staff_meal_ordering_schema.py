#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional, List


class StaffMealOrderingContentModel(BaseModel):
    year: Optional[str] = None
    month: Optional[str] = None
    day: Optional[str] = None
    cardno: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    dn: Optional[str] = None
    food: Optional[str] = None
    foodName: Optional[str] = None


class StaffMealOrderingResponseModel(BaseModel):
    Content: List[StaffMealOrderingContentModel]


class StaffMealOrderingModel(BaseModel):
    cardno: str
    nad: str
    cktime: str
    loca: str
    locaName: str
    Category: str

    class Config:
        json_schema_extra = {
            "example": {
              "Category": "01",
              "cardno": "A5558",
              "cktime": "2026-03-24 10:26:00.000",
              "loca": "10.10.1.62",
              "locaName": "舊廠便當機",
              "nad": "01"
            }
        }
        
class GuestMealOrderingModel(BaseModel):
    cardno: str
    mtype: str
    cnt_02: str
    cnt_03: str
    code: str
    cktime: str
    con_name: str
    memo: Optional[str] = ""

    class Config:
        json_schema_extra = {
            "example": {
                "cardno": "A5558",
                "mtype": "dinner",
                "cnt_02": "0",
                "cnt_03": "1",
                "code": "A01",
                "cktime": "2026-03-24 15:30:00",
                "con_name": "超人有限公司",
                "memo": ""
            }
        }        
        
class DepartmentContentModel(BaseModel):
    Emp_ID: str
    Emp_Name: str
    Department_ID: str
    emp_id_hr: str
    dept_name: Optional[str] = None

class DepartmentResponseModel(BaseModel):
    Content: List[DepartmentContentModel]        

