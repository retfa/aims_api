#!/usr/bin/env python
# coding: utf-8

# In[6]:


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.core.config import settings
from app.core.app_logging import init_logging
import logging
from pathlib import Path

# 初始化 logging（只做一次）
BASE_DIR = Path(__file__).resolve().parent
log_path = BASE_DIR / "core" / "app.log"
init_logging(log_path)

logger = logging.getLogger("MES_API")

from app.routers import (
    healthcheck, login, business_intelligence, business_intelligence_history,
    consumption, department, dining, machine, menu, menutree, user,
    permission, permission_cross_department, program, paper_quality_standard,
    skyeye, wintriss, aug,
    system, auth
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="MES API",
        version="1.0.0",
        description="""
本區提供 RESTful Web API，使用者可採用 HTTP 方法，取得資料，並以通用 JSON 格式作為回傳結果。

輸出<br>
{<br>
"data": 回傳資料,<br>
"success": "API執行結果",<br>
"status_code": "HTTP status 狀態碼"<br>
}<br>

輸出 data

```json
{
    "Action": API動作,
    "Content": 結果集,
    "ExecutionTime": 執行耗時,
    "ExecutionDto": 執行時間,
    "Length": Content筆數,
}
""",        
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 放這裡，會讓 Swagger UI 出現右上角 Authorize
    bearer_scheme = HTTPBearer()    
    
    # 系統相關 Router
    app.include_router(system.router, prefix="/system", tags=["System"])
    
    # 功能 Router
# ----舊FLASK API ----
    app.include_router(healthcheck.router)
    app.include_router(login.router)
    app.include_router(business_intelligence.router)
    app.include_router(business_intelligence_history.router)
    app.include_router(consumption.router)
    app.include_router(department.router)
    app.include_router(dining.router)
    app.include_router(machine.router)
    app.include_router(menu.router)
    app.include_router(menutree.router)
    app.include_router(user.router)
    app.include_router(permission.router)
    app.include_router(permission_cross_department.router)
    app.include_router(program.router)
    app.include_router(paper_quality_standard.router)
    app.include_router(skyeye.router)
    app.include_router(wintriss.router)
    app.include_router(aug.router)
    
#     app.include_router(auth.router)

# ---- 舊FAST API ----


    logger.info("FastAPI app created")  # 啟動時記錄

    return app

app = create_app()


# In[ ]:


# Swagger UI

# http://127.0.0.1:8000/docs
# http://10.10.2.154:50000/docs


# In[ ]:


# Redis
# https://www.youtube.com/watch?v=6nY-kci1rlo

# cd C:\Users\Jason.Ouyang\Downloads\OuYang\Python\20250204_PM21_GreenZone
# uvicorn app.main:app --host 10.10.2.154 --port 50000

# uvicorn app.main:app --reload --host 10.10.2.154 --port 50000

