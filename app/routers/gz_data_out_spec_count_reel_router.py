#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.gz_data_out_spec_count_reel_service import GZDataOutSpecCountReelService

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataOutSpecCountReelService = None

def get_service() -> GZDataOutSpecCountReelService:
    if service is None:
        raise RuntimeError("GZDataOutSpecCountReelService not initialized")
    return service

@router.get(
    "/GET_GZ_data_out_spec_count_reel",
    summary="查詢 GreenZone 的訊號超出規格的捲紙統計數字",
    description="透過條件查詢 GreenZone 的訊號超出規格的捲紙統計數字"
)
def get_gz_data_out_spec_count_reel(
    dFrom: str = Query(None, alias="dFrom", description="查詢日期，格式yyyy-mm-dd"),
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataOutSpecCountReelService = Depends(get_service)
):
    result = svc.get_out_spec_count_reel(dFrom, machine)
    return JSONResponse(content=result)


@router.post("/GET_GZ_data_out_spec_count_reel")
def post_gz_data_out_spec_count_reel():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

