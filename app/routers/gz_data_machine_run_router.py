#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.gz_data_machine_run_service import GZDataMachineRunService

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataMachineRunService = None

def get_service() -> GZDataMachineRunService:
    if service is None:
        raise RuntimeError("GZDataMachineRunService not initialized")
    return service

@router.get(
    "/GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung",
    summary="查詢 GreenZone 的狀態，包含停車、段紙、標準化...等資訊",
    description="透過條件查詢 GreenZone 的狀態，包含停車、段紙、標準化...等資訊"
)
def get_gz_data_machine_run(
    stime: str = Query(None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    machine: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataMachineRunService = Depends(get_service)
):
    result = svc.get_machine_run(stime, etime, machine)
    return JSONResponse(content=result)


@router.post("/GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung")
def post_gz_data_machine_run():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

