#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from sqlalchemy import text
from resources.WSP import OutputListQuery
from schemas.outputlist_schema import OutputListPostModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class OutputListService:

    def __init__(self, servers,redis_client=None):
        self.fetcher = OutputListQuery(servers=servers)
        self.DB_NAME = OutputListQuery.DB_NAME
        self.SCHEMA = OutputListQuery.SCHEMA
        self.detail_tables = {
            "mes": "ooutputlist_mes_d",
            "wspgalaxy": "ooutputlist_wspgalaxy_d",
            "wspdevice": "ooutputlist_wspdevice_d",
            "emd": "ooutputlist_emd_d"
        }

    def query(self, sn: Optional[int] = None):
        try:
            return self.fetcher.fetch(sn=sn)
        except Exception as e:
            logger.error(f"OutputList query error: {e}")
            return {"success": False, "error": str(e)}

    def upsert(self, data: OutputListPostModel):
        try:
            with self.fetcher.engine.connect() as conn:
                with conn.begin():
                    # 主表
                    m_data = data.m.dict(exclude_none=True)
                    if m_data.get("Sn"):
                        set_clause = ", ".join(f"[{k}] = :{k}" for k in m_data if k != "Sn")
                        if not set_clause:
                            set_clause = "[ModifiedBy] = :ModifiedBy"
                        sql = f"UPDATE [{self.DB_NAME}].[{self.SCHEMA}].[ooutputlist_m] SET {set_clause} WHERE Sn = :Sn"
                        conn.execute(text(sql), m_data)
                    else:
                        keys = ", ".join(f"[{k}]" for k in m_data)
                        values = ", ".join(f":{k}" for k in m_data)
                        sql = f"INSERT INTO [{self.DB_NAME}].[{self.SCHEMA}].[ooutputlist_m] ({keys}) OUTPUT INSERTED.Sn VALUES ({values})"
                        m_data["Sn"] = conn.execute(text(sql), m_data).scalar()

                    master_sn = m_data["Sn"]

                    # 明細表
                    for key, table in self.detail_tables.items():
                        detail_list = getattr(data, key) or [None]
                        for row in detail_list:
                            if row is None:
                                row_data = {"MasterSn": master_sn}
                            else:
                                row_data = row.dict(exclude_none=True)
                                row_data["MasterSn"] = master_sn

                            if self.fetcher._detail_exists(conn, table, master_sn):
                                set_clause = ", ".join(f"[{k}] = :{k}" for k in row_data if k != "MasterSn")
                                if set_clause:
                                    sql = f"UPDATE [{self.DB_NAME}].[{self.SCHEMA}].[{table}] SET {set_clause} WHERE MasterSn = :MasterSn"
                                    conn.execute(text(sql), row_data)
                            else:
                                keys = ", ".join(f"[{k}]" for k in row_data)
                                values = ", ".join(f":{k}" for k in row_data)
                                sql = f"INSERT INTO [{self.DB_NAME}].[{self.SCHEMA}].[{table}] ({keys}) VALUES ({values})"
                                conn.execute(text(sql), row_data)

            return {"success": True, "Sn": master_sn}

        except Exception as e:
            logger.error(f"OutputList upsert error: {e}")
            return {"success": False, "error": str(e)}

    def delete(self, sn: int):
        try:
            with self.fetcher.engine.connect() as conn:
                with conn.begin():
                    for table in self.detail_tables.values():
                        sql = f"DELETE FROM [{self.DB_NAME}].[{self.SCHEMA}].[{table}] WHERE MasterSn = :sn"
                        conn.execute(text(sql), {"sn": sn})

                    sql_m = f"DELETE FROM [{self.DB_NAME}].[{self.SCHEMA}].[ooutputlist_m] WHERE Sn = :sn"
                    result = conn.execute(text(sql_m), {"sn": sn})
                    if result.rowcount == 0:
                        return {"success": False, "error": f"Sn {sn} 不存在"}

            return {"success": True, "Sn": sn}
        except Exception as e:
            logger.error(f"OutputList delete error: {e}")
            return {"success": False, "error": str(e)}

