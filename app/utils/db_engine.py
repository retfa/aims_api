#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.db_connections import load_connection_info

# 指定哪些 SQL Server DB 要用 READ UNCOMMITTED
READ_UNCOMMITTED_DBS = ["YFYAIUPSVISA1"]

# 全域 engine cache，避免每次都 new engine
_engine_cache = {}

def get_engine(db_name):
    if db_name in _engine_cache:
        return _engine_cache[db_name]    
    
    conn_str, db_type = load_connection_info(db_name)
    
    # 共用 engine args
    engine_args = dict(
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_timeout=5,
    )

    if db_type == "mssql":
        # MSSQL 特定設定
        engine_args["fast_executemany"] = True
        
        # --- 策略：與 PostgreSQL 保持對稱，確保整體吞吐量 ---
        engine_args["pool_size"] = 20
        engine_args["max_overflow"] = 30
        
        # 只對指定資料庫使用 READ UNCOMMITTED
        if db_name in READ_UNCOMMITTED_DBS:
            engine_args["isolation_level"] = "READ UNCOMMITTED"
    elif db_type == "postgresql":
        # PostgreSQL 特定設定
        engine_args["pool_size"] = 20          # 控制最大連線
        engine_args["max_overflow"] = 30       # 超過 5 個就等，不開更多
        engine_args["connect_args"] = {"connect_timeout": 5}
        engine_args["isolation_level"] = "AUTOCOMMIT"  # 🔑 避免 idle ROLLBACK        

    engine = create_engine(conn_str, **engine_args)
    # cache 起來
    _engine_cache[db_name] = engine
    return engine

def get_session(db_name):
    engine = get_engine(db_name)
    return sessionmaker(bind=engine)

