#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import timedelta
from sqlalchemy import text

import requests
import json

from collections import defaultdict


# In[ ]:


import logging
logger = logging.getLogger(__name__)  # 取得和主程式共用的 logger


# In[ ]:


class OutputListQuery:
    
    DB_NAME = "AIMSFTAO"
    SCHEMA = "dbo"    
    
    def __init__(self, servers):
        self.servers = servers
        self.engine = self.servers['SRVMSDBA1']["create_engine"][0]
        
    # -------------------------
    # 判斷明細表是否存在
    # -------------------------
    def _detail_exists(self, conn, table: str, master_sn: int) -> bool:
        sql = f"SELECT 1 FROM [{self.DB_NAME}].[{self.SCHEMA}].[{table}] WHERE MasterSn = :sn"
        result = conn.execute(text(sql), {"sn": master_sn}).first()
        return result is not None        
       
    # =========================
    # 共用：時間欄位轉字串
    # =========================
    def _convert_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        for col in df.columns:
            if "Date" in col or "date" in col:
                df[col] = pd.to_datetime(df[col], errors="coerce")

                # 轉 ISO 格式字串，保留微秒和時區
                df[col] = df[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)

        # 清理 null char
        df = df.applymap(
            lambda x: None if isinstance(x, str) and '\x00' in x else x
        )

        return df
    
    # =========================
    # 共用：撈 MasterSn 明細表
    # =========================
    def _fetch_detail(self, conn, table_name: str, sn: int) -> list:
        sql = f"""
            SELECT *
            FROM [AIMSFTAO].[dbo].[{table_name}]
            WHERE MasterSn = :sn
        """

        df = pd.read_sql(text(sql), conn, params={"sn": sn})
        df = self._convert_datetime(df)

        return df.to_dict(orient="records") 
    
    # =========================
    # 主功能
    # =========================    
    def fetch(self, sn: int):

        startTime = time.time()
        
        result_json = {
            "m": {},
            "mes": [],
            "wspgalaxy": [],
            "wspdevice": [],
            "emd": []
        }        

        try:
            srv = self.servers['SRVMSDBA1']

            with srv["create_engine"][0].connect() as conn:

                # 1️⃣ 撈主表
                sql_m = """
                    SELECT *
                    FROM [AIMSFTAO].[dbo].[ooutputlist_m]
                    WHERE Sn = :sn
                """

                df_m = pd.read_sql(text(sql_m), conn, params={"sn": sn})

                if df_m.empty:
                    return {"data": result_json}

                df_m = self._convert_datetime(df_m)
                result_json["m"] = df_m.iloc[0].to_dict()

                # 2️⃣ 撈明細表（乾淨統一呼叫）
                detail_tables = {
                    "mes": "ooutputlist_mes_d",
                    "wspgalaxy": "ooutputlist_wspgalaxy_d",
                    "wspdevice": "ooutputlist_wspdevice_d",
                    "emd": "ooutputlist_emd_d"
                }

                for key, table in detail_tables.items():
                    result_json[key] = self._fetch_detail(conn, table, sn)

        except Exception as e:
            return {"data": result_json}

        ExecutionTime = time.time() - startTime
        return {"data": result_json}

