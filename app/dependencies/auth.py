#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
import jwt
import json
from app.core.security import decode_token

security = HTTPBearer()

def get_current_user():
    # 永遠回傳 demo
    return {"FTAId": "demo", "UserName": "demo"}

# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     用於路由依賴的 JWT 驗證
#     """
#     token = credentials.credentials
#     try:
#         payload = decode_token(token)
#         return payload
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="JWT expired")
#     except jwt.InvalidTokenError as e:
#         raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT: {str(e)}")

