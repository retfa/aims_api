#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Body, Request, Response, Query
from fastapi.responses import JSONResponse
from typing import Optional

from schemas.permission_cross_department_schema import (
    PermissionCrossDepartmentQuery,
    PermissionCrossDepartmentEdit,
    FtaResponsePermissionCrossDepartment
)
from services.permission_cross_department_service import PermissionCrossDepartmentService
from Model.jwt_manager import JwtManager

router = APIRouter(
    prefix="/permissioncrossdepartment",
    tags=["permissioncrossdepartment"]
)

service = PermissionCrossDepartmentService()


@router.get("/", response_model=FtaResponsePermissionCrossDepartment)
def get_permission_cross_department(
    request: Request,
    response: Response,
    query: PermissionCrossDepartmentQuery = Depends()
):
    """
    查詢跨部門權限（需 JWT）
    """
    try:
        jwt_manager = JwtManager()
        payload = jwt_manager.decode_jwt_from_cookie(request)

        if not payload:
            return JSONResponse({"message": "JWT invalid"}, status_code=401)

        return service.browse(query)

    except Exception as e:
        msg = f"get_permission_cross_department |An error occurred: {str(e)}"
        return {"message": msg}


@router.get("/{user_id}", response_model=FtaResponsePermissionCrossDepartment)
def get_user_permission_cross_department(
    request: Request,
    response: Response,
    user_id: str,
    query: PermissionCrossDepartmentQuery = Depends()
):
    """
    查詢指定使用者跨部門權限（需 JWT）
    """
    try:
        jwt_manager = JwtManager()
        payload = jwt_manager.decode_jwt_from_cookie(request)

        if not payload:
            return JSONResponse({"message": "JWT invalid"}, status_code=401)

        return service.read(user_id, query)

    except Exception as e:
        msg = f"get_user_permission_cross_department |An error occurred: {str(e)}"
        return {"message": msg}


@router.put("/{user_id}", response_model=FtaResponsePermissionCrossDepartment)
def edit_user_permission_cross_department(
    request: Request,
    response: Response,
    user_id: str,
    data: PermissionCrossDepartmentEdit = Body(
        ...,
        example={
              "progm_id": "string",
              "departments": "string"
            }
        )
):
    """
    編輯跨部門權限（需 JWT）
    """
    try:
        jwt_manager = JwtManager()
        payload = jwt_manager.decode_jwt_from_cookie(request)

        current_user_id = payload.get("FTAId")
        if not current_user_id:
            return FtaResponsePermissionCrossDepartment(
                data=PermissionCrossDepartmentResponse(
                    Action="AUTH_ERROR",
                    Content=[],
                    ExecutionTime="0 ms",
                    ExecutionDto="",
                    Length=0
                ),
                status_code=401,
                success=False
            )

        return service.edit(user_id, data, current_user_id)

    except Exception as e:
        return FtaResponsePermissionCrossDepartment(
            data=PermissionCrossDepartmentResponse(
                Action="ERROR",
                Content=[],
                ExecutionTime="0 ms",
                ExecutionDto="",
                Length=0
            ),
            status_code=500,
            success=False
        )

