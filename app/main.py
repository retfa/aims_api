#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys

from anyio.lowlevel import RunVar
from anyio import CapacityLimiter

from pathlib import Path
import logging
import time

# ==============================
# 專案根目錄 / app 資料夾
# ==============================
if getattr(sys, "frozen", False):
    # exe 執行時，app 解壓在 _MEIPASS/app
    BASE_DIR = Path(sys._MEIPASS) / "app"
else:
    # 開發環境，專案根目錄 / app
    BASE_DIR = Path(__file__).resolve().parent.parent / "app"

# 把 app 目錄加到 sys.path
sys.path.insert(0, str(BASE_DIR))

# ==============================
# Import FastAPI
# ==============================
from fastapi import FastAPI, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

# ==============================
# Import core 模組
# ==============================
from core.config import settings
from core.app_logging import init_logging

# ==============================
# 初始化 logging
# ==============================
log_path = Path(sys._MEIPASS).parent / "logs" / "app.log" if getattr(sys, "frozen", False) else BASE_DIR.parent / "logs" / "app.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
init_logging(log_path)
logger = logging.getLogger("MES_API")

# ==============================
# Import routers
# ==============================
from routers import (
    healthcheck, business_intelligence, business_intelligence_history,
    consumption, department, dining, machine, menu, menutree, user_router,
    permission_cross_department, program, paper_quality_standard,
    skyeye, wintriss, aug
)
from routers import authentication, system_router

from routers import (
    gz_data_router, gz_data_feature_importance_router, gz_data_gramg_speed_router, gz_data_machine_run_router,
    gz_data_outputlist_router, gz_data_out_spec_count_router, gz_data_out_spec_count_reel_router,
    gz_data_user_favorite_router, gz_data_diff_data_router, gz_data_diff_data_feature_importance_router,
    gz_data_prediction_status_router
)

from routers import mes_router, costsheet_router, coatingweight_router
from routers import staff_meal_ordering_router
from routers import outputlist_router
from routers import permission_router

from routers import redis_router

# ==============================
# Import service
# ==============================
from services.gz_data_service import GZDataService
from services.gz_data_feature_importance_service import GZDataFeatureImportanceService
from services.gz_data_gramg_speed_service import GZDataGramgSpeedService
from services.gz_data_machine_run_service import GZDataMachineRunService
from services.gz_data_outputlist_service import GZDataOutputlistService
from services.gz_data_out_spec_count_service import GZDataOutSpecCountService
from services.gz_data_out_spec_count_reel_service import GZDataOutSpecCountReelService
from services.gz_data_user_favorite_service import GZDataUserFavoriteService
from services.gz_data_diff_data_service import GZDataDiffDataService
from services.gz_data_diff_data_feature_importance_service import GZDataDiffDataFeatureImportanceService
from services.gz_data_prediction_status_service import GZDataPredictionStatusService

from services.mes_service import MESService
from services.costsheet_service import CostSheetService
from services.coatingweight_service import CoatingWeightService

from services.staff_meal_ordering_service import StaffMealOrderingService

from services.outputlist_service import OutputListService

from services.system_service import SystemService

from services.redis_service import RedisService

# ==============================
# Import utils
# ==============================
from utils.server_manager import load_servers

# ==============================
# Import redis
# ==============================
import redis

from starlette.middleware.base import BaseHTTPMiddleware

