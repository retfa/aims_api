#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Literal
import logging

<<<<<<< HEAD
from schemas.wintriss import FtaResponseLength
from dependencies.auth import get_current_user
from services.wintriss import WintrissService
from fta_response import FtaResult
=======
from app.schemas.wintriss import FtaResponseLength
from app.dependencies.auth import get_current_user
from app.services.wintriss import WintrissService
from app.fta_response import FtaResult
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

router = APIRouter(
    prefix="/wintriss",
    tags=["WinTriss"]
)

logger = logging.getLogger("MES_API")

@router.get("/length_realtime", response_model=FtaResponseLength,
    summary=" ")
def get_defect(
    MachineName: str = Query(..., description="機台名稱", example="20"),
    ExportFormat: str = Query(None,description="輸出類別// json(default), tablejson"),
    user=Depends(get_current_user)
):
    """
    查詢機台指定紙捲號碼的瑕疵
    
輸出 data.Content

```json
[
    {
        "length": int,
    }
]
    """
    try:
        # 組成 dict 傳給 Service（不要用 SimpleNamespace）
        data  = {
            "MachineName": MachineName,
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }
        
        logger.info(f"Get Wintriss length_realtime for user {user['FTAId']}")

        content, execution_time = WintrissService.get_length_realtime(data)
        
        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()

    except Exception as e:
        logger.exception(f"get_defect failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()

