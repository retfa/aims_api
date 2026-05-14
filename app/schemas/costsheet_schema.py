#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class ProductCostDetailsQuery(BaseModel):
    stime: Optional[str]
    etime: Optional[str]
    mname: Optional[str]
    category: Optional[str]
    ptype_two: Optional[str]
    two_month: Optional[str]
    level: Optional[str]

class ProductCostEquivalentQuery(BaseModel):
    stime: Optional[str]
    etime: Optional[str]
    mname: Optional[str]
    category: Optional[str]
    ptype_two: Optional[str]
    two_month: Optional[str]

class MonthlyEquivalentProductionQuery(BaseModel):
    year: Optional[str]

class MonthlyERPInventoryQuery(BaseModel):
    year: Optional[str]

class MonthlyYieldRateQuery(BaseModel):
    year: Optional[str]

class ERPInventoryQuery(BaseModel):
    date_from: Optional[str]
    date_to: Optional[str]
    machine_name: Optional[str]
    month: Optional[str]

class EndWorkInProcessQuery(BaseModel):
    year_month_from: Optional[str]

class MonthlyFixedFeeQuery(BaseModel):
    year: Optional[str]

class MonthlyEnergyUsageQuery(BaseModel):
    year: Optional[str]

class MonthlyCostSheetQuery(BaseModel):
    year_month_From: Optional[str]
    mname: Optional[str]
    year: Optional[str]
    ptype2: Optional[str]

