#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse

from services.gz_data_service import GZDataService


router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataService = None


def get_service() -> GZDataService:
    if service is None:
        raise RuntimeError("GZDataService not initialized")
    return service


@router.get(
    "/GET_GZ_data",
    summary="查詢 GreenZone 資料",
    description="透過條件查詢 GreenZone 資料"
)
def get_gz_data(
    stime: str = Query(None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    variable_Name: str = Query(None, alias="VariableName", description="欲查詢變數，格式包含「METROLOGY-COATINGWEIGHT」、「METROLOGY-COATINGWEIGHT-2SIGMA」、「METROLOGY-P21-MO1-SP」、「METROLOGY-P21-MO1-SP-2SIGMA」或「ACDRY-DCS_A103」"),
    MachineName: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataService = Depends(get_service)
):

    result = svc.get_data(
        stime,
        etime,
        variable_Name,
        MachineName
    )

    return JSONResponse(content=result)


@router.post("/GET_GZ_data")
def post_gz_data():

    return JSONResponse(
        content={
            "success": False,
            "message": "Please use GET"
        }
    )

