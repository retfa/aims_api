#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class GZDataDiffDataFeatureImportanceQuery(BaseModel):
    VariableName: Optional[str]
    MachineName: Optional[str]
    ptype: Optional[str]
    smax: Optional[str]
    smin: Optional[str]
    qdate: Optional[str]  # timetag
    bdate: Optional[str]
    cdate: Optional[str]
    wmax: Optional[str]
    wmin: Optional[str]

