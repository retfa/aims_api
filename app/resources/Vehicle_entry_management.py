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


# 車輛進出載重管理


# In[ ]:


class System_time:
    def __init__(self, servers):
        self.servers = servers       
    
    def fetch(self): 
        startTime = time.time()
       
        try:
            srv_SRVADA1 = self.servers['SRVADA1']
            with srv_SRVADA1['create_engine'][0].connect() as conn:
                sql =   """
                    SELECT [Lic_plate]
                          ,[tag_ID]
                          ,[dept]
                          ,[owner]
                          ,[v_type]
                          ,[v_weight]
                          ,[main_load]
                          ,[fuel]
                          ,[memo]
                      FROM [ERP-A].[dbo].[VehicleData]
                """         
                query = conn.execute(text(sql))  
                df_VehicleData = pd.DataFrame([dict(i) for i in query])  

                df_VehicleData['v_weight'] = df_VehicleData['v_weight'].astype(str)

        except:
            df_VehicleData = pd.DataFrame()
                


        # 建立 JSON 結構
        result_json = {
            "data": [
                {
                    "owner": row["owner"],
                }
                for _, row in df_VehicleData.iterrows()
            ]
        }   


        ExecutionTime = time.time() - startTime   

        return result_json


# In[ ]:


class Vehicle_entry_load_management:
    def __init__(self, servers):
        self.servers = servers    
    
    def fetch(self, plate: str):  
        startTime = time.time()
        
        if not plate:          
            try:
                srv_SRVADA1 = self.servers['SRVADA1']
                with srv_SRVADA1['create_engine'][0].connect() as conn:                
                    sql =   """
                        SELECT [Lic_plate]
                              ,[tag_ID]
                              ,[dept]
                              ,[owner]
                              ,[v_type]
                              ,[v_weight]
                              ,[main_load]
                              ,[fuel]
                              ,[memo]
                          FROM [ERP-A].[dbo].[VehicleData]
                    """         
                    query = conn.execute(text(sql))  
                    df_VehicleData = pd.DataFrame([dict(i) for i in query])  
                    
                    df_VehicleData['v_weight'] = df_VehicleData['v_weight'].astype(str)
                    
            except:
                df_VehicleData = pd.DataFrame()
                


            # 建立 JSON 結構
            result_json = {
                "data": [
                    {
                        "Lic_plate": row["Lic_plate"],
                        "tag_ID": row["tag_ID"],
                        "dept": row["dept"],
                        "owner": row["owner"],
                        "v_type": row["v_type"],
                        "v_weight": row["v_weight"],
                        "main_load": row["main_load"],
                        "fuel": row["fuel"],
                        "memo": row["memo"]
                        
                    }
                    for _, row in df_VehicleData.iterrows()
                ]
            }   
                           

            ExecutionTime = time.time() - startTime

            return result_json
        else:
            try:
                srv_SRVADA1 = self.servers['SRVADA1']
                with srv_SRVADA1['create_engine'][0].connect() as conn:
                    sql =   """
                        SELECT [Lic_plate]
                              ,[tag_ID]
                              ,[dept]
                              ,[owner]
                              ,[v_type]
                              ,[v_weight]
                              ,[main_load]
                              ,[fuel]
                              ,[memo]
                          FROM [ERP-A].[dbo].[VehicleData]
                    """         
                    query = conn.execute(text(sql))  
                    df_VehicleData = pd.DataFrame([dict(i) for i in query])  
                    
                    df_VehicleData['v_weight'] = df_VehicleData['v_weight'].astype(str)
                    df_VehicleData = df_VehicleData[df_VehicleData['Lic_plate'].str.contains(plate)]
                    
            except:
                df_VehicleData = pd.DataFrame()
                


            # 建立 JSON 結構
            result_json = {
                "data": [
                    {
                        "Lic_plate": row["Lic_plate"],
                        "tag_ID": row["tag_ID"],
                        "dept": row["dept"],
                        "owner": row["owner"],
                        "v_type": row["v_type"],
                        "v_weight": row["v_weight"],
                        "main_load": row["main_load"],
                        "fuel": row["fuel"],
                        "memo": row["memo"]
                        
                    }
                    for _, row in df_VehicleData.iterrows()
                ]
            }   
                           

            ExecutionTime = time.time() - startTime

            return result_json

