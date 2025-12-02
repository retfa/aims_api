#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import timedelta
from flask import request, Response
from flask_restful import Resource
from sqlalchemy import text

import requests
import json

from collections import defaultdict


# In[ ]:


import logging
logger = logging.getLogger(__name__)  # 取得和主程式共用的 logger


# In[ ]:


class CurrentTime:
    def __init__(self, servers):
        self.servers = servers       
    
    def fetch(self): 
        startTime = time.time()
       
        try:
            srv_SRVMSDBA2 = self.servers['SRVADA1']
            with srv_SRVMSDBA2['create_engine'][0].connect() as conn:
                sql =   """
                    SELECT GETDATE() AS CurrentTime_time
                """         
                query = conn.execute(text(sql))  
                df_CurrentTime_time = pd.DataFrame([dict(i) for i in query])  

        except:
            df_CurrentTime_time = pd.DataFrame()
                


        # 建立 JSON 結構
        result_json = {
            "data": [
                {
                    "CurrentTime_time": str(row["CurrentTime_time"]),
                }
                for _, row in df_CurrentTime_time.iterrows()
            ]
        }   


        ExecutionTime = time.time() - startTime   

        return result_json

