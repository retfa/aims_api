#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from services.system_service import SystemService

router = APIRouter(prefix="", tags=["System"])

# 初始化 service
service: SystemService = None

def get_service() -> SystemService:
    if service is None:
        raise RuntimeError("SystemService not initialized")
    return service

# -------------------------
# 根目錄
# -------------------------
@router.get("/", summary="根目錄", description="取得根目錄")
def root():
    return {"success": True, "message": "GET OK"}

# -------------------------
# 系統時間 GET
# -------------------------
@router.get("/System/CurrentTime",
    summary="系統時間",
    description="取得系統時間")
def get_current_time(svc: SystemService = Depends(get_service)):
    result = svc.fetch_current_time()
    return JSONResponse(content=result, media_type="application/json")

# -------------------------
# 系統時間 POST (禁止使用)
# -------------------------
@router.post("/System/CurrentTime",
    summary="系統時間",
    description="請使用 GET 取得系統時間")
def post_current_time():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

