#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
# import logging

router = APIRouter()
# logger = logging.getLogger("MES_API")

@router.get("/secure")
def secure_api(user=Depends(get_current_user)):
    return user

