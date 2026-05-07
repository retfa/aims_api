#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from services.redis_service import RedisService
from typing import List, Optional

router = APIRouter(prefix="/redis", tags=["Redis"])

service: RedisService = None  # 會由 main.py 注入

def get_service():
    if service is None:
        raise RuntimeError("RedisService not initialized")
    return service

@router.get("/keys", summary="搜尋 Redis Keys", description="根據關鍵字搜尋 Redis keys；若未提供 keywords，則回傳全部 keys")
def get_redis_keys(
    keywords: Optional[List[str]] = Query(
        default=None,
        description="搜尋的關鍵字 list，不填則搜尋全部"
    ),
    limit: int = Query(
        1000,
        description="最多返回筆數（避免撈取過多資料）"
    ),
    svc: RedisService = Depends(get_service)
):
    """
    使用 SCAN 指令搜尋符合關鍵字的 Redis keys，並回傳 TTL。
    """
    keys = svc.scan_keys(keywords, limit)
    return JSONResponse(content={"count": len(keys), "keys": keys})

@router.get("/get", summary="取得 Redis Key 的值", description="取得指定 key 的資料，並支援限制顯示筆數")
def redis_get(
    key: str = Query(..., description="要取得的 Redis key"),
    limit: int = Query(100, description="限制返回資料筆數"),
    svc: RedisService = Depends(get_service)
):
    result = svc.get_key(key, limit)
    return JSONResponse(content=result)

# -----------------------
# 刪除功能
# -----------------------

# 1️⃣ 單筆刪除
@router.delete("/key", summary="刪除單筆 Redis Key", description="刪除指定的 Redis key，只能刪除一個 key")
def delete_redis_key(
    key: str = Query(..., description="要刪除的 Redis key"),
    svc: RedisService = Depends(get_service)
):
    result = svc.delete_key(key)
    return JSONResponse(content=result)

# 2️⃣ 多筆刪除
@router.delete("/keys", summary="刪除多筆 Redis Keys", description="刪除多個指定的 Redis keys，傳入 key list")
def delete_redis_keys(
    keys: list[str] = Query(..., description="要刪除的 Redis keys，支援多筆"),
    svc: RedisService = Depends(get_service)
):
    deleted_count = 0
    for k in keys:
        deleted_count += svc.delete_key(k).get("deleted", 0)
    return JSONResponse(content={"deleted": deleted_count, "keys": keys})

# 3️⃣ 模糊刪除
@router.delete("/clear", summary="模糊刪除 Redis Keys", description="刪除符合 pattern 的所有 Redis keys，例如 staff_meal_order*")
def clear_redis_keys(
    pattern: str = Query(..., description="匹配 Redis key 的 pattern，例如 staff_meal_order*"),
    svc: RedisService = Depends(get_service)
):
    keys_to_delete = [k["key"] for k in svc.scan_keys([pattern])]
    deleted_count = 0
    for k in keys_to_delete:
        deleted_count += svc.delete_key(k).get("deleted", 0)
    return JSONResponse(content={"deleted": deleted_count, "pattern": pattern, "keys_deleted": keys_to_delete})

# 4️⃣ 刪除全部
@router.delete("/all", summary="刪除全部 Redis Keys", description="清空 Redis 中的所有 key，請謹慎操作")
def delete_all_redis_keys(
    svc: RedisService = Depends(get_service)
):
    keys_to_delete = [k["key"] for k in svc.scan_keys(["*"])]
    deleted_count = 0
    for k in keys_to_delete:
        deleted_count += svc.delete_key(k).get("deleted", 0)
    return JSONResponse(content={"deleted": deleted_count, "keys_deleted": keys_to_delete})

