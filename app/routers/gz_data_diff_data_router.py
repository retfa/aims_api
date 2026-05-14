#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.gz_data_diff_data_service import GZDataDiffDataService

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataDiffDataService = None

def get_service() -> GZDataDiffDataService:
    if service is None:
        raise RuntimeError("GZDataDiffDataService not initialized")
    return service

@router.get(
    "/GET_GZ_data_diff_data",
    summary="查詢 GreenZone 的差異分析資料",
    description="透過條件查詢 GreenZone 的差異分析資料"
)
def get_gz_data_diff_data(
    variable_name: str = Query(None, alias="VariableName", description="欲查詢變數，格式只能為「METROLOGY-COATINGWEIGHT」、「METROLOGY-P21-MO1-SP」"),
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    ptype: str = Query(None, alias="ptype", description="格式 四碼紙別 如KL00"),
    smax: str = Query(None, alias="smax", description="格式 車速最大值 如941"),
    smin: str = Query(None, alias="smin", description="格式 車速最小值 如851"),
    bdate: str = Query(None, alias="bdate", description="格式 歸屬日期 yyyy-mm-dd"),
    wmax: str = Query(None, alias="wmax", description="格式 基重最大值 如61"),
    wmin: str = Query(None, alias="wmin", description="格式 基重最小值 如55"),
    svc: GZDataDiffDataService = Depends(get_service)
):
    result = svc.get_diff_data(variable_name, machine, ptype, smax, smin, bdate, wmax, wmin)
    return JSONResponse(content=result)


@router.post("/GET_GZ_data_diff_data")
def post_gz_data_diff_data():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

