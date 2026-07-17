from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
import time
from datetime import datetime

from services.mes_service import MESService
from schemas.energy_schema import PatchEnergyBody
from core.security import verify_jwt

router = APIRouter(
    prefix="/energy-daily-settlement",
    tags=["energy-daily-settlement"]
)

service: MESService = None

def get_service() -> MESService:
    if service is None:
        raise RuntimeError("MESService not initialized for energy_router")
    return service

@router.get("", summary="查詢汽電紀錄")
async def get_energy_record(
    date: str = Query(..., description="查詢日期 (格式: yyyy-mm-dd)", example="2026-04-18"),
    svc: MESService = Depends(get_service),
    jwt_payload = Depends(verify_jwt)
):
    start_time = time.time()
    
    try:
        record = svc.get_energy_record(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not record:
        raise HTTPException(
            status_code=404, 
            detail=f"找不到該日期的能量日結算紀錄: {date}"
        )
    
    execution_time = time.time() - start_time
    return {
        "data": {
            "Action": "GET",
            "Content": record,
            "ExecutionTime": f"{execution_time:.2f} ms",
            "ExecutionDto": datetime.now().isoformat(),
            "Length": 1
        },
        "success": True,
        "status_code": 200
    }

@router.patch("", summary="修改特定日期的部分能量參數")
async def patch_energy_record(
    body: PatchEnergyBody,
    svc: MESService = Depends(get_service),
    jwt_payload = Depends(verify_jwt)
):
    start_time = time.time()
    user_info = jwt_payload if jwt_payload else {"FTAId": "SYSTEM"}
    
    sdate = body.sdate
    
    # 將 body 轉為 dict，排除未傳入欄位並還原 alias 鍵名 (得到原始數字鍵)
    update_data = body.dict(exclude_unset=True, by_alias=True)
    
    # 移除定位主鍵 sdate
    update_data.pop("sdate", None)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="沒有提供任何需要更新的欄位")
        
    try:
        res = svc.patch_energy_record(
            sdate=sdate.strftime("%Y-%m-%d %H:%M:%S"),
            body=update_data,
            user_info=user_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if not res.get("success", False):
        raise HTTPException(status_code=400, detail=res.get("message", "更新失敗"))
        
    execution_time = time.time() - start_time
    return {
        "data": {
            "Action": "PATCH",
            "Content": res.get("data"),
            "ExecutionTime": f"{execution_time:.2f} ms",
            "ExecutionDto": datetime.now().isoformat(),
            "Length": 1
        },
        "success": True,
        "status_code": 200
    }
