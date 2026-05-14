#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.gz_data_outputlist_service import GZDataOutputlistService

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataOutputlistService = None

def get_service() -> GZDataOutputlistService:
    if service is None:
        raise RuntimeError("GZDataOutputlistService not initialized")
    return service

@router.get(
    "/GET_GZ_data_Outputlist",
    summary="查詢 GreenZone 的訊號代碼與中文名稱",
    description="透過條件查詢 GreenZone 的訊號代碼與中文名稱"
)
def get_gz_data_outputlist(
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataOutputlistService = Depends(get_service)
):
    result = svc.get_outputlist(machine)
    return JSONResponse(content=result)


@router.post("/GET_GZ_data_Outputlist")
def post_gz_data_outputlist():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

