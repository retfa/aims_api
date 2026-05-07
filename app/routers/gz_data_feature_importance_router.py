#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse

from services.gz_data_feature_importance_service import GZDataFeatureImportanceService

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataFeatureImportanceService = None

def get_service() -> GZDataFeatureImportanceService:
    if service is None:
        raise RuntimeError("GZDataFeatureImportanceService not initialized")
    return service

@router.get(
    "/GET_GZ_data_feature_importance",
    summary="查詢 GreenZone 的重要變數",
    description="透過條件查詢 GreenZone 的重要變數"
)
def get_gz_data_feature_importance(
    stime: str = Query(None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    variable_name: str = Query(None, alias="VariableName", description="欲查詢變數，格式只能為以下四種「METROLOGY-COATINGWEIGHT」、「METROLOGY-COATINGWEIGHT-2SIGMA」、「METROLOGY-P21-MO1-SP」、「METROLOGY-P21-MO1-SP-2SIGMA」"),
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataFeatureImportanceService = Depends(get_service)
):

    result = svc.get_feature_importance(
        stime,
        etime,
        variable_name,
        machine
    )

    return JSONResponse(content=result)


@router.post("/GET_GZ_data_feature_importance")
def post_gz_data_feature_importance():

    return JSONResponse(
        content={
            "success": False,
            "message": "Please use GET"
        }
    )

