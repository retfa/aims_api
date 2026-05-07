#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Query, Path, Body
from fastapi.responses import JSONResponse

from services.outputlist_service import OutputListService
from schemas.outputlist_schema import OutputListPostModel

router = APIRouter(prefix="/WSP", tags=["WSP"])

service: OutputListService = None

def get_service():
    if service is None:
        raise RuntimeError("outputlistService not initialized")
    return service

@router.get("/outputlist", summary="查詢 outputlist")
def query_outputlist(
    sn: int = Query(None, description="主鍵 Sn"),
    svc: OutputListService = Depends(get_service)
):
    return JSONResponse(content=svc.query(sn))

@router.post("/outputlist", summary="新增或更新 outputlist")
def upsert_outputlist(
    data: OutputListPostModel = Body(...),
    svc: OutputListService = Depends(get_service)
):
    return JSONResponse(content=svc.upsert(data))

@router.delete("/outputlist/{sn}", summary="刪除 outputlist（含明細）")
def delete_outputlist(
    sn: int = Path(...),
    svc: OutputListService = Depends(get_service)
):
    return JSONResponse(content=svc.delete(sn))

