#!/usr/bin/env python
# coding: utf-8

<<<<<<< HEAD
# In[1]:


from fastapi import APIRouter, Depends, HTTPException
import logging

from schemas.menu import MenuRequest
from services.menu import MenuService
from core.security import verify_jwt  # <-- 直接用 dependency

from fta_response import FtaResult

router = APIRouter(
    prefix="/menu",
    tags=["menu"]
#     dependencies=[Depends(verify_jwt)]
)


@router.get("")
def get_menu(Node: str, jwt_payload=Depends(verify_jwt)):
    """
    取得 Menu 詳細資料
    """
    url = f'GET /menu?Node={Node}'
    logging.info(url)

    data = {"Node": Node, "jwt": jwt_payload}

    try:
        content, execution_time = MenuService.get_menu(data)
        return FtaResult(content, execution_time, True, export_format="json").to_dict()

    except Exception as e:
        msg = f'MenuRouter | An error occurred: {str(e)}'
        logging.debug(msg)
        raise HTTPException(status_code=500, detail=msg)


# In[ ]:



=======
# In[ ]:


from fastapi import APIRouter
import logging

router = APIRouter(
    prefix="/menu",
    tags=["Menu"]
)

logger = logging.getLogger("MES_API")

@router.get("/")
def health():
    logger.info("healthcheck API called")
    return {
        "status": "Healthy",
        "version": "1.0.0",
        "details": None
    }
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

