#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.gz_data_gramg_speed_service import GZDataGramgSpeedService

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataGramgSpeedService = None

def get_service() -> GZDataGramgSpeedService:
    if service is None:
        raise RuntimeError("GZDataGramgSpeedService not initialized")
    return service

@router.get(
    "/GET_GZ_data_gramg_speed",
    summary="查詢 GreenZone 的基重與車速",
    description="透過條件查詢 GreenZone 的基重與車速"
)
def get_gz_data_gramg_speed(
    stime: str = Query(None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataGramgSpeedService = Depends(get_service)
):
    result = svc.get_gramg_speed(stime, etime, machine)
    return JSONResponse(content=result)


@router.post("/GET_GZ_data_gramg_speed")
def post_gz_data_gramg_speed():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

