#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter
import logging

router = APIRouter(
    prefix="/permission-cross-department",
    tags=["PermissionCrossDepartment"]
)

logger = logging.getLogger("MES_API")

@router.get("/")
def health():
    logger.info("healthcheck API called")
    return {
        "status": "Healthy",
        "version": "1.0.0",
        "details": None
    }

