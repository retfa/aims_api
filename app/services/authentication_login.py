#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import logging
from fastapi import HTTPException, status
from Model.jwt_manager import JwtManager
from Model.user import UserLogin, UserSignedIn  # <- 改成 Pydantic model
from BLL.auth import Authentication

def authenticate_user(acc: str, pwd: str):
    usr = UserLogin(login_id=acc, password=pwd)  # <- 直接用 Pydantic
    auth = Authentication(folders=None)  # 替換成你的設定來源
    user = auth.Auth(usr)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    return user

def generate_jwt(user):
    jwt_manager = JwtManager()
    jwt_token = jwt_manager.generate_jwt(user)
    logging.info(f"JWT generated: {jwt_token}")
    return jwt_token

def decode_jwt_from_cookie(jwt_token: str):
    if not jwt_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing JWT")
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(jwt_token)
    return payload

