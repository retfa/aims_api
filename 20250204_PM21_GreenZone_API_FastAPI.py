#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import timedelta
import pytz

from fastapi import FastAPI, Query, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio, sys
import nest_asyncio
from starlette.middleware.base import BaseHTTPMiddleware

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pyodbc

import requests
import json
import traceback

import re
from collections import defaultdict

from urllib.parse import quote_plus as urlquote

import warnings
warnings.filterwarnings("ignore")

from dateutil.relativedelta import relativedelta

from typing import List,Optional
from pydantic import BaseModel, Field


# In[2]:


import logging
from logging.handlers import TimedRotatingFileHandler

try:
    log_filename = r'E:\AP\Api\dist\20250204_PM21_GreenZone_API_FastAPI.log'
    handler = TimedRotatingFileHandler(log_filename, when='midnight', backupCount=7)
except:
    log_filename = r'C:\Users\Jason.Ouyang\Downloads\OuYang\Python\20250204_PM21_GreenZone\fast_api.log'
    handler = TimedRotatingFileHandler(log_filename, when='midnight', backupCount=7)

handler.suffix = '%Y-%m-%d.log'
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


# In[3]:


try:
    df_SERVER_GZ = pd.DataFrame([['10.10.24.192','AIUPS']], columns=['SERVER', 'DB'])

    df_SERVER_GZ['create_engine'] = ''
    df_SERVER_GZ['cnx'] = ''

    df_SERVER_GZ['create_engine'][0] = create_engine('postgresql+psycopg2://Aiups_OnlineDB:Aiups_OnlineDB@10.10.24.192:5432/Aiups_OnlineDB',
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
    df_SERVER_GZ['cnx'][0] = df_SERVER_GZ['create_engine'][0].connect()
except:
    df_SERVER_GZ = pd.DataFrame([['10.10.24.192','AIUPS']], columns=['SERVER', 'DB'])

    df_SERVER_GZ['create_engine'] = ''
    df_SERVER_GZ['cnx'] = ''

df_SERVER_SRVMSDBA2 = pd.DataFrame([['10.10.2.50','GREENZONE']], columns=['SERVER', 'DB'])

df_SERVER_SRVMSDBA2['create_engine'] = ''
df_SERVER_SRVMSDBA2['cnx'] = ''

df_SERVER_SRVMSDBA2['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2022") + df_SERVER_SRVMSDBA2['SERVER'][0] + '/' + df_SERVER_SRVMSDBA2['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVMSDBA2['cnx'][0] = df_SERVER_SRVMSDBA2['create_engine'][0].connect() 

df_SERVER_YFYAIUPSVISA1 = pd.DataFrame([['10.10.24.153','AIUPS_CDB']], columns=['SERVER', 'DB'])

df_SERVER_YFYAIUPSVISA1['create_engine'] = ''
df_SERVER_YFYAIUPSVISA1['cnx'] = ''

df_SERVER_YFYAIUPSVISA1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2024") + df_SERVER_YFYAIUPSVISA1['SERVER'][0] + '/' + df_SERVER_YFYAIUPSVISA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    isolation_level="READ UNCOMMITTED",  # ← 一行設定全域生效
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_YFYAIUPSVISA1['cnx'][0] = df_SERVER_YFYAIUPSVISA1['create_engine'][0].connect() 

df_SERVER_SRVAIUPSPRA1 = pd.DataFrame([['SRVAIUPSPRA1','AIUPS']], columns=['SERVER', 'DB'])

df_SERVER_SRVAIUPSPRA1['create_engine'] = ''
df_SERVER_SRVAIUPSPRA1['cnx'] = ''

df_SERVER_SRVAIUPSPRA1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2024") + df_SERVER_SRVAIUPSPRA1['SERVER'][0] + '/' + df_SERVER_SRVAIUPSPRA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVAIUPSPRA1['cnx'][0] = df_SERVER_SRVAIUPSPRA1['create_engine'][0].connect() 

df_SERVER_SRVMSDBA1 = pd.DataFrame([['SRVMSDBA1','AIMSFTAO']], columns=['SERVER', 'DB'])

df_SERVER_SRVMSDBA1['create_engine'] = ''
df_SERVER_SRVMSDBA1['cnx'] = ''

df_SERVER_SRVMSDBA1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk@") + df_SERVER_SRVMSDBA1['SERVER'][0] + '/' + df_SERVER_SRVMSDBA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVMSDBA1['cnx'][0] = df_SERVER_SRVMSDBA1['create_engine'][0].connect() 

df_SERVER_SRVAD1 = pd.DataFrame([['SRVAD1','AMIS']], columns=['SERVER', 'DB'])

df_SERVER_SRVAD1['create_engine'] = ''
df_SERVER_SRVAD1['cnx'] = ''

df_SERVER_SRVAD1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk") + df_SERVER_SRVAD1['SERVER'][0] + '/' + df_SERVER_SRVAD1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVAD1['cnx'][0] = df_SERVER_SRVAD1['create_engine'][0].connect() 

df_SERVER_CHPGTERPDBAAR01 = pd.DataFrame([['CHPGTERPDBAAR01','YFYPRODERP_FTA']], columns=['SERVER', 'DB'])

df_SERVER_CHPGTERPDBAAR01['create_engine'] = ''
df_SERVER_CHPGTERPDBAAR01['cnx'] = ''

df_SERVER_CHPGTERPDBAAR01['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk") + df_SERVER_CHPGTERPDBAAR01['SERVER'][0] + '/' + df_SERVER_CHPGTERPDBAAR01['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_CHPGTERPDBAAR01['cnx'][0] = df_SERVER_CHPGTERPDBAAR01['create_engine'][0].connect() 

df_SERVER_SRVMESDBA1 = pd.DataFrame([['SRVMESDBA1','AMIS']], columns=['SERVER', 'DB'])

df_SERVER_SRVMESDBA1['create_engine'] = ''
df_SERVER_SRVMESDBA1['cnx'] = ''

df_SERVER_SRVMESDBA1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2023") + df_SERVER_SRVMESDBA1['SERVER'][0] + '/' + df_SERVER_SRVMESDBA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVMESDBA1['cnx'][0] = df_SERVER_SRVMESDBA1['create_engine'][0].connect() 

df_SERVER_SRVAD2 = pd.DataFrame([['SRVAD2','AMIS']], columns=['SERVER', 'DB'])

df_SERVER_SRVAD2['create_engine'] = ''
df_SERVER_SRVAD2['cnx'] = ''

df_SERVER_SRVAD2['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk") + df_SERVER_SRVAD2['SERVER'][0] + '/' + df_SERVER_SRVAD2['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVAD2['cnx'][0] = df_SERVER_SRVAD2['create_engine'][0].connect() 

df_SERVER_YFYAIDBA3 = pd.DataFrame([['YFYAIDBA3','AI']], columns=['SERVER', 'DB'])

df_SERVER_YFYAIDBA3['create_engine'] = ''
df_SERVER_YFYAIDBA3['cnx'] = ''

df_SERVER_YFYAIDBA3['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2022") + df_SERVER_YFYAIDBA3['SERVER'][0] + '/' + df_SERVER_YFYAIDBA3['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_YFYAIDBA3['cnx'][0] = df_SERVER_YFYAIDBA3['create_engine'][0].connect() 

df_SERVER_SRVADA1 = pd.DataFrame([['SRVADA1','ERP-A']], columns=['SERVER', 'DB'])

df_SERVER_SRVADA1['create_engine'] = ''
df_SERVER_SRVADA1['cnx'] = ''

df_SERVER_SRVADA1['create_engine'][0] = create_engine('mssql+pyodbc://pd_user:%s@' % urlquote("ayfyuserpd") + df_SERVER_SRVADA1['SERVER'][0] + '/' + df_SERVER_SRVADA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVADA1['cnx'][0] = df_SERVER_SRVADA1['create_engine'][0].connect() 

df_SERVER_SRVAD6 = pd.DataFrame([['SRVAD6','HR']], columns=['SERVER', 'DB'])

df_SERVER_SRVAD6['create_engine'] = ''
df_SERVER_SRVAD6['cnx'] = ''

df_SERVER_SRVAD6['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk") + df_SERVER_SRVAD6['SERVER'][0] + '/' + df_SERVER_SRVAD6['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
                                                    pool_pre_ping=True,
                                                    pool_recycle=1800,  # 避免 MySQL idle 超時
                                                    pool_size=5,  # 視應用情境而定
                                                    max_overflow=10)
df_SERVER_SRVAD6['cnx'][0] = df_SERVER_SRVAD6['create_engine'][0].connect() 


# In[4]:


servers = {
    "GZ": df_SERVER_GZ,
    "SRVMSDBA2": df_SERVER_SRVMSDBA2,
    "YFYAIUPSVISA1": df_SERVER_YFYAIUPSVISA1,
    "SRVAIUPSPRA1": df_SERVER_SRVAIUPSPRA1,
    "SRVMSDBA1": df_SERVER_SRVMSDBA1,
    "SRVAD1": df_SERVER_SRVAD1,
    "CHPGTERPDBAAR01": df_SERVER_CHPGTERPDBAAR01,
    "SRVMESDBA1": df_SERVER_SRVMESDBA1,
    "SRVAD2": df_SERVER_SRVAD2,
    "YFYAIDBA3": df_SERVER_YFYAIDBA3,
    "SRVADA1": df_SERVER_SRVADA1,
    "SRVAD6": df_SERVER_SRVAD6,
}


# In[5]:


def read_config(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        return lines[0].strip(), int(lines[1])


# In[6]:


def mapping_df_types(df):
    dtypedict = {}
    for i, j in zip(df.columns, df.dtypes):
        if "object" in str(j):
            dtypedict.update({i: sqlalchemy.types.NVARCHAR(length=255)})
        if "float" in str(j):
            dtypedict.update({i: sqlalchemy.types.Float()})
        if "int" in str(j):
            dtypedict.update({i: sqlalchemy.types.Integer()})
        if "datetime" in str(j):
            dtypedict.update({i: sqlalchemy.DateTime()})
    return dtypedict


# In[7]:


# 這裡開始


# In[8]:


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 套用 patch 讓 asyncio 可以在 Jupyter Notebook 重複使用
nest_asyncio.apply()

# 初始化 FastAPI
app = FastAPI(
    title="MES API",
    description="提供MES、AI、會計成本單、訂餐系統的 API 介面",
    version="1.0.0"
)

# --- Logging Middleware ---
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"{request.client.host} - {request.method} {request.url.path} "
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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允許的前端來源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# In[9]:


@app.get("/",
        summary="根目錄",
        description="取得根目錄")
def root():
    return {"success": True, "message": "GET OK"}


# In[10]:


# System


# In[11]:


from resources.System import CurrentTime
CurrentTime_fetcher = CurrentTime(servers=servers)
@app.get("/System/CurrentTime",
    summary="系統時間",
    description="取得系統時間")
async def CurrentTime():
    result = CurrentTime_fetcher.fetch()
    return JSONResponse(content=result, media_type="application/json")
    
@app.post("/System/CurrentTime",
        summary="系統時間",
        description="請使用 GET 取得系統時間")
async def POST_CurrentTime():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})  


# In[12]:


# GreenZone


# In[13]:


from resources.get_gz_data import GET_GZ_data
GET_GZ_data_fetcher = GET_GZ_data(servers=servers)
@app.get("/GET_GZ_data",
        summary="查詢 GreenZone 資料",
        description="透過條件查詢 GreenZone 資料")
async def GET_GZ_data(
    stime: str = Query(default=None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(default=None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    variable_Name: str = Query(default=None, alias="VariableName", description="欲查詢變數，格式包含「METROLOGY-COATINGWEIGHT」、「METROLOGY-COATINGWEIGHT-2SIGMA」、「METROLOGY-P21-MO1-SP」、「METROLOGY-P21-MO1-SP-2SIGMA」或「ACDRY-DCS_A103」"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_fetcher.fetch(stime=stime, etime=etime, variable_Name=variable_Name, MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/GET_GZ_data",
        summary="查詢 GreenZone 資料",
        description="請使用 GET 查詢 GreenZone 資料")
async def POST_GZ_data():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_feature_importance
GET_GZ_data_feature_importance_fetcher = GET_GZ_data_feature_importance(servers=servers)
@app.get("/GET_GZ_data_feature_importance",
        summary="查詢 GreenZone 的重要變數",
        description="透過條件查詢 GreenZone 的重要變數")
async def GET_GZ_data_feature_importance(
    stime: str = Query(default=None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(default=None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    variable_Name: str = Query(default=None, alias="VariableName", description="欲查詢變數，格式只能為以下四種「METROLOGY-COATINGWEIGHT」、「METROLOGY-COATINGWEIGHT-2SIGMA」、「METROLOGY-P21-MO1-SP」、「METROLOGY-P21-MO1-SP-2SIGMA」"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_feature_importance_fetcher.fetch(stime=stime, etime=etime, variable_Name=variable_Name, MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")
    
@app.post("/GET_GZ_data_feature_importance",
        summary="查詢 GreenZone 的重要變數",
        description="請使用 GET 查詢 GreenZone 的重要變數")
async def POST_GZ_data_feature_importance():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_gramg_speed
GET_GZ_data_gramg_speed_fetcher = GET_GZ_data_gramg_speed(servers=servers)
@app.get("/GET_GZ_data_gramg_speed",
        summary="查詢 GreenZone 的基重與車速",
        description="透過條件查詢 GreenZone 的基重與車速")
async def GET_GZ_data_gramg_speed(
    stime: str = Query(default=None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(default=None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_gramg_speed_fetcher.fetch(stime=stime, etime=etime, variable_Name='METROLOGY-COATINGWEIGHT', MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")    

@app.post("/GET_GZ_data_gramg_speed",
        summary="查詢 GreenZone 的基重與車速",
        description="請使用 GET 查詢 GreenZone 的基重與車速")
async def POST_GZ_data_gramg_speed():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung
GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung_fetcher = GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung(servers=servers)
@app.get("/GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung",
        summary="查詢 GreenZone 的狀態，包含停車、段紙、標準化...等資訊",
        description="透過條件查詢 GreenZone 的狀態，包含停車、段紙、標準化...等資訊")
async def GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung(
    stime: str = Query(default=None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(default=None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung_fetcher.fetch(stime=stime, etime=etime, variable_Name='METROLOGY-COATINGWEIGHT', MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung",
        summary="查詢 GreenZone 的狀態，包含停車、段紙、標準化...等資訊",
        description="請使用 GET 查詢 GreenZone 的狀態，包含停車、段紙、標準化...等資訊")
async def POST_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_Outputlist
GET_GZ_data_Outputlist_fetcher = GET_GZ_data_Outputlist(servers=servers)
@app.get("/GET_GZ_data_Outputlist",
        summary="查詢 GreenZone 的訊號代碼與中文名稱",
        description="透過條件查詢 GreenZone 的訊號代碼與中文名稱")
async def GET_GZ_data_Outputlist(
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_Outputlist_fetcher.fetch(MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")      

@app.post("/GET_GZ_data_Outputlist",
        summary="查詢 GreenZone 的訊號代碼與中文名稱",
        description="請使用 GET 查詢 GreenZone 的訊號代碼與中文名稱")
async def POST_GZ_data_Outputlist():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_out_spec_count
GET_GZ_data_out_spec_count_fetcher = GET_GZ_data_out_spec_count(servers=servers)
@app.get("/GET_GZ_data_out_spec_count",
        summary="查詢 GreenZone 的訊號超出規格的詳細內容",
        description="透過條件查詢 GreenZone 的訊號超出規格的詳細內容")
async def GET_GZ_data_out_spec_count(
    stime: str = Query(default=None, alias="Stime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    etime: str = Query(default=None, alias="Etime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_out_spec_count_fetcher.fetch(stime=stime, etime=etime, variable_Name='METROLOGY-COATINGWEIGHT', MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/GET_GZ_data_out_spec_count",
        summary="查詢 GreenZone 的訊號超出規格的詳細內容",
        description="請使用 GET 查詢 GreenZone 的訊號超出規格的詳細內容")
async def POST_GZ_data_out_spec_count():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_out_spec_count_reel
GET_GZ_data_out_spec_count_reel_fetcher = GET_GZ_data_out_spec_count_reel(servers=servers)
@app.get("/GET_GZ_data_out_spec_count_reel",
        summary="查詢 GreenZone 的訊號超出規格的捲紙統計數字",
        description="透過條件查詢 GreenZone 的訊號超出規格的捲紙統計數字")
async def GET_GZ_data_out_spec_count_reel(
    dFrom: str = Query(default=None, alias="dFrom", description="查詢日期，格式yyyy-mm-dd"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_out_spec_count_reel_fetcher.fetch(dFrom=dFrom, MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/GET_GZ_data_out_spec_count_reel",
        summary="查詢 GreenZone 的訊號超出規格的捲紙統計數字",
        description="請使用 GET 查詢 GreenZone 的訊號超出規格的捲紙統計數字")
async def POST_GZ_data_out_spec_count_reel():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_user_favorite
GET_GZ_data_user_favorite_fetcher = GET_GZ_data_user_favorite(servers=servers)
@app.get("/GET_GZ_data_user_favorite",
        summary="查詢 GreenZone 的我的最愛訊號",
        description="透過條件查詢 GreenZone 的我的最愛訊號")
async def GET_GZ_data_user_favorite(
    Isfavorite: str = Query(default=None, alias="Isfavorite", description="是否查詢最愛參數，格式 1、0、NULL"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21")
):
    result = GET_GZ_data_user_favorite_fetcher.fetch(Isfavorite=Isfavorite, MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/GET_GZ_data_user_favorite",
        summary="查詢 GreenZone 的我的最愛訊號",
        description="請使用 GET 查詢 GreenZone 的我的最愛訊號")
async def POST_GZ_data_user_favorite():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

@app.put("/GET_GZ_data_user_favorite",
    summary="更新 GreenZone 我的最愛清單",
    description="一次覆寫 favoritesensor 的所有資料，Request Body 需為字串陣列，例如 ['ACDRY-DCS_A103', 'ACDRY-DCS_A102']"
)
async def PUT_GZ_data_user_favorite(data: List[str] = Body(...)):
    try:
        srv_GZ = GET_GZ_data_user_favorite_fetcher.servers['GZ']
        with srv_GZ['create_engine'][0].connect() as conn:
            with conn.begin():
                conn.execute(text("DELETE FROM public.favoritesensor"))
                sql = text("INSERT INTO public.favoritesensor (sensor) VALUES (:sensor)")
                for sensor in data:
                    conn.execute(sql, {"sensor": sensor})
    except Exception as e:
        return JSONResponse(content={'success': False, 'message': f'Favorite list update failed: {str(e)}'}, status_code=500)

    return JSONResponse(content={'success': True, 'message': 'Favorite list updated successfully'})

from resources.get_gz_data import GET_GZ_data_diff_data
GET_GZ_data_diff_data_fetcher = GET_GZ_data_diff_data(servers=servers)
@app.get("/GET_GZ_data_diff_data",
        summary="查詢 GreenZone 的差異分析資料",
        description="透過條件查詢 GreenZone 的差異分析資料")
async def GET_GZ_data_diff_data(
    variable_Name: str = Query(default=None, alias="VariableName", description="欲查詢變數，格式只能為以下二種「METROLOGY-COATINGWEIGHT」、「METROLOGY-P21-MO1-SP」"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21"),
    ptype: str = Query(default=None, alias="ptype", description="格式 四碼紙別 如KL00"),
    smax: str = Query(default=None, alias="smax", description="格式 車速最大值 如941"),
    smin: str = Query(default=None, alias="smin", description="格式 車速最小值 如851"),
    bdate: str = Query(default=None, alias="bdate", description="格式 歸屬日期 yyyy-mm-dd"),
    wmax: str = Query(default=None, alias="wmax", description="格式 基重最大值 如61"),
    wmin: str = Query(default=None, alias="wmin", description="格式 基重最小值 如55")
):
    result = GET_GZ_data_diff_data_fetcher.fetch(variable_Name=variable_Name, MachineName=MachineName, ptype=ptype,
                                                smax=smax,smin=smin,bdate=bdate,wmax=wmax,wmin=wmin)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/GET_GZ_data_diff_data",
        summary="查詢 GreenZone 的差異分析資料",
        description="請使用 GET 查詢 GreenZone 的差異分析資料")
async def POST_GZ_data_diff_data():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_diff_data_feature_importance
GET_GZ_data_diff_data_feature_importance_fetcher = GET_GZ_data_diff_data_feature_importance(servers=servers)
@app.get("/GET_GZ_data_diff_data_feature_importance",
        summary="查詢 GreenZone 的差異分析資料的前十二大重要特徵",
        description="透過條件查詢 GreenZone 的差異分析資料的前十二大重要特徵")
async def GET_GZ_data_diff_data_feature_importance(
    variable_Name: str = Query(default=None, alias="VariableName", description="欲查詢變數，格式只能為以下二種「METROLOGY-COATINGWEIGHT」、「METROLOGY-P21-MO1-SP」"),
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21"),
    ptype: str = Query(default=None, alias="ptype", description="格式 四碼紙別 如KL00"),
    smax: str = Query(default=None, alias="smax", description="格式 車速最大值 如941"),
    smin: str = Query(default=None, alias="smin", description="格式 車速最小值 如851"),
    timetag: str = Query(default=None, alias="qdate", description="格式 歸屬日期 yyyy-mm-dd"),
    bdate: str = Query(default=None, alias="bdate", description="格式 基準時間 yyyy-mm-dd"),
    cdate: str = Query(default=None, alias="cdate", description="格式 對照時間 yyyy-mm-dd"),
    wmax: str = Query(default=None, alias="wmax", description="格式 基重最大值 如61"),
    wmin: str = Query(default=None, alias="wmin", description="格式 基重最小值 如55")
):
    result = GET_GZ_data_diff_data_feature_importance_fetcher.fetch(variable_Name=variable_Name, MachineName=MachineName, ptype=ptype,
                                                smax=smax,smin=smin,timetag=timetag,bdate=bdate,cdate=cdate,wmax=wmax,wmin=wmin)
    return JSONResponse(content=result, media_type="application/json")    

@app.post("/GET_GZ_data_diff_data_feature_importance",
        summary="查詢 GreenZone 的差異分析資料的前十二大重要特徵",
        description="請使用 GET 查詢 GreenZone 的差異分析資料的前十二大重要特徵")
async def POST_GZ_data_diff_data_feature_importance():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.get_gz_data import GET_GZ_data_prediction_status
GET_GZ_data_prediction_status_fetcher = GET_GZ_data_prediction_status(servers=servers)
@app.get("/greenzone/prediction-status",
        summary="查詢 GreenZone 的機台生產狀態",
        description="透過條件查詢 GreenZone 的機台生產狀態")
async def GET_GZ_data_prediction_status(
    MachineName: str = Query(default=None, alias="MachineName", description="格式 18、19、20、21"),
):
    result = GET_GZ_data_prediction_status_fetcher.fetch(MachineName=MachineName)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/greenzone/prediction-status",
        summary="查詢 GreenZone 的機台生產狀態",
        description="請使用 GET 查詢 GreenZone 的機台生產狀態")
async def POST_GZ_data_prediction_status():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# In[14]:


# MES


# In[15]:


from resources.MES import amreel_groupby_ptime
amreel_groupby_ptime_fetcher = amreel_groupby_ptime(servers=servers)
@app.get("/MES/amreel_groupby_ptime",
        summary="查詢 MES 的各機台彙整的生產資訊",
        description="透過條件查詢 MES 的各機台彙整的生產資訊")
async def amreel_groupby_ptime(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    MachineCode: str = Query(default=None, alias="MachineCode", description="(可選)格式 R1、C1、EA、WA")
):
    result = amreel_groupby_ptime_fetcher.fetch(stime=stime,etime=etime,mname=mname,MachineCode=MachineCode)
    return JSONResponse(content=result, media_type="application/json")    

@app.post("/MES/amreel_groupby_ptime",
        summary="查詢 MES 的各機台彙整的生產資訊",
        description="請使用 GET 查詢 MES 的各機台彙整的生產資訊")
async def POST_amreel_groupby_ptime():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import ERP_SR_summary
ERP_SR_summary_fetcher = ERP_SR_summary(servers=servers)
@app.get("/MES/ERP_SR_summary",
        summary="查詢 MES 的 ERP_SR 資訊",
        description="透過條件查詢 MES 的 ERP_SR 資訊")
async def ERP_SR_summary(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
):
    result = ERP_SR_summary_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")                    

@app.post("/MES/ERP_SR_summary",
        summary="查詢 MES 的 ERP_SR 資訊",
        description="請使用 GET 查詢 MES 的 ERP_SR 資訊")
async def POST_ERP_SR_summary():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import ERP_SH_summary
ERP_SH_summary_fetcher = ERP_SH_summary(servers=servers)
@app.get("/MES/ERP_SH_summary",
        summary="查詢 MES 的 ERP_SH 資訊",
        description="透過條件查詢 MES 的 ERP_SH 資訊")
async def ERP_SH_summary(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
):
    result = ERP_SH_summary_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/ERP_SH_summary",
        summary="查詢 MES 的 ERP_SH 資訊",
        description="請使用 GET 查詢 MES 的 ERP_SH 資訊")
async def POST_ERP_SH_summary():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import adchem_use_d
adchem_use_d_fetcher = adchem_use_d(servers=servers)
@app.get("/MES/adchem_use_d",
        summary="查詢 MES 的 日化工用量",
        description="透過條件查詢 MES 的 日化工用量")
async def adchem_use_d(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
):
    result = adchem_use_d_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/adchem_use_d",
        summary="查詢 MES 的 日化工用量",
        description="請使用 GET 查詢 MES 的 日化工用量")
async def POST_adchem_use_d():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import adcoat_use_d
adcoat_use_d_fetcher = adcoat_use_d(servers=servers)
@app.get("/MES/adcoat_use_d",
        summary="查詢 MES 的 日塗料用量",
        description="透過條件查詢 MES 的 日塗料用量")
async def adcoat_use_d(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
):       
    result = adcoat_use_d_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/adcoat_use_d",
        summary="查詢 MES 的 日塗料用量",
        description="請使用 GET 查詢 MES 的 日塗料用量")
async def POST_adcoat_use_d():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import adpulp_use_d
adpulp_use_d_fetcher = adpulp_use_d(servers=servers)
@app.get("/MES/adpulp_use_d",
        summary="查詢 MES 的 日纖維用量",
        description="透過條件查詢 MES 的 日纖維用量")
async def adpulp_use_d(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
):
    result = adpulp_use_d_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/adpulp_use_d",
        summary="查詢 MES 的 日纖維用量",
        description="請使用 GET 查詢 MES 的 日纖維用量")
async def POST_adpulp_use_d():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import adcoat_use_d_amortization
adcoat_use_d_amortization_fetcher = adcoat_use_d_amortization(servers=servers)
@app.get("/MES/adcoat_use_d_amortization",
        summary="查詢 MES 的 日塗料用量分攤",
        description="透過條件查詢 MES 的 日塗料用量分攤")
async def adcoat_use_d_amortization(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
):           
    result = adcoat_use_d_amortization_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/adcoat_use_d_amortization",
        summary="查詢 MES 的 日塗料用量分攤",
        description="請使用 GET 查詢 MES 的 日塗料用量分攤")
async def POST_adcoat_use_d_amortization():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import adchem_use_d_amortization
adchem_use_d_amortization_fetcher = adchem_use_d_amortization(servers=servers)
@app.get("/MES/adchem_use_d_amortization",
        summary="查詢 MES 的 日化工用量分攤",
        description="透過條件查詢 MES 的 日化工用量分攤")
async def adchem_use_d_amortization(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
): 
    result = adchem_use_d_amortization_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/adchem_use_d_amortization",
        summary="查詢 MES 的 日化工用量分攤",
        description="請使用 GET 查詢 MES 的 日化工用量分攤")
async def POST_adchem_use_d_amortization():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import adpulp_use_d_amortization
adpulp_use_d_amortization_fetcher = adpulp_use_d_amortization(servers=servers)
@app.get("/MES/adpulp_use_d_amortization",
        summary="查詢 MES 的 日纖維用量分攤",
        description="透過條件查詢 MES 的 日纖維用量分攤")
async def adpulp_use_d_amortization(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21")
):              
    result = adpulp_use_d_amortization_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/adpulp_use_d_amortization",
        summary="查詢 MES 的 日纖維用量分攤",
        description="請使用 GET 查詢 MES 的 日纖維用量分攤")
async def POST_adpulp_use_d_amortization():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# In[16]:


from resources.MES import Ampaper_category
Ampaper_category_fetcher = Ampaper_category(servers=servers)
@app.get("/MES/ampaper-category",
        summary="查詢 MES 的 該日期區間生產紙別彙整",
        description="透過條件查詢 MES 的 該日期區間生產紙別彙整")
async def Ampaper_category(
    stime: str = Query(default=None, alias="date_from", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="date_to", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="machine_name", description="格式 18、19、20、21"),
    mode: str = Query(default=None, alias="mode", description="(可選)填入class表示需要生產類別，不填表示需要銷售類別"),
    year_month_from: str = Query(default=None, alias="year_month_from", description="(可選)年月模式，格式yyyy-mm")
):              
    result = Ampaper_category_fetcher.fetch(stime=stime,etime=etime,mname=mname,mode=mode,year_month_from=year_month_from)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/ampaper-category",
        summary="查詢 MES 的 該日期區間生產紙別彙整",
        description="請使用 GET 查詢 MES 的 該日期區間生產紙別彙整")
async def POST_Ampaper_category():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import Defect_induced_recycle_analysis_report
Defect_induced_recycle_analysis_report_fetcher = Defect_induced_recycle_analysis_report(servers=servers)
@app.get("/MES/defect-induced-recycle/report",
        summary="查詢 MES 的 瑕疵回爐分析資料",
        description="透過條件查詢 MES 的 瑕疵回爐分析資料")
async def Defect_induced_recycle_analysis_report(
    stime: str = Query(default=None, alias="yearMonthFrom", description="起始年月，格式yyyy-mm"),
    etime: str = Query(default=None, alias="yearMonthTo", description="結束年月，格式yyyy-mm"),
    mname: str = Query(default=None, alias="machineName", description="格式 18、19、20、21")
):
    result = Defect_induced_recycle_analysis_report_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/defect-induced-recycle/report",
        summary="查詢 MES 的 瑕疵回爐分析資料",
        description="請使用 GET 查詢 MES 的 瑕疵回爐分析資料")
async def POST_Defect_induced_recycle_analysis_report():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import Defect_induced_recycle_chart
Defect_induced_recycle_chart_fetcher = Defect_induced_recycle_chart(servers=servers)
@app.get("/MES/defect-induced-recycle/chart",
        summary="查詢 MES 的 瑕疵回爐分析資料圖",
        description="透過條件查詢 MES 的 瑕疵回爐分析資料圖")
async def Defect_induced_recycle_chart(
    stime: str = Query(default=None, alias="yearMonthFrom", description="起始年月，格式yyyy-mm"),
    etime: str = Query(default=None, alias="yearMonthTo", description="結束年月，格式yyyy-mm"),
    mname: str = Query(default=None, alias="machineName", description="格式 18、19、20、21")
):
    result = Defect_induced_recycle_chart_fetcher.fetch(stime=stime,etime=etime,mname=mname)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/defect-induced-recycle/chart",
        summary="查詢 MES 的 瑕疵回爐分析資料圖",
        description="請使用 GET 查詢 MES 的 瑕疵回爐分析資料圖")
async def POST_Defect_induced_recycle_chart():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import Yield_daily_report
Yield_daily_report_fetcher = Yield_daily_report(servers=servers)
@app.get("/MES/yield-daily-report",
        summary="查詢 MES 的 加工良率每日報表",
        description="透過條件查詢 MES 的 加工良率每日報表")
async def Yield_daily_report(
    stime: str = Query(default=None, alias="date_from", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="date_to", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="machine_name", description="格式 18、19、20、21"),
    Product_Category: str = Query(default=None, alias="category", description="生產類別，格式 格拉新、單銅")
):
    result = Yield_daily_report_fetcher.fetch(stime=stime,etime=etime,mname=mname,Product_Category=Product_Category)
    return JSONResponse(content=result, media_type="application/json")            

@app.post("/MES/yield-daily-report",
        summary="查詢 MES 的 加工良率每日報表",
        description="請使用 GET 查詢 MES 的 加工良率每日報表")
async def POST_Yield_daily_report():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.MES import Relno_production_history
Relno_production_history_fetcher = Relno_production_history(servers=servers)
@app.get("/MES/Relno-production-history",
        summary="查詢 MES 的 紙捲號碼生產履歷",
        description="透過條件查詢 MES 的 紙捲號碼生產履歷")
async def Relno_production_history(
    relno: str = Query(default=None, alias="relno", description="紙捲號碼，格式 W5101301")
):
    result = Relno_production_history_fetcher.fetch(relno=relno)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/Relno-production-history",
        summary="查詢 MES 的 紙捲號碼生產履歷",
        description="請使用 GET 查詢 MES 的 紙捲號碼生產履歷")
async def POST_Relno_production_history():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# In[17]:


# CostSheet


# In[18]:


from resources.CostSheet import product_cost_details
product_cost_details_fetcher = product_cost_details(servers=servers)
@app.get("/MES/product_cost_details",
        summary="查詢 會計 成本單",
        description="透過條件查詢 會計 成本單")
async def product_cost_details(
    stime: str = Query(default=None, alias="stime", description="起始年月，格式yyyymm"),
    etime: str = Query(default=None, alias="etime", description="結束年月，格式yyyymm"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    Product_Category: str = Query(default=None, alias="category", description="格式 根據level 不同 值不同 預設是1 格式 格拉新、NCR"),
    Product_two_ptype: str = Query(default=None, alias="ptype_two", description="(可選)兩碼紙別 格式 KL、SL、KA"),
    two_month: str = Query(default=None, alias="two_month", description="(可選)格式 1 表示只顯示兩個月的資料 0 表示顯示三個月的資料 預設為 0"),
    level: str = Query(default=None, alias="level", description="(可選)格式 1 表示銷售類別 2 表示兩碼紙別 3 表示四碼紙別")
):
    result = product_cost_details_fetcher.fetch(stime=stime,etime=etime,mname=mname,Product_Category=Product_Category,
                                               Product_two_ptype=Product_two_ptype,two_month=two_month,level=level)
    return JSONResponse(content=result, media_type="application/json")    

@app.post("/MES/product_cost_details",
        summary="查詢 會計 成本單",
        description="請使用 GET 查詢 會計 成本單")
async def POST_product_cost_details():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import product_cost_equivalent
product_cost_equivalent_fetcher = product_cost_equivalent(servers=servers)
@app.get("/MES/product_cost_equivalent",
        summary="查詢 會計 約當量與得率報表",
        description="透過條件查詢 會計 約當量與得率報表")
async def product_cost_equivalent(
    stime: str = Query(default=None, alias="stime", description="起始年月，格式yyyymm"),
    etime: str = Query(default=None, alias="etime", description="結束年月，格式yyyymm"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    Product_Category: str = Query(default=None, alias="category", description="銷售類別 格式 格拉新、NCR"),
    Product_two_ptype: str = Query(default=None, alias="ptype_two", description="(可選)兩碼紙別 格式 KL、SL、KA"),
    two_month: str = Query(default=None, alias="two_month", description="(可選)格式 1 表示只顯示兩個月的資料 0 表示顯示三個月的資料 預設為 0")
):
    result = product_cost_equivalent_fetcher.fetch(stime=stime,etime=etime,mname=mname,Product_Category=Product_Category,
                                               Product_two_ptype=Product_two_ptype,two_month=two_month)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/product_cost_equivalent",
        summary="查詢 會計 約當量與得率報表",
        description="請使用 GET 查詢 會計 約當量與得率報表")
async def POST_product_cost_equivalent():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import monthly_equivalent_production
monthly_equivalent_production_fetcher = monthly_equivalent_production(servers=servers)
@app.get("/MES/monthly_equivalent_production",
        summary="查詢 會計 約當產量報表",
        description="透過條件查詢 會計 約當產量報表")
async def monthly_equivalent_production(
    year: str = Query(default=None, alias="year", description="年份，格式yyyy"),
):
    result = monthly_equivalent_production_fetcher.fetch(year=year)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/monthly_equivalent_production",
        summary="查詢 會計 約當產量報表",
        description="請使用 GET 查詢 會計 約當產量報表")
async def POST_monthly_equivalent_production():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import monthly_ERP_inventory
monthly_ERP_inventory_fetcher = monthly_ERP_inventory(servers=servers)
@app.get("/MES/monthly_ERP_inventory",
        summary="查詢 會計 入庫量月報表",
        description="透過條件查詢 會計 入庫量月報表")
async def monthly_ERP_inventory(
    year: str = Query(default=None, alias="year", description="年份，格式yyyy"),
):
    result = monthly_ERP_inventory_fetcher.fetch(year=year)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/monthly_ERP_inventory",
        summary="查詢 會計 入庫量月報表",
        description="請使用 GET 查詢 會計 入庫量月報表")
async def POST_monthly_ERP_inventory():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import monthly_yield_rate
monthly_yield_rate_fetcher = monthly_yield_rate(servers=servers)
@app.get("/MES/monthly_yield_rate",
        summary="查詢 會計 月得率報表",
        description="透過條件查詢 會計 月得率報表")
async def monthly_yield_rate(
    year: str = Query(default=None, alias="year", description="年份，格式yyyy"),
):
    result = monthly_yield_rate_fetcher.fetch(year=year)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/monthly_yield_rate",
        summary="查詢 會計 月得率報表",
        description="請使用 GET 查詢 會計 月得率報表")
async def POST_monthly_yield_rate():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import ERP_inventory
ERP_inventory_fetcher = ERP_inventory(servers=servers)
@app.get("/MES/erp-inventory",
        summary="查詢 入庫量報表",
        description="透過條件查詢 入庫量報表")
async def ERP_inventory(
    stime: str = Query(default=None, alias="date_from", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="date_to", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="machine_name", description="格式 18、19、20、21"),
    month: str = Query(default=None, alias="month", description="(可選)年月，格式yyyy-mm"),
):
    result = ERP_inventory_fetcher.fetch(stime=stime,etime=etime,mname=mname,month=month)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/erp-inventory",
        summary="查詢 入庫量報表",
        description="請使用 GET 查詢 入庫量報表")
async def POST_ERP_inventory():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import End_work_in_process
End_work_in_process_fetcher = End_work_in_process(servers=servers)
@app.get("/MES/End_work_in_process",
        summary="查詢 期末在產品報表",
        description="透過條件查詢 期末在產品報表")
async def End_work_in_process(
    year_month_from: str = Query(default=None, alias="year_month_from", description="年月，格式yyyymm"),
):
    result = End_work_in_process_fetcher.fetch(year_month_from=year_month_from)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/End_work_in_process",
        summary="查詢 期末在產品報表",
        description="請使用 GET 查詢 期末在產品報表")
async def POST_End_work_in_process():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import monthly_fixed_fee
monthly_fixed_fee_fetcher = monthly_fixed_fee(servers=servers)
@app.get("/MES/monthly_fixed_fee",
        summary="查詢 會計 固定費用報表",
        description="透過條件查詢 會計 固定費用報表")
async def monthly_fixed_fee(
    year: str = Query(default=None, alias="year", description="年份，格式yyyy"),
):
    result = monthly_fixed_fee_fetcher.fetch(year=year)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/monthly_fixed_fee",
        summary="查詢 會計 固定費用報表",
        description="請使用 GET 查詢 會計 固定費用報表")
async def POST_monthly_fixed_fee():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import monthly_energy_usage
monthly_energy_usage_fetcher = monthly_energy_usage(servers=servers)
@app.get("/MES/monthly_energy_usage",
        summary="查詢 會計 能源耗用成本報表",
        description="透過條件查詢 會計 能源耗用成本報表")
async def monthly_energy_usage(
    year: str = Query(default=None, alias="year", description="年份，格式yyyy"),
):
    result = monthly_energy_usage_fetcher.fetch(year=year)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/monthly_energy_usage",
        summary="查詢 會計 能源耗用成本報表",
        description="請使用 GET 查詢 會計 能源耗用成本報表")
async def POST_monthly_energy_usage():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

from resources.CostSheet import monthly_Cost_sheet
monthly_Cost_sheet_fetcher = monthly_Cost_sheet(servers=servers)
@app.get("/MES/monthly_Cost_sheet",
        summary="查詢 會計 月成本報表",
        description="透過條件查詢 會計 月成本報表，參數為(year,ptype2)、(year_month_From,mname)，前者為年模式、後者為年月模式，任選一對輸入即可")
async def monthly_Cost_sheet(
    year_month_From: str = Query(default=None, alias="year_month_From", description="年月，格式yyyymm"),
    mname: str = Query(default=None, alias="mname", description="格式 PM18、PM19、PM20、PM21"),
    year: str = Query(default=None, alias="year", description="年份，格式yyyy"),
    ptype2: str = Query(default=None, alias="ptype2", description="兩碼紙別 格式 KL、SL、KA"),   
):
    result = monthly_Cost_sheet_fetcher.fetch(year_month_From=year_month_From,mname=mname,year=year,ptype2=ptype2)
    return JSONResponse(content=result, media_type="application/json")

@app.post("/MES/monthly_Cost_sheet",
        summary="查詢 會計 月成本報表",
        description="請使用 GET 查詢 會計 月成本報表")
async def POST_monthly_Cost_sheet():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# In[19]:


# CostSheet_Maintenance


# In[20]:


from resources.CostSheet_Maintenance import CoatingWeight
CoatingWeight_fetcher = CoatingWeight(servers=servers)
@app.get("/MES/CostSheet/CoatingWeight",
        summary="查詢 塗佈量設定",
        description="透過條件查詢 塗佈量設定")
async def get_coating_weight():
    result = CoatingWeight_fetcher.fetch()
    return JSONResponse(content=result, media_type="application/json")

class CoatingWeightModel(BaseModel):
    Machine: str
    PN2: str
    PN4: str
    PaperGSM: int
    ProductGSM: int
    PN4BW: int
    TypePaperGSM: str
    TypeProductGSM: str
    OnMachineCoating: float
    OffMachineCoating1: float
    OffMachineCoating2: float
    TotalCoating: float
    TypeName: str
    BasePN4: str
    BasePaperGSM: int
    buser: str
    muser: str

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "Machine": "M01",
                    "PN2": "P1",
                    "PN4": "P123",
                    "PaperGSM": 80,
                    "ProductGSM": 82,
                    "PN4BW": 100,
                    "TypePaperGSM": "TypeA",
                    "TypeProductGSM": "TypeB",
                    "OnMachineCoating": 2.5,
                    "OffMachineCoating1": 1.0,
                    "OffMachineCoating2": 0.5,
                    "TotalCoating": 4.0,
                    "TypeName": "A",
                    "BasePN4": "B123",
                    "BasePaperGSM": 80,
                    "buser": "admin",
                    "muser": "admin"
                }
            ]
        }

@app.post("/MES/CostSheet/CoatingWeight",
    summary="新增 塗佈量設定",
    description="利用 POST 新增一筆 CoatingWeight 記錄，請依照下方範例提供所有欄位。")          
async def create_coating_weight(payload: CoatingWeightModel):
    try:
        payload_dict = payload.dict()
        
        with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
            fields = ", ".join(payload_dict.keys())
            values = ", ".join(f":{k}" for k in payload_dict.keys())
            sql = f"INSERT INTO [Accounting].[dbo].[CoatingWeight] ({fields}) VALUES ({values})"
            conn.execute(text(sql), payload_dict)
        return JSONResponse(content={"success": True, "message": "Inserted successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
    
class CoatingWeightUpdateModel(BaseModel):
    Machine: Optional[str] = None
    PN2: Optional[str] = None
    PN4: Optional[str] = None
    PaperGSM: Optional[int] = None
    ProductGSM: Optional[int] = None
    PN4BW: Optional[int] = None
    TypePaperGSM: Optional[str] = None
    TypeProductGSM: Optional[str] = None
    OnMachineCoating: Optional[float] = None
    OffMachineCoating1: Optional[float] = None
    OffMachineCoating2: Optional[float] = None
    TotalCoating: Optional[float] = None
    TypeName: Optional[str] = None
    BasePN4: Optional[str] = None
    BasePaperGSM: Optional[int] = None
    buser: Optional[str] = None
    muser: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "Machine": "M01",
                "PN4": "UPDA",
                "TotalCoating": 5.0,
                "muser": "admin"
            }
        }

@app.put("/MES/CostSheet/CoatingWeight/{sn}",
    summary="更新 塗佈量設定",
    description="可更新任意欄位，未提供的欄位不會修改。"
)
async def update_coating_weight(
    sn: int,
    payload: CoatingWeightUpdateModel
):
    try:
        update_data = payload.dict(exclude_unset=True)  # 只保留有提供的欄位
        
        if not update_data:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "No data provided for update"}
            )
        
        set_clause = ", ".join(f"{k} = :{k}" for k in update_data.keys())
        update_data["sn"] = sn        
        
        with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
            sql = f"UPDATE [Accounting].[dbo].[CoatingWeight] SET {set_clause} WHERE Sn = :sn"
            conn.execute(text(sql), update_data)
        return JSONResponse(content={"success": True, "message": "Updated successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.delete("/MES/CostSheet/CoatingWeight/{sn}",
    summary="刪除塗佈量設定",
    description="依照 Sn 刪除指定的 CoatingWeight 記錄。"
)
async def delete_coating_weight(sn: int):
    try:
        with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
            sql = "DELETE FROM [Accounting].[dbo].[CoatingWeight] WHERE Sn = :sn"
            conn.execute(text(sql), {"sn": sn})
        return JSONResponse(content={"success": True, "message": "Deleted successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


# In[21]:


# 車輛進出載重管理


# In[22]:


# from resources.Vehicle_entry_management import Transport_companies
# Transport_companies_fetcher = Transport_companies(servers=servers)
# @app.get("/vehicle-entry-load-management/transport-companies")
# async def Transport_companies():
#     result = Transport_companies_fetcher.fetch()
#     return JSONResponse(content=result, media_type="application/json")
    
# @app.post("/vehicle-entry-load-management/transport-companies")
# async def POST_Transport_companies():
#     return JSONResponse(content={'success': False, 'message': 'Please use GET'})    

# from resources.Vehicle_entry_management import Vehicle_entry_load_management
# Vehicle_entry_load_management_fetcher = Vehicle_entry_load_management(servers=servers)
# @app.get("/vehicle-entry-load-management/vehicle")
# async def Vehicle_entry_load_management(
#     plate: str = Query(default=None, alias="plate")
# ):
#     result = Vehicle_entry_load_management_fetcher.fetch(plate=plate)
#     return JSONResponse(content=result, media_type="application/json")
    
# @app.post("/vehicle-entry-load-management/vehicle")
# async def POST_Vehicle_entry_load_management(request: Request):
#     try:
#         data = await request.json()

#         # 檢查 Lic_plate 必填
#         if 'Lic_plate' not in data:
#             return JSONResponse(status_code=400, content={'success': False, 'message': 'Missing field: Lic_plate'})     

#         all_fields = ["Lic_plate", "tag_ID", "dept", "owner", "v_type", "v_weight", "main_load", "fuel", "memo", "busr"]

#         # 補齊缺漏欄位為 None
#         for field in all_fields:
#             data.setdefault(field, None)

#         # 插入資料
#         with df_SERVER_SRVADA1['create_engine'][0].connect() as conn:
#             insert_sql = text("""
#                 INSERT INTO [ERP-A].[dbo].[VehicleData] (
#                     Lic_plate, tag_ID, dept, owner, v_type, v_weight, main_load, fuel, memo, busr
#                 ) VALUES (
#                     :Lic_plate, :tag_ID, :dept, :owner, :v_type, :v_weight, :main_load, :fuel, :memo, :busr
#                 )
#             """)
#             conn.execute(insert_sql, data)  # 用 dict 傳遞參數

#         return JSONResponse(status_code=201, content={'success': True, 'message': 'Vehicle inserted successfully'})

#     except Exception as e:
#         return JSONResponse(status_code=500, content={'success': False, 'message': f'Insert failed: {str(e)}'})
    
# @app.get("/vehicle-entry-load-management/inbound-outbound-record")
# async def get_inbound_outbound():
#     return JSONResponse(status_code=405, content={'success': False, 'message': 'Please use POST'})    

# @app.post("/vehicle-entry-load-management/inbound-outbound-record")
# async def post_inbound_outbound(request: Request):
#     startTime = time.time()

#     try:
#         data = await request.json()

#         if 'isInbound' not in data:
#             return JSONResponse(status_code=400, content={'success': False, 'message': 'Missing field: isInbound'})
#         if 'plate' not in data:
#             return JSONResponse(status_code=400, content={'success': False, 'message': 'Missing field: plate'})            

#         all_fields = [
#             "isInbound", "plate", "grossWeightKg", "tareWeightKg", "netWeightKg", 
#             "tractorWeightKg", "flatbedTrailerWeightKg", "containerWeightKg", "mainLoad",
#             "memo", "weighStation", "weighTicketNo", "busr"
#         ]

#         # 補齊缺漏欄位為 None
#         for field in all_fields:
#             data.setdefault(field, None)

#         # 資料庫插入
#         with df_SERVER_SRVADA1['create_engine'][0].connect() as conn:
#             insert_sql = text("""
#                 INSERT INTO [ERP-A].[dbo].[InboundOutboundRecord] (
#                     [isInbound],[plate],[grossWeightKg],[tareWeightKg],[netWeightKg],[tractorWeightKg],
#                     [flatbedTrailerWeightKg],[containerWeightKg],[mainLoad],[memo],[weighStation],[weighTicketNo],[busr]
#                 ) VALUES (
#                     :isInbound, :plate, :grossWeightKg, :tareWeightKg, :netWeightKg, :tractorWeightKg,
#                     :flatbedTrailerWeightKg, :containerWeightKg, :mainLoad, :memo, :weighStation, :weighTicketNo, :busr
#                 )
#             """)
#             conn.execute(insert_sql, data)

#         return JSONResponse(status_code=201, content={'success': True, 'message': 'InboundOutboundRecord inserted successfully'})

#     except Exception as e:
#         return JSONResponse(status_code=500, content={'success': False, 'message': f'Insert failed: {str(e)}'})    


# In[23]:


# 員工訂餐系統


# In[24]:


from resources.Staff_meal_ordering_system import Staff_meal_ordering_query
Staff_meal_ordering_query_fetcher = Staff_meal_ordering_query(servers=servers)
@app.get("/Staff_meal_ordering_system/Staff_meal_ordering_query",
        summary="查詢 員工訂餐紀錄",
        description="透過條件查詢 員工訂餐紀錄")
async def Staff_meal_ordering_query(
    year: str = Query(default=None, alias="year", description="年份，格式 yyyy"),
    month: str = Query(default=None, alias="month", description="月份，格式 mm"),
    day: str = Query(default=None, alias="day", description="(可選)日期，格式 dd"),
    cardno: str = Query(default=None, alias="cardno", description="(可選)卡號，格式 A1234"),
    code: str = Query(default=None, alias="code", description="(可選)用餐地點代碼，格式 B05"),
    dn: str = Query(default=None, alias="dn", description="(可選)餐別，格式 01 午餐 03 晚餐"),
    food: str = Query(default=None, alias="food", description="(可選)餐別，格式 2 葷 3 素"),
):
    result = Staff_meal_ordering_query_fetcher.fetch(year=year,month=month,cardno=cardno,day=day,code=code,dn=dn,food=food)
    return JSONResponse(content=result, media_type="application/json")

class StaffMealOrderingModel(BaseModel):
    cardno: str
    nad: str
    cktime: str
    loca: str
    locaName: str
    Category: str

    class Config:
        json_schema_extra = {
            "example": {
                "cardno": "A5558",
                "nad": "01",
                "cktime": "2025-11-11 08:03:01.000",
                "loca": "10.10.1.62",
                "locaName": "舊廠便當機",
                "Category": "01"
            }
        }

@app.post("/Staff_meal_ordering_system/Staff_meal_ordering_query",
    summary="新增員工餐點紀錄",
    description="將一筆餐點紀錄寫入 [HR].[dbo].[erp_eat_log] 資料表，請依照下方範例輸入欄位。"
)
async def POST_Staff_meal_ordering_query(payload: StaffMealOrderingModel):
    try:
        data = payload.dict()
        
        with df_SERVER_SRVAD6['create_engine'][0].connect() as conn:
            fields = ", ".join(data.keys())
            values = ", ".join(f":{k}" for k in data.keys())
            sql = f"INSERT INTO [HR].[dbo].[erp_eat_log] ({fields}) VALUES ({values})"
            conn.execute(text(sql), data)
        return JSONResponse(content={"success": True, "message": "Inserted successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
    
@app.delete("/Staff_meal_ordering_system/Staff_meal_ordering_query/{sid}",
    summary="刪除員工餐點紀錄",
    description="依照 Sn 刪除指定的 員工餐點紀錄。"
)            
async def delete_Staff_meal_ordering(sid: int):
    try:
        engine = df_SERVER_SRVAD6['create_engine'][0]
        with engine.begin() as conn:  # 使用 begin() 自動 commit/rollback
            sid_sql =  """
                SELECT TOP 1 
                    cardno,dn,bdate
                FROM hdeatlog
                WHERE sid = :sid            
            """
            row = conn.execute(text(sid_sql), {"sid": sid}).mappings().first()
            
            if not row:
                return {"success": False, "message": f"sid {sid} not found"}
            
            cardno = row["cardno"]
            dn = row["dn"]
            bdate = row["bdate"]   
            
            # 找出所有要刪除的 sid（可能有多筆）
            sids_to_delete = conn.execute(
                text("SELECT sid FROM [HR].[dbo].[hdeatlog] WHERE cardno = :cardno AND dn = :dn AND bdate = :bdate"),
                {"cardno": cardno, "dn": dn, "bdate": bdate}
            ).scalars().all()
            
            del_sid_sql = """
                DELETE FROM [HR].[dbo].[hdeatlog]
                WHERE cardno = :cardno AND dn = :dn AND bdate = :bdate
            """
            # 刪除 hdeatlog
            conn.execute(text(del_sid_sql), {"cardno": cardno, "dn": dn, "bdate": bdate})

            # 逐筆刪除 erp_eat_log
            for s in sids_to_delete:
                conn.execute(
                    text("DELETE FROM [HR].[dbo].[erp_eat_log] WHERE sid = :sid"),
                    {"sid": s}
                )

        return JSONResponse(content={"success": True, "message": "Deleted successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


# In[25]:


from resources.Staff_meal_ordering_system import Staff_meal_ordering_query_guest_meal
Staff_meal_ordering_query_guest_meal_fetcher = Staff_meal_ordering_query_guest_meal(servers=servers)
@app.get("/Staff_meal_ordering_system/Staff_meal_ordering_query_guest_meal",
        summary="查詢 客飯訂餐紀錄",
        description="透過條件查詢 客飯訂餐紀錄")
async def Staff_meal_ordering_query_guest_meal(
    year: str = Query(default=None, alias="year", description="年份，格式 yyyy"),
    month: str = Query(default=None, alias="month", description="月份，格式 mm"),
    day: str = Query(default=None, alias="day", description="(可選)日期，格式 dd"),
    cardno: str = Query(default=None, alias="cardno", description="(可選)卡號，格式 A1234"),
    code: str = Query(default=None, alias="code", description="(可選)用餐地點代碼，格式 B05"),
    mtype: str = Query(default=None, alias="mtype", description="(可選)餐別，格式 lunch、dinner")

):
    result = Staff_meal_ordering_query_guest_meal_fetcher.fetch(year=year,month=month,cardno=cardno,day=day,code=code,mtype=mtype)
    return JSONResponse(content=result, media_type="application/json")

class GuestMealOrderingModel(BaseModel):
    cardno: str
    mtype: str
    cnt_02: str  
    cnt_03: str
    code: str
    cktime: str
    con_name: str
    memo: str

    class Config:
        json_schema_extra = {
            "example": {
              "cardno": "A5558",
              "mtype": 'dinner', # lunch / dinner
              "cnt_02": '0',
              "cnt_03": "1",
              "code": "A01",
              "cktime": "2025-11-19 15:30:00",
              "con_name": "超人有限公司",
              "memo": "",
            }
        }

@app.post("/Staff_meal_ordering_system/Staff_meal_ordering_query_guest_meal",
    summary="新增客飯餐點紀錄",
    description="將一筆餐點紀錄寫入 [HR].[dbo].[hdeatlog_KB] 資料表，請依照下方範例輸入欄位。"
)
async def POST_Staff_meal_ordering_query_guest_meal(payload: GuestMealOrderingModel):
    try:
        data = payload.dict()
        
        required_fields = ["cardno", "code", "cktime"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Missing parameter(s): {', '.join(missing)}"
                }
            ) 
        
        cardno = data.get("cardno")
        code = data.get("code")           
        cktime_str = data.get("cktime")  
        
        bdate = None
        if cktime_str:
            try:
                cktime = datetime.datetime.strptime(cktime_str, "%Y-%m-%d %H:%M:%S")
                bdate = datetime.datetime(cktime.year, cktime.month, cktime.day, 0, 0, 0)
            except ValueError:
                bdate = None                

        # 預設值
        memo = data.get("memo", "")     
        
        with df_SERVER_SRVAD6['create_engine'][0].connect() as conn:

            staff_sql = """
                SELECT TOP 1 
                       emp_id AS cardno, 
                       chsnm,
                       team_sn
                FROM hmstaff
                WHERE emp_id = :cardno
            """
            staff_row = conn.execute(text(staff_sql), {"cardno": cardno}).mappings().first()

            if not staff_row:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": f"找不到卡號 {cardno} 對應的員工資料"}
                )
            
            if bdate:
                ID_sql = """
                    SELECT TOP 1 ID 
                    FROM hdeatlog_KB 
                    where bdate= :bdate 
                    order by ID desc
                """
                ID_row = conn.execute(text(ID_sql), {"bdate": bdate}).mappings().first()
                ID_name = int(ID_row["ID"]) + 1 if ID_row else 1
                
            bdate = bdate.strftime("%Y-%m-%d %H:%M:%S")

            # 合併欄位
            insert_data = {
                **data,  # 使用者傳的欄位
                "ID": str(ID_name),
                "team_sn": staff_row["team_sn"],
                "bdate": bdate,
                "memo": memo,
                "musr": cardno,
            }

            fields = ", ".join(insert_data.keys())
            values = ", ".join(f":{k}" for k in insert_data.keys())
            sql = f"INSERT INTO [HR].[dbo].[hdeatlog_KB] ({fields}) VALUES ({values})"
            conn.execute(text(sql), insert_data)
            
        return JSONResponse(content={"success": True, "message": "Inserted successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
    
@app.delete("/Staff_meal_ordering_system/Staff_meal_ordering_query_guest_meal/{sn}",
    summary="刪除客飯餐點紀錄",
    description="依照 Sn 刪除指定的 客飯餐點紀錄。"
)            
async def delete_Staff_meal_ordering_query_guest_meal(sn: int):
    try:
        engine = df_SERVER_SRVAD6['create_engine'][0]
        with engine.begin() as conn:  # 使用 begin() 自動 commit/rollback
            sn_sql =  """
                SELECT TOP 1 
                    code,cardno,team_sn,bdate,mtype,con_name,cnt_02,cnt_03,memo                  
                FROM hdeatlog_KB
                WHERE sn = :sn            
            """
            row = conn.execute(text(sn_sql), {"sn": sn}).mappings().first()
            
            if not row:
                return {"success": False, "message": f"sn {sn} not found"}    
            
            code = row["code"]
            cardno = row["cardno"]
            team_sn = row["team_sn"]
            bdate = row["bdate"]
            mtype = row["mtype"]
            con_name = row["con_name"]
            cnt_02 = row["cnt_02"]
            cnt_03 = row["cnt_03"]
            memo = row["memo"]
            
            del_sn_sql = """
                DELETE FROM [HR].[dbo].[hdeatlog_KB]
                WHERE code = :code AND cardno = :cardno AND team_sn = :team_sn AND bdate = :bdate
                AND mtype = :mtype AND con_name = :con_name AND cnt_02 = :cnt_02 AND cnt_03 = :cnt_03 AND memo = :memo
            """
            # 刪除 hdeatlog
            conn.execute(text(del_sn_sql), {"code": code,"cardno": cardno, "team_sn": team_sn,"bdate": bdate,
                                             "mtype": mtype,"con_name": con_name,
                                             "cnt_02": cnt_02,"cnt_03": cnt_03,"memo": memo})
            
        return JSONResponse(content={"success": True, "message": "Deleted successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


# In[26]:


# 讀取設定檔
try:
    host, port = read_config("config2.txt")
except:
    try:
        host, port = read_config(r"E:\AP\Api\dist\config2.txt") 
    except:        
        try:
            host, port = read_config("config.txt")
        except:
            host, port = read_config(r"E:\AP\Api\dist\config.txt")  
    
# 共用的 config/server 實例
config = uvicorn.Config(app, host=host, port=port, log_level="info",timeout_keep_alive=30)
server = uvicorn.Server(config)

# 判斷是否在 Jupyter Notebook 環境中
def is_notebook():
    try:
        shell = get_ipython().__class__.__name__
        return shell == 'ZMQInteractiveShell'
    except NameError:
        return False

# ✅ Jupyter Notebook 中啟動方式
if is_notebook():
    if "server_started" not in globals():
        asyncio.create_task(server.serve())
        server_started = True        

# ✅ 一般 Python 環境／打包環境使用 asyncio.run()
else:
    async def start_server():
        await server.serve()

    if __name__ == "__main__":
        asyncio.run(start_server())
        
# swagger 
# http://10.10.2.154:50001/docs#/default


# In[ ]:




