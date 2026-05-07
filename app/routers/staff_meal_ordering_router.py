#!/usr/bin/env python
# coding: utf-8

# In[1]:


from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse

from services.staff_meal_ordering_service import StaffMealOrderingService
from schemas.staff_meal_ordering_schema import (
    StaffMealOrderingModel,
    StaffMealOrderingResponseModel,
    GuestMealOrderingModel,
    DepartmentResponseModel
)

router = APIRouter(
    prefix="/Staff_meal_ordering_system",
    tags=["Staff_meal_ordering_system"]
)

service: StaffMealOrderingService = None


def get_service():
    if service is None:
        raise RuntimeError("StaffMealOrderingService not initialized")
    return service


# -------------------------
# 查詢
# -------------------------
@router.get(
    "/Staff_meal_ordering_query",
    summary="查詢 員工訂餐紀錄",
    response_model=StaffMealOrderingResponseModel
)
def get_staff_meal_ordering(
    year: str = Query(None),
    month: str = Query(None),
    day: str = Query(None),
    cardno: str = Query(None),
    code: str = Query(None),
    dn: str = Query(None),
    food: str = Query(None),
    OG_name: str = Query(None),
    svc: StaffMealOrderingService = Depends(get_service)
):

    result = svc.fetch(year, month, day, cardno, code, dn, food, OG_name)  

    return JSONResponse(content=result)


# -------------------------
# 新增
# -------------------------
@router.post(
    "/Staff_meal_ordering_query",
    summary="新增員工餐點紀錄"
)
def create_staff_meal_ordering(
    payload: StaffMealOrderingModel,
    svc: StaffMealOrderingService = Depends(get_service)
):

    result = svc.create(payload)

    return JSONResponse(content=result)


# -------------------------
# 刪除
# -------------------------
@router.delete(
    "/Staff_meal_ordering_query/{sid}",
    summary="刪除員工餐點紀錄"
)
def delete_staff_meal_ordering(
    sid: int = Path(...),
    svc: StaffMealOrderingService = Depends(get_service)
):

    result = svc.delete(sid)

    return JSONResponse(content=result)


@router.get("/Staff_meal_ordering_query_guest_meal",
summary="查詢 客飯訂餐紀錄")
def get_guest_meal(
    year: str = Query(None),
    month: str = Query(None),
    day: str = Query(None),
    cardno: str = Query(None),
    code: str = Query(None),
    mtype: str = Query(None),
    ogname: str = Query(None),
    svc: StaffMealOrderingService = Depends(get_service)
):

    result = svc.fetch_guest_meal(
        year, month, day, cardno, code, mtype, ogname
    )

    return JSONResponse(content=result)

@router.post(
"/Staff_meal_ordering_query_guest_meal",
summary="新增客飯餐點紀錄"
)
def create_guest_meal(
    payload: GuestMealOrderingModel,
    svc: StaffMealOrderingService = Depends(get_service)
):

    result = svc.create_guest_meal(payload)

    return JSONResponse(content=result)

@router.delete(
"/Staff_meal_ordering_query_guest_meal/{sn}",
summary="刪除客飯餐點紀錄"
)
def delete_guest_meal(
    sn: int = Path(...),
    svc: StaffMealOrderingService = Depends(get_service)
):

    result = svc.delete_guest_meal(sn)

    return JSONResponse(content=result)

@router.get(
    "/Staff_meal_ordering_query_department",
    summary="查詢部門資訊",
    response_model=DepartmentResponseModel
)
def get_department(
    emp_id_hr: str = Query(..., description="員工 HR ID"),
    svc: StaffMealOrderingService = Depends(get_service)
):
    result = svc.fetch_department(emp_id_hr)
    return JSONResponse(content=result)


# In[ ]:




