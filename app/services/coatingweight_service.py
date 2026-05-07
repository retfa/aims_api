#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import logging
from sqlalchemy import text
import pandas as pd
from typing import Tuple, Optional

from resources.CostSheet_Maintenance import CoatingWeight
from schemas.coatingweight_schema import CoatingWeightModel, CoatingWeightUpdateModel

logger = logging.getLogger("MES_API")

class CoatingWeightService:
    def __init__(self, servers, server_name="SRVMSDBA1", redis_client=None):
        self.servers = servers

        if server_name not in self.servers:
            raise RuntimeError(f"Server {server_name} not available")

        self.server_df = self.servers[server_name]
        self.fetcher = CoatingWeight(servers=self.servers)       

    # GET 查詢
    def fetch(self):
        try:
            return self.fetcher.fetch()
        except Exception as e:
            logger.error(f"CoatingWeight fetch error: {e}")
            return {"success": False,"message": str(e)}

    # POST 新增
    def create(self, payload: CoatingWeightModel):
        
        payload_dict = payload.dict()
        
        try:
            with self.server_df['create_engine'][0].begin() as conn:
                fields = ", ".join(payload_dict.keys())
                values = ", ".join(f":{k}" for k in payload_dict.keys())
                sql = f"INSERT INTO [Accounting].[dbo].[CoatingWeight] ({fields}) VALUES ({values})"
                conn.execute(text(sql), payload_dict)
            logger.info(f"Inserted CoatingWeight record: {payload_dict}")
            return {"success": True, "message": "Inserted successfully"}
        except Exception as e:
            logger.error(f"Create CoatingWeight error: {e}")
            return {"success": False, "message": str(e)}

    # PUT 更新
    def update(self, sn: int, payload: CoatingWeightUpdateModel):
        payload_dict = payload.dict(exclude_unset=True)
        if not payload_dict:
            return {"success": False, "message": "No data provided for update"}
        set_clause = ", ".join(f"{k} = :{k}" for k in payload_dict.keys())
        payload_dict["sn"] = sn
        try:
            with self.server_df['create_engine'][0].begin() as conn:
                sql = f"UPDATE [Accounting].[dbo].[CoatingWeight] SET {set_clause} WHERE Sn = :sn"
                conn.execute(text(sql), payload_dict)
            logger.info(f"Updated CoatingWeight Sn={sn} with data: {payload_dict}")
            return {"success": True, "message": "Updated successfully"}
        except Exception as e:
            logger.error(f"Update CoatingWeight error: {e}")
            return {"success": False, "message": str(e)}

    # DELETE 刪除
    def delete(self, sn: int):
        try:
            with self.server_df['create_engine'][0].begin() as conn:
                sql = "DELETE FROM [Accounting].[dbo].[CoatingWeight] WHERE Sn = :sn"
                conn.execute(text(sql), {"sn": sn})
            logger.info(f"Deleted CoatingWeight Sn={sn}")
            return {"success": True, "message": "Deleted successfully"}
        except Exception as e:
            logger.error(f"Delete CoatingWeight error: {e}")
            return {"success": False, "message": str(e)}

