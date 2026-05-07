#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import json
from urllib.parse import quote_plus as urlquote
from utils.filepath import get_temproot_and_exe_folder
import sys

def load_connection_info(servers_db_name="SRVMSDBA2_GREENZONE"):
    """
    從 connections.json 讀取指定 DB 的連線資訊
    """
    if getattr(sys, "frozen", False):
        # 打包成 exe，檔案在 exe 同目錄下的 app 資料夾
        project_root = os.path.join(os.path.dirname(sys.executable), "app")
    else:
        # 開發環境
        temp_root, exe_folder = get_temproot_and_exe_folder()
        project_root = os.path.dirname(temp_root)  # 上層資料夾 

    json_path = os.path.join(project_root, "connections.json")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到 {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        connections = json.load(f)

    if servers_db_name not in connections:
        raise ValueError(f"DB '{servers_db_name}' 不在 connections.json 中")

    info = connections[servers_db_name]
    
    db_type = info.get("type", "mssql")  # 預設 SQL Server

    username = urlquote(info["username"])
    password = urlquote(info["password"])
    
    if db_type == "mssql":
        conn_str = (
            f"mssql+pyodbc://{username}:{password}@{info['server']}/{info['database']}"
            f"?driver=ODBC+Driver+17+for+SQL+Server"
            f"&timeout=10"               # ← 新增：連線建立最多等 10s
            f"&ConnectRetryCount=3"      # ← 新增：失敗自動重試 3 次
            f"&ConnectRetryInterval=5"   # ← 新增：每次重試間隔 5s            
        )
    elif db_type == "postgresql":
        port = info.get("port", 5432)
        conn_str = f"postgresql+psycopg2://{username}:{password}@{info['server']}:{port}/{info['database']}"
    else:
        raise ValueError(f"Unknown db type: {db_type}")

    return conn_str, db_type

