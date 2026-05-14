#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
from utils.db_engine import get_engine
import logging

logger = logging.getLogger("MES_API")


SERVER_LIST = {
    "GZ": "GZ",
    "SRVMSDBA2": "SRVMSDBA2",
    "YFYAIUPSVISA1": "YFYAIUPSVISA1",
    "SRVAIUPSPRA1": "SRVAIUPSPRA1",
    "SRVMSDBA1": "SRVMSDBA1",
    "SRVAD1": "SRVAD1",
    "CHPGTERPDBAAR01": "CHPGTERPDBAAR01",
    "SRVMESDBA1": "SRVMESDBA1",
    "SRVAD2": "SRVAD2",
    "YFYAIDBA3": "YFYAIDBA3",
    "SRVADA1": "SRVADA1",
    "SRVAD6": "SRVAD6",
    "WSP2023R2HTA1": "WSP2023R2HTA1"
}

def load_servers():
    servers = {}
    for name, db_name in SERVER_LIST.items():
        try:
            engine = get_engine(db_name)
            
            # ✅ 測試連線是否可用（測完立刻歸還）
            with engine.connect() as test_conn:
                pass            
            
#             cnx = engine.connect()
            df = pd.DataFrame(
                [[name, db_name, engine]],
                columns=["SERVER", "DB", "create_engine"]
            )
            servers[name] = df
        except Exception as e:
            logger.error(f"連線失敗: SERVER={name}, DB={db_name}, error={e}")
            # 可以選擇繼續下一個資料庫，或直接 raise
            # raise e

    return servers

