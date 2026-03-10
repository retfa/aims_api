#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
import jwt
from app.core.security import SECRET_KEY, ISSUER, AUDIENCE
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/generate_test_jwt", summary="生成測試 JWT")
def generate_test_jwt(FTAId: str = Query("demo", description="測試用 FTAId")):
    """
    生成一個測試用 JWT Token，用於 Swagger 測試 API。
    """
    utcnow = datetime.utcnow()
    payload = {
        "FTAId": FTAId,
        "exp": utcnow + timedelta(hours=1),  # 1 小時後過期
        "iat": utcnow,
        "nbf": utcnow,
        "iss": ISSUER,
        "aud": AUDIENCE
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return JSONResponse({"token": token})

@router.get("/test_jwt")
def test_jwt(user=Depends(get_current_user)):
    return {"message": "JWT 驗證成功", "user": user}

