#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel

class LoginModel(BaseModel):
    acc: str
    pwd: str

