#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class GZDataDiffDataQuery(BaseModel):
    VariableName: Optional[str]
    MachineName: Optional[str]
    ptype: Optional[str]
    smax: Optional[str]
    smin: Optional[str]
    bdate: Optional[str]
    wmax: Optional[str]
    wmin: Optional[str]