def create_app() -> FastAPI:
    servers = load_servers()   

    # ✅ 建立 connection pool（不會真的連線）
    redis_pool = redis.ConnectionPool(
        host="srvmsdba1",
        port=6379,
        db=0,
        socket_connect_timeout=5,
        socket_timeout=5,
        max_connections=20,        # 每個 worker 最多 20 條
        decode_responses=True
    )

    # ✅ Redis client（lazy，不會在這裡連線）
    redis_client = redis.Redis(connection_pool=redis_pool)
    
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
"""  
    )
    
    # --- Logging Middleware ---
    class LoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            client = request.client.host if request.client else "unknown"
            duration = time.time() - start_time
            logger.info(f"{client} - {request.method} {request.url.path} "
                        f"({response.status_code}) took {duration:.3f}s")
            return response

    # --- 加入 Logging Middleware ---
    app.add_middleware(LoggingMiddleware)

    # 設定 CORS
    origins = [
        "http://ftapa202000108a.yfy.corp:4200",
        "http://ftapa202000108a:4200",
        "http://10.10.2.158:4200",
        "http://FTAPB202401622A.yfy.corp:4200",
        "http://FTAPB202401622A:4200",
        "http://10.10.2.155:4200",
        # === Jason Ouyang 開發環境 ===
        "http://FTAPA202202918A.yfy.corp:4200",
        "http://FTAPA202202918A:4200",
        "http://10.10.2.154:4200",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # 允許的前端來源
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )    

    # 放這裡，會讓 Swagger UI 出現右上角 Authorize
    bearer_scheme = HTTPBearer()
    
    # 初始化Redis
    redis_router.service = RedisService(redis_client=redis_client)
    app.include_router(redis_router.router)
    
    # 功能 Router
# ----舊FLASK API ----
#     app.include_router(aug.router)
    app.include_router(authentication.router)
#     app.include_router(business_intelligence.router)
#     app.include_router(business_intelligence_history.router)
#     app.include_router(consumption.router)
#     app.include_router(healthcheck.router)    
#     app.include_router(department.router)
#     app.include_router(dining.router)    
#     app.include_router(machine.router)
    app.include_router(menu.router)
#     app.include_router(menutree.router)    
#     app.include_router(paper_quality_standard.router)
    app.include_router(permission_router.router)
    app.include_router(permission_cross_department.router)  
#     app.include_router(program.router)
    app.include_router(skyeye.router)    
    app.include_router(user_router.router)
    app.include_router(wintriss.router)    

# ---- 舊FAST API ----
    gz_data_router.service = GZDataService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_router.router)
    
    gz_data_feature_importance_router.service = GZDataFeatureImportanceService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_feature_importance_router.router)
    
    gz_data_gramg_speed_router.service = GZDataGramgSpeedService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_gramg_speed_router.router)  
    
    gz_data_machine_run_router.service = GZDataMachineRunService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_machine_run_router.router)   
    
    gz_data_outputlist_router.service = GZDataOutputlistService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_outputlist_router.router)   
    
    gz_data_out_spec_count_router.service = GZDataOutSpecCountService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_out_spec_count_router.router) 
    
    gz_data_out_spec_count_reel_router.service = GZDataOutSpecCountReelService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_out_spec_count_reel_router.router)
    
    gz_data_user_favorite_router.service = GZDataUserFavoriteService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_user_favorite_router.router)   
    
    gz_data_diff_data_router.service = GZDataDiffDataService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_diff_data_router.router)
    
    gz_data_diff_data_feature_importance_router.service = GZDataDiffDataFeatureImportanceService(
        servers=servers,
        redis_client=redis_client
    )
    app.include_router(gz_data_diff_data_feature_importance_router.router)
    
    gz_data_prediction_status_router.service = GZDataPredictionStatusService(servers=servers,redis_client=redis_client)
    app.include_router(gz_data_prediction_status_router.router)
    
    #---MES---
    mes_router.service = MESService(servers=servers,redis_client=redis_client)
    app.include_router(mes_router.router)
    
    costsheet_router.service = CostSheetService(servers=servers,redis_client=redis_client)
    app.include_router(costsheet_router.router)
    
    coatingweight_router.service = CoatingWeightService(servers=servers,redis_client=redis_client)
    app.include_router(coatingweight_router.router)
    
    staff_meal_ordering_router.service = StaffMealOrderingService(servers=servers,redis_client=redis_client)
    app.include_router(staff_meal_ordering_router.router)
    
    outputlist_router.service = OutputListService(servers=servers,redis_client=redis_client)
    app.include_router(outputlist_router.router)
    
    # system
    system_router.service = SystemService(servers=servers)
    app.include_router(system_router.router)
    
    # --- 加大同步執行緒池的限制 ---
    @app.on_event("startup")
    async def startup_event():
        # 將預設的 40 個 Thread 增加到 100 個
        RunVar("_default_thread_limiter").set(CapacityLimiter(100))
        logger.info("FastAPI startup: Thread pool limit set to 100")    

    logger.info("FastAPI app created")  # 啟動時記錄

    return app

app = create_app()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    import uvicorn
    # 這裡建議 workers 設為 2~4 (視伺服器 CPU 核心數而定)
    # 注意：在 Windows 下使用多 workers，傳入的必須是字串 "main:app"    
    uvicorn.run(
        "main:app",  # 改用字串形式，這對多 workers 是必須的     
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level="info",
        reload=False,         # 打包後不要 reload
        workers=2,    # 開啟 2 個平行視窗處理請求
        # 增加這兩個參數
        timeout_keep_alive=35,
        timeout_graceful_shutdown=60,  # 增加關閉/重啟時的緩衝時間
        limit_concurrency=200, # 限制總併發數，避免 9 個 Worker 把 SQL 連線池撐爆 
        backlog=2048           # 增加等待隊列，防止高併發時連線被拒絕        
    )


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

