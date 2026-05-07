#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends, Body
from fastapi.responses import JSONResponse
from services.gz_data_user_favorite_service import GZDataUserFavoriteService
from typing import List

router = APIRouter(
    prefix="",
    tags=["GreenZone"]
)

service: GZDataUserFavoriteService = None

def get_service() -> GZDataUserFavoriteService:
    if service is None:
        raise RuntimeError("GZDataUserFavoriteService not initialized")
    return service

# GET 查詢我的最愛
@router.get(
    "/GET_GZ_data_user_favorite",
    summary="查詢 GreenZone 的我的最愛訊號",
    description="透過條件查詢 GreenZone 的我的最愛訊號"
)
def get_gz_data_user_favorite(
    Isfavorite: str = Query(None, alias="Isfavorite", description="是否查詢最愛參數，格式 1、0、NULL"),
    MachineName: str = Query(None, alias="MachineName", description="格式 18、19、20、21"),
    svc: GZDataUserFavoriteService = Depends(get_service)
):
    result = svc.get_user_favorite(Isfavorite, MachineName)
    return JSONResponse(content=result)

# POST (提醒使用 GET)
@router.post("/GET_GZ_data_user_favorite")
def post_gz_data_user_favorite():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

# PUT 更新我的最愛
@router.put(
    "/GET_GZ_data_user_favorite",
    summary="更新 GreenZone 我的最愛清單",
    description="一次覆寫 favoritesensor 的所有資料，Request Body 需為字串陣列，例如 ['ACDRY-DCS_A103', 'ACDRY-DCS_A102']"
)
def put_gz_data_user_favorite(
    favorite_list: List[str] = Body(...),
    svc: GZDataUserFavoriteService = Depends(get_service)
):
    try:
        result = svc.update_user_favorite(favorite_list)
    except RuntimeError as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)
    return JSONResponse(content=result)

