#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class MESBaseQuery(BaseModel):
    stime: Optional[str]
    etime: Optional[str]
    mname: Optional[str]  
        
class MESAmreelGroupByPtimeQuery(BaseModel):
    stime: Optional[str]
    etime: Optional[str]
    mname: Optional[str]
    MachineCode: Optional[str]  
        
class AmpaperCategoryQuery(BaseModel):
    date_from: Optional[str]
    date_to: Optional[str]
    machine_name: Optional[str]
    mode: Optional[str]
    year_month_from: Optional[str]

class DefectReportQuery(BaseModel):
    yearMonthFrom: Optional[str]
    yearMonthTo: Optional[str]
    machineName: Optional[str]

class YieldDailyReportQuery(BaseModel):
    date_from: Optional[str]
    date_to: Optional[str]
    machine_name: Optional[str]
    category: Optional[str]

class RelnoProductionHistoryQuery(BaseModel):
    relno: Optional[str]        

