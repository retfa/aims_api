#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import jwt
import json
from pathlib import Path
from jwt import ExpiredSignatureError, InvalidTokenError

# 讀取 security.json
security_file = Path(__file__).parent / "security.json"
with open(security_file, "r") as f:
    security_data = json.load(f)
    SECRET_KEY = security_data["Jwt"]["Key"]
    ISSUER = security_data["Jwt"]["Issuer"]
    AUDIENCE = security_data["Jwt"].get("Audience", ISSUER)

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

