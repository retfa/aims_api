from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
import time
from services.mes_service import MESService
from schemas.truck_scale_schema import GetTruckScalePayloads, PostTruckScalePayload, PutTruckScalePayload, DeleteTruckScalePayload, ItemNameEnum
from core.security import verify_jwt

router = APIRouter(
    prefix="/truck_scale_payloads",
    tags=["TruckScalePayloads"]
)

service: MESService = None

def get_service() -> MESService:
    if service is None:
        raise RuntimeError("MESService not initialized for truck_scale_router")
    return service

@router.get("/item_names", summary="取得可用的項目名稱清單")
async def get_item_name_options(
    svc: MESService = Depends(get_service),
    jwt_payload = Depends(verify_jwt)
):
    options = [
        {"value": ItemNameEnum.fiber.value, "label": "纖維"},
        {"value": ItemNameEnum.coal.value, "label": "煤炭"},
        {"value": ItemNameEnum.sludge.value, "label": "污泥"},
    ]
    return {
        "data": {
            "Action": "GET",
            "Content": options,
            "ExecutionTime": "0 ms",
            "ExecutionDto": datetime.now().isoformat(),
            "Length": len(options)
        },
        "success": True,
        "status_code": 200
    }

@router.get("", summary="查詢 Payload 紀錄")
async def get_payload_records(
    category: str = Query(None, description="分類篩選", example="CategoryA"),
    svc: MESService = Depends(get_service),
    jwt_payload = Depends(verify_jwt)
):
    start_time = time.time()
    
    try:
        content = svc.get_truck_scale_payloads(category=category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    execution_time = (time.time() - start_time) * 1000
    return {
        "data": {
            "Action": "GET",
            "Content": content,
            "ExecutionTime": f"{execution_time:.2f} ms",
            "ExecutionDto": datetime.now().isoformat(),
            "Length": len(content)
        },
        "success": True,
        "status_code": 200
    }

@router.post("", summary="新增 Payload 紀錄")
async def create_payload_record(
    params: PostTruckScalePayload,
    svc: MESService = Depends(get_service),
    jwt_payload = Depends(verify_jwt)
):
    start_time = time.time()
    
    try:
        res = svc.create_truck_scale_payload(
            category=params.category.value,
            item_name=params.item_name,
            item_code=params.item_code,
            company=params.company,
            company_code=params.company_code,
            description=params.description,
            category_order=params.category_order
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if not res.get("success", False):
        raise HTTPException(status_code=409, detail=res.get("message", "新增失敗"))
        
    execution_time = (time.time() - start_time) * 1000
    return {
        "data": {
            "Action": "POST",
            "Content": res.get("data"),
            "ExecutionTime": f"{execution_time:.2f} ms",
            "ExecutionDto": datetime.now().isoformat(),
            "Length": 1
        },
        "success": True,
        "status_code": 200
    }
 
@router.put("", summary="更新 Payload 紀錄")
async def update_payload_record(
    params: PutTruckScalePayload,
    svc: MESService = Depends(get_service),
    jwt_payload = Depends(verify_jwt)
):
    start_time = time.time()
    
    try:
        res = svc.update_truck_scale_payload(
            id=params.id,
            category=params.category.value if params.category is not None else None,
            item_name=params.item_name,
            item_code=params.item_code,
            company=params.company,
            company_code=params.company_code,
            description=params.description,
            category_order=params.category_order
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if not res.get("success", False):
        status_code = 404 if "找不到" in res.get("message", "") else 400
        raise HTTPException(status_code=status_code, detail=res.get("message", "更新失敗"))
        
    execution_time = (time.time() - start_time) * 1000
    return {
        "data": {
            "Action": "PUT",
            "Content": res.get("data"),
            "ExecutionTime": f"{execution_time:.2f} ms",
            "ExecutionDto": datetime.now().isoformat(),
            "Length": 1
        },
        "success": True,
        "status_code": 200
    }

@router.delete("", summary="刪除 Payload 紀錄")
async def delete_payload_record(
    params: DeleteTruckScalePayload,
    svc: MESService = Depends(get_service),
    jwt_payload = Depends(verify_jwt)
):
    start_time = time.time()
    
    try:
        res = svc.delete_truck_scale_payload(id=params.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if not res.get("success", False):
        raise HTTPException(status_code=404, detail=res.get("message", "刪除失敗"))
        
    execution_time = (time.time() - start_time) * 1000
    return {
        "data": {
            "Action": "DELETE",
            "Content": res.get("data"),
            "ExecutionTime": f"{execution_time:.2f} ms",
            "ExecutionDto": datetime.now().isoformat(),
            "Length": 1
        },
        "success": True,
        "status_code": 200
    }
