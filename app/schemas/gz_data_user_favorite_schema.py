#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional, List

class GZDataUserFavoriteQuery(BaseModel):
    Isfavorite: Optional[str]
    MachineName: Optional[str]

class GZDataUserFavoriteUpdate(BaseModel):
    favorite_list: List[str]

