#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class GZDataFeatureImportanceQuery(BaseModel):
    Stime: Optional[str]
    Etime: Optional[str]
    VariableName: Optional[str]
    MachineName: Optional[str]

