#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Response, Cookie, Request, Depends
from fastapi.responses import JSONResponse
from schemas.authentication_login import LoginModel
from services.authentication_login import authenticate_user, generate_jwt, decode_jwt_from_cookie
from Model.jwt_manager import JwtManager
from fastapi import HTTPException, status
import json
from typing import Optional

router = APIRouter(prefix="/authentication", tags=["authentication"])

# ------------------------------
# POST /authenticate
# ------------------------------
@router.post("/authenticate")
def authenticate(login: LoginModel, response: Response):
    """
    Accept Post to log user in.
    """
    user = authenticate_user(login.acc, login.pwd)
    jwt_token = generate_jwt(user)
    response.set_cookie("jwt", jwt_token, httponly=True)
    response.headers["Authorization"] = f"Bearer {jwt_token}"
    return {"jwt": jwt_token}

# ------------------------------
# GET /whoami
# ------------------------------
@router.get("/whoami")
def whoami(request: Request, response: Response):
    """
    Get login user data
    """    
    jwt_manager = JwtManager()
    payload = jwt_manager.decode_jwt_from_cookie(request)
    response_data = {
        "FTAId": payload.get("FTAId"),
        "YFYId": payload.get("YFYId"),
        "Name": payload.get("Name"),
    }
    return JSONResponse(content=response_data)

# ------------------------------
# POST /refreshtoken & /revokerefreshtoken
# ------------------------------
# @router.post("/refreshtoken")
# def refreshtoken():
#     return {"message": "Not implemented yet"}

# @router.post("/revokerefreshtoken")
# def revokerefreshtoken():
#     return {"message": "Not implemented yet"}

