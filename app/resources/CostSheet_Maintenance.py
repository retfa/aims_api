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


class CoatingWeight:
    def __init__(self, servers):
        self.servers = servers       
    
    def fetch(self): 
        startTime = time.time()
       
        try:
            srv_SRVMSDBA1 = self.servers['SRVMSDBA1']
            with srv_SRVMSDBA1['create_engine'][0].connect() as conn:
                sql =   """
                    SELECT * FROM [Accounting].[dbo].[CoatingWeight]
                """
                query = conn.execute(text(sql))  
                df_CoatingWeight = pd.DataFrame([dict(i) for i in query])  

        except:
            df_CoatingWeight = pd.DataFrame()
                
        # 建立 JSON 結構
        result_json = {
            "data": [
                {
                    "Sn": row["Sn"],
                    "Machine": row["Machine"],
                    "PN2": row["PN2"],
                    "PN4": row["PN4"],
                    "PaperGSM": row["PaperGSM"],
                    "ProductGSM": row["ProductGSM"],
                    "PN4BW": row["PN4BW"],
                    "TypePaperGSM": row["TypePaperGSM"],
                    "TypeProductGSM": row["TypeProductGSM"],
                    "OnMachineCoating": row["OnMachineCoating"],
                    "OffMachineCoating1": row["OffMachineCoating1"],
                    "OffMachineCoating2": row["OffMachineCoating2"],
                    "TotalCoating": row["TotalCoating"],
                    "TypeName": row["TypeName"],
                    "BasePN4": row["BasePN4"],
                    "BasePaperGSM": row["BasePaperGSM"],
                    "bdtm": row["bdtm"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row["bdtm"]) else None,    
                    "buser": row["buser"],                    
                    "mdtm": row["mdtm"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row["mdtm"]) else None,     
                    "muser": row["muser"]
                }
                for _, row in df_CoatingWeight.iterrows()
            ]
        }   

        ExecutionTime = time.time() - startTime   
        
        # 假設 result_json 是你準備回傳的 dict/list
        def clean_json(obj):
            if isinstance(obj, dict):
                return {k: clean_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_json(i) for i in obj]
            elif isinstance(obj, float):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                else:
                    return obj
            else:
                return obj

        result_json = clean_json(result_json)

        return result_json

