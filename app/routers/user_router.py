#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Request, Body, Query
from typing import Optional
import logging

from services.user_service import UserService
from schemas.user_schema import (
    UserQuery,
    FtaResponseUser,
    FtaResponseEmploee,
    UserEdit,
    UserAdd,
    UserPasswordEdit,
    UserStatusEdit
)
from Model.jwt_manager import JwtManager

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

logger = logging.getLogger("MES_API")

service = UserService()


# ✅ 查詢 user
@router.get("/", response_model=FtaResponseUser)
def get_users(data: UserQuery = Depends()):
    return service.get_users(data)

# ✅ 新增 user
@router.post("/", response_model=FtaResponseUser)
def add_user(
    request: Request,
    data: UserAdd = Body(...)
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)

    return service.add_user(data, payload)
# =================== HR ===================

# ✅ HR 查詢使用者列表
@router.get("/hr", response_model=FtaResponseEmploee)
def hr_browse(
    request: Request,
    user_id: Optional[str] = Query(None),
    user_id_hris: Optional[str] = Query(None),
    user_name: Optional[str] = Query(None),
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)

    data = UserQuery(
        user_id=user_id,
        user_id_hris=user_id_hris,
        user_name=user_name
    )
    

# ✅ HR 修改資料
@router.patch("/hr/{idhris}", response_model=FtaResponseEmploee)
def hr_edit(
    idhris: str,
    request: Request,
    data: UserEdit = Body(...)
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)
    return service.hr_edit(idhris, data, payload)
    
    
    return service.hr_browse(data)

# ✅ HR 查詢單一使用者
@router.get("/hr/{idhris}", response_model=FtaResponseUser)
def hr_read(
    idhris: str,
    request: Request
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)
    return service.hr_read(idhris)



# ✅ HR 新增資料
@router.post("/hr/{idhris}", response_model=FtaResponseEmploee)
def hr_add(
    idhris: str,
    request: Request,
    data: UserAdd = Body(...)
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)
    return service.hr_add(idhris, data, payload)


# ✅ HR AD6 查詢使用者
@router.get("/hrad6/{id}", response_model=FtaResponseUser)
def hr_ad6_read(
    id: str,
    request: Request
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)
    return service.srvad6_hr_read(id)


# ✅ 修改密碼
@router.patch("/password/{user_id}", response_model=FtaResponseUser)
def edit_password(
    user_id: str,
    request: Request,
    data: UserPasswordEdit = Body(...)
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)

    return service.edit_password(user_id, data, payload)


# ✅ 啟停用
@router.patch("/status/{user_id}", response_model=FtaResponseUser)
def edit_status(
    user_id: str,
    request: Request,
    data: UserStatusEdit = Body(...)
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)

    return service.edit_status(user_id, data, payload)

# ✅ 查詢單一 user
@router.get("/{user_id}", response_model=FtaResponseUser)
def get_user(user_id: str):
    return service.get_user(user_id)


# ✅ 修改 user
@router.patch("/{user_id}", response_model=FtaResponseUser)
def edit_user(
    user_id: str,
    request: Request,
    data: UserEdit = Body(...)
):
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)

    return service.edit_user(user_id, data, payload)

