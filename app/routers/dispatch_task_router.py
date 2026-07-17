#!/usr/bin/env python
# coding: utf-8



#!/usr/bin/env python
# coding: utf-8

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dispatch_task", tags=["DispatchTask"])

# 由 main.py 的 create_app() 注入
service = None


@router.post("/trigger", summary="手動觸發每日派車排程任務")
def trigger_task():
    result = service.trigger()
    if not result["acquired"]:
        raise HTTPException(status_code=409, detail="任務正在執行中，請稍後再試")
    return {"trigger_id": result["trigger_id"], "status": result["status"]}


@router.get("/status", summary="查詢每日派車排程任務執行狀態")
def get_task_status():
    return service.get_status()

