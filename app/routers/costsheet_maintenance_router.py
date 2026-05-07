#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse
from services.costsheet_maintenance_service import CoatingWeightService

router = APIRouter(prefix="/MES/CostSheet", tags=["CostSheet_Maintenance"])
service: CoatingWeightService = None

def get_service() -> CoatingWeightService:
    if service is None:
        raise RuntimeError("CoatingWeightService not initialized")
    return service


@router.get("/CoatingWeight",
        summary="查詢 塗佈量設定",
        description="透過條件查詢 塗佈量設定")
def get_coating_weight(svc: CoatingWeightService = Depends(get_service)):
    result = svc.get_all()
    return JSONResponse(content=result)


@router.post("/CoatingWeight",
    summary="新增 塗佈量設定",
    description="利用 POST 新增一筆 CoatingWeight 記錄，請依照下方範例提供所有欄位。")
def create_coating_weight(payload: CoatingWeightModel, svc: CoatingWeightService = Depends(get_service)):
    result = svc.create(payload)
    return JSONResponse(content=result)


@router.put("/CoatingWeight/{sn}",
    summary="更新 塗佈量設定",
    description="可更新任意欄位，未提供的欄位不會修改。")
def update_coating_weight(
    sn: int = Path(..., description="CoatingWeight 的 Sn 編號"),
    payload: CoatingWeightUpdateModel = ...,
    svc: CoatingWeightService = Depends(get_service)
):
    result = svc.update(sn, payload)
    return JSONResponse(content=result)


@router.delete("/CoatingWeight/{sn}",
    summary="刪除塗佈量設定",
    description="依照 Sn 刪除指定的 CoatingWeight 記錄。")
def delete_coating_weight(sn: int = Path(..., description="CoatingWeight 的 Sn 編號"),
                          svc: CoatingWeightService = Depends(get_service)):
    result = svc.delete(sn)
    return JSONResponse(content=result)

