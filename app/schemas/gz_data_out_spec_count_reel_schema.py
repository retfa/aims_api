#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class GZDataOutSpecCountReelQuery(BaseModel):
    dFrom: Optional[str]
    MachineName: Optional[str]

