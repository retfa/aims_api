#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class GZDataGramgSpeedQuery(BaseModel):
    Stime: Optional[str]
    Etime: Optional[str]
    MachineName: Optional[str]

