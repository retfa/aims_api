#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Body, Request, Response, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from services.permission_service import PermissionService
from schemas.permission_schema import PermissionQuery, FtaResponsePermission, PermissionCopyQuery
from Model.jwt_manager import JwtManager

router = APIRouter(
    prefix="/permission",
    tags=["permission"]
)

service = PermissionService()


@router.get("/", response_model=FtaResponsePermission)
def get_permission(data: PermissionQuery = Depends()):
    return service.get_permission(data)

@router.get("/current")
def get_current_permission(
    request: Request, 
    response: Response, 
    up_function: Optional[str] = Query(None),
    function: Optional[str] = Query(None),
    progm_id: Optional[str] = Query(None)
):
    """
    取得當前使用者權限，JWT 從 cookie 讀取
    """
    try:
        # 從 cookie 讀取 JWT 並解析
        jwt_manager = JwtManager()
        payload = jwt_manager.decode_jwt_from_cookie(request)
        user_id = payload.get("FTAId")
        if not user_id:
            return JSONResponse({"message": "JWT missing FTAId"}, status_code=401)
        
        # 建立查詢物件
        data = PermissionQuery(
            function=function,
            up_function=up_function,
            progm_id=progm_id
        )        

        # 呼叫 service 取得權限資料
        permission_data: FtaResponsePermission = service.get_current_permission(user_id, data)
        return permission_data  # 直接回傳 Pydantic model

    except Exception as e:
        # 解析或 service 發生錯誤
        msg = f"get_current_permission |An error occurred: {str(e)}"
        return {"message": msg}

@router.get("/{user_id}", response_model=FtaResponsePermission)
def get_user_permission(
    user_id: str,
    up_function: Optional[str] = None
):
    return service.get_user_permission(user_id, up_function)

@router.put("/copy/{user_id}", response_model=FtaResponsePermission)
def copy_permission(user_id: str, data: PermissionCopyQuery = Body(...)):
    return service.copy_permission(user_id, data)

@router.put("/{user_id}", response_model=FtaResponsePermission)
def edit_permission(
    user_id: str, 
    data: dict = Body(
        ...,
        example={
              "user_id": "string",
              "up_function": "string",
              "Content": [
                {
                  "Havepermission": "string",
                  "sid": 0,
                  "user_id": "string",
                  "mname": "string",
                  "progm_id": "string",
                  "up_code": "string",
                  "f_code": "string",
                  "st_func": "string",
                  "sp_func": "string",
                  "func_print": "string",
                  "func_edit": "string",
                  "func_sign": "string",
                  "func_detail": "string",
                  "func_download": "string",
                  "func_other": "string"
                }
              ]
            }
    )
):
    return service.edit_permission(user_id, data)

# 單筆刪除
@router.delete("/{user_id}/{function}/{machine}", response_model=FtaResponsePermission)
def delete_permission(user_id: str, function: str, machine: str):
    datum = {"user_id": user_id, "function": function, "machine": machine if machine != "empty" else ""}
    return service.delete_permission(datum)

# 批次刪除
@router.delete("/", response_model=FtaResponsePermission)
def delete_permission_bulk(
    data_list: List[dict] = Body(
        ...,
        example=[  # 🔹 這個就是 Swagger 會顯示的 Example Value
            {
              "user_id": "A5558",
              "function": "H0124251303",
              "machine": ""
            }
        ]    
    )
):
    for datum in data_list:
        if "machine" not in datum or datum["machine"] is None:
            datum["machine"] = ""
    return service.delete_permission_bulk(data_list)

