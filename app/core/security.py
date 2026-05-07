#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import jwt
import json
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError

# -----------------------------
# 讀取 security.json
# -----------------------------
security_file = Path(__file__).parent / "security.json"

with open(security_file, "r") as f:
    security_data = json.load(f)
    
SECRET_KEY = security_data["Jwt"]["Key"]
ISSUER = security_data["Jwt"]["Issuer"]
AUDIENCE = security_data["Jwt"].get("Audience", ISSUER)

# -----------------------------
# Swagger JWT Security
# -----------------------------
bearer_scheme = HTTPBearer()

# -----------------------------
# JWT Decode
# -----------------------------
def decode_token(token: str) -> dict:
    """
    解碼 JWT 並驗證 issuer/audience
    """
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=["HS256"],
        issuer=ISSUER,
        audience=AUDIENCE
    )

# -----------------------------
# FastAPI Dependency
# -----------------------------
def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """
    驗證 JWT Token
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

