#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class GZDataPredictionStatusQuery(BaseModel):
    MachineName: Optional[str]

