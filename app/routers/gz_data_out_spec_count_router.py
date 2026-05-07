#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.gz_data_out_spec_count_service import GZDataOutSpecCountService

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataOutSpecCountService = None

def get_service() -> GZDataOutSpecCountService:
    if service is None:
        raise RuntimeError("GZDataOutSpecCountService not initialized")
    return service

@router.get(
    "/GET_GZ_data_out_spec_count",
    summary="查詢 GreenZone 的訊號超出規格的詳細內容",
    description="透過條件查詢 GreenZone 的訊號超出規格的詳細內容"
)
def get_gz_data_out_spec_count(
    stime: str = Query(None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataOutSpecCountService = Depends(get_service)
):
    result = svc.get_out_spec_count(stime, etime, machine)
    return JSONResponse(content=result)


@router.post("/GET_GZ_data_out_spec_count")
def post_gz_data_out_spec_count():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

