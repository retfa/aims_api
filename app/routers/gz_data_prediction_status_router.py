#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.gz_data_prediction_status_service import GZDataPredictionStatusService

router = APIRouter(
    prefix="/greenzone",
    tags=["GreenZone"]
)

service: GZDataPredictionStatusService = None

def get_service() -> GZDataPredictionStatusService:
    if service is None:
        raise RuntimeError("GZDataPredictionStatusService not initialized")
    return service

@router.get(
    "/prediction-status",
    summary="查詢 GreenZone 的機台生產狀態",
    description="透過條件查詢 GreenZone 的機台生產狀態"
)
def get_gz_data_prediction_status(
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataPredictionStatusService = Depends(get_service)
):
    result = svc.get_prediction_status(machine)
    return JSONResponse(content=result)


@router.post("/prediction-status")
def post_gz_data_prediction_status():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

