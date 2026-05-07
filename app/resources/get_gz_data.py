#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import timedelta
from sqlalchemy import text

import requests
import redis
import json
import re

from collections import defaultdict


# In[ ]:


import logging
logger = logging.getLogger(__name__)  # 取得和主程式共用的 logger


# In[2]:


def get_GZ_data(stime,etime,variable_Name,servers):   
    
    def parse_variable_indicator(row):
        var_list = row['VARIABLE_NAME'].strip('[]').split(';')
        ind_list = row['INDICATOR'].strip('[]').split(';')
        return dict(zip(var_list, map(float, ind_list))) 

    srv_YFYAIUPSVISA1 = servers['YFYAIUPSVISA1']
    with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:
        sql =   """
            SELECT * 
            FROM
            (            
                SELECT 
                    [PIECEID]
                    ,[METROLOGYNAME]
                    ,[TIMETAG]
                    ,[INDICATOR]
                    ,[VARIABLE_NAME]
                    ,CASE WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT' THEN METROLOGY.FIELD_2
                    WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP' THEN METROLOGY.FIELD_3
                    WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT-2SIGMA' THEN METROLOGY.FIELD_4
                    WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP-2SIGMA' THEN METROLOGY.FIELD_5
                    END AS METROLOGY
                FROM [AIUPS_CDB].[dbo].[RESULT] WITH (NOLOCK)
                LEFT JOIN (SELECT [CONTEXTID],[FIELD_2],[FIELD_3],[FIELD_4],[FIELD_5] FROM [AI41_AVM2_RESULT_PIVOT].[dbo].[METROLOGY]) [METROLOGY] 
                ON [METROLOGY].CONTEXTID = [RESULT].PIECEID
                WHERE TIMETAG >='"""+ str(stime) +"""' AND TIMETAG <='"""+ str(etime) +"""'
            ) t
            WHERE METROLOGY IS NOT NULL
            OPTION (RECOMPILE);
        """       
        query = conn.execute(text(sql))  
        df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query]) 

    if df_YFYAIUPSVISA1.empty:
        return pd.DataFrame()
    else:
        df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1.drop_duplicates().reset_index(drop=True)
        
        df_YFYAIUPSVISA1["INDICATOR"] = df_YFYAIUPSVISA1["INDICATOR"].astype(str).str.replace("非數值", "99999")
        # 使用 apply 處理每一行
        df_YFYAIUPSVISA1['VARIABLE_INDICATOR'] = df_YFYAIUPSVISA1.apply(parse_variable_indicator, axis=1)
        
        try:
            srv_GZ = servers['GZ'] 
            with srv_GZ['create_engine'][0].connect() as conn:   
                
#                 conn.execute(text("SET statement_timeout = 20000"))  # 設定 20 秒查詢超時
                
                sql =   """
                SELECT piece_id,target,isi,spec
                  FROM public.indicator_result WITH (NOLOCK)
                  WHERE piece_id IN (""" + str(list(df_YFYAIUPSVISA1['PIECEID'].unique()))[1:-1]  + """)

                """         
                query = conn.execute(text(sql))  
                df_indicator_result = pd.DataFrame([dict(i) for i in query])  
            
            df_result = df_YFYAIUPSVISA1.merge(df_indicator_result,left_on=['PIECEID','METROLOGYNAME'], right_on=['piece_id','target'])            .drop(['INDICATOR','VARIABLE_NAME','piece_id','target'],axis=1)    

            df_result = df_result.loc[:,['PIECEID','TIMETAG','METROLOGYNAME','METROLOGY','VARIABLE_INDICATOR','isi','spec']]

            def check_out_of_spec(row):
                variable_values = row['VARIABLE_INDICATOR']  # 實際值
                spec_limits = row['spec']  # 規格
                result = {}

                for var, value in variable_values.items():
                    if var in spec_limits:
                        usl = spec_limits[var]['usl']
                        lsl = spec_limits[var]['lsl']
                        result[var] = 1 if (value > usl or value < lsl) else 0
                    else:
                        result[var] = 0  # 如果 spec 中沒有這個變數，預設不超標

                return result

            # 應用到整個 DataFrame
            df_result['Out_of_Spec'] = df_result.apply(check_out_of_spec, axis=1)

            df_result = df_result.sort_values(by=['TIMETAG','METROLOGYNAME']).reset_index(drop=True)
        except:
            
            df_result = df_YFYAIUPSVISA1.copy()        
            
            df_result['isi'] = None
            df_result['spec'] = None
            df_result = df_result.loc[:,['PIECEID','TIMETAG','METROLOGYNAME','METROLOGY','VARIABLE_INDICATOR','isi','spec']]
            df_result['Out_of_Spec'] = None            
            
            df_result = df_result.sort_values(by=['TIMETAG','METROLOGYNAME']).reset_index(drop=True)            
            
            return df_result

    return df_result


# In[3]:


class GET_GZ_data:
    def __init__(self, servers, redis_client):
        self.servers = servers 
        self.redis = redis_client
        
    def fetch(self, stime: str, etime: str, variable_Name: str, MachineName: str):    
        if not stime:
            return {'success': False, 'message': 'Missing Stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing Etime parameter'}        
        if not variable_Name:
            return {'success': False, 'message': 'Missing VariableName parameter'} 
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'} 
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}        

        start_time = time.time()

        if variable_Name in ['METROLOGY-COATINGWEIGHT','METROLOGY-COATINGWEIGHT-2SIGMA','METROLOGY-P21-MO1-SP','METROLOGY-P21-MO1-SP-2SIGMA']:            
            
            redis_key = f"GZ:{MachineName}:{variable_Name}:{stime}:{etime}"

            try:
                cached = self.redis.get(redis_key)
                if cached:
                    logging.info(f"Redis hit: {redis_key}")
                    return json.loads(cached)
            except Exception as e:
                logging.warning(f"Redis get failed: {e}")            

            srv_YFYAIUPSVISA1 = self.servers['YFYAIUPSVISA1']
            with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:                
                sql =   """
                    SELECT * 
                    FROM
                    (            
                        SELECT 
                            [PIECEID]
                            ,[METROLOGYNAME]
                            ,[TIMETAG]
                            ,[INDICATOR]
                            ,[VARIABLE_NAME]
                            ,[NN]
                            ,CASE WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT' THEN METROLOGY.FIELD_2
                            WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP' THEN METROLOGY.FIELD_3
                            WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT-2SIGMA' THEN METROLOGY.FIELD_4
                            WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP-2SIGMA' THEN METROLOGY.FIELD_5
                            END AS METROLOGY
                        FROM [AIUPS_CDB].[dbo].[RESULT]
                        LEFT JOIN (SELECT [CONTEXTID],[FIELD_2],[FIELD_3],[FIELD_4],[FIELD_5] FROM [AI41_AVM2_RESULT_PIVOT].[dbo].[METROLOGY]) [METROLOGY] 
                        ON [METROLOGY].CONTEXTID = [RESULT].PIECEID
                        WHERE TIMETAG >='"""+ str(stime) +"""' AND TIMETAG <='"""+ str(etime) +"""'
                    ) t
                    --WHERE METROLOGY IS NOT NULL 
                    OPTION (RECOMPILE);
                """       
                query = conn.execute(text(sql))  
                df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query]) 

            if df_YFYAIUPSVISA1.empty:
                df_result = pd.DataFrame()
            else:
                df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1.drop_duplicates().reset_index(drop=True)

                df_result_NN = df_YFYAIUPSVISA1.copy()
                df_result = df_YFYAIUPSVISA1[~df_YFYAIUPSVISA1['METROLOGY'].isna()].reset_index(drop=True).copy()
#                     df_result = df_YFYAIUPSVISA1.copy()       

                # 20250619 新增四個驗收標準
                df_result['ERROR'] = df_result['NN'].astype(float) - df_result['METROLOGY'].astype(float)
                df_grouped = df_result.groupby('METROLOGYNAME').agg({
                    'PIECEID': ['count'],
                    'METROLOGY': ['std'],
                    'ERROR': [
                        lambda x: abs(x.quantile(0.95)),  # 95% 百分位數
                        lambda x: np.mean(np.abs(x))  # MAE
                    ]
                })

                # 重新命名欄位名稱
                df_grouped.columns = ['PIECEID_count', 'METROLOGY_std', 'ERROR_95th', 'ERROR_MAE']

                df_grouped['METROLOGY_two_std'] = df_grouped['METROLOGY_std'] * 2
                df_grouped = df_grouped.loc[:,['PIECEID_count', 'METROLOGY_std', 'ERROR_MAE','METROLOGY_two_std', 'ERROR_95th']].reset_index()
                df_grouped['Accept'] = np.where(
                    (df_grouped['ERROR_MAE'] < df_grouped['METROLOGY_std']) & (df_grouped['ERROR_95th'] < df_grouped['METROLOGY_two_std']),
                    "OK",
                    "NG"
                )                    

                df_result['isi'] = None
                df_result['spec'] = None
                df_result['VARIABLE_INDICATOR'] = None
                df_result = df_result.loc[:,['PIECEID','TIMETAG','METROLOGYNAME','NN','METROLOGY','VARIABLE_INDICATOR','isi','spec']]
                df_result_NN['NN'] = df_result_NN['NN'].astype(float)
                df_result['Out_of_Spec'] = None            

                df_result = df_result.sort_values(by=['TIMETAG','METROLOGYNAME']).reset_index(drop=True)                   
        else:
            df_result = get_GZ_data(stime,etime,variable_Name,self.servers)

        elapsed = time.time() - start_time
        logging.info(f"get_GZ_data time for {variable_Name}: {elapsed:.2f} seconds")

        if not df_result.empty:

            if variable_Name in ['METROLOGY-COATINGWEIGHT','METROLOGY-COATINGWEIGHT-2SIGMA','METROLOGY-P21-MO1-SP','METROLOGY-P21-MO1-SP-2SIGMA']:
                df_result = df_result[df_result['METROLOGYNAME']==variable_Name]
                df_result_NN = df_result_NN[df_result_NN['METROLOGYNAME']==variable_Name].sort_values(by=['TIMETAG']).reset_index(drop=True)

                df_result[variable_Name] = np.array(df_result['METROLOGY'])

                try:
                    start_time = time.time()

                    srv_SRVAIUPSPRA1 = self.servers['SRVAIUPSPRA1'] 
                    with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
                        conn.execute(text("SET LOCK_TIMEOUT 2000"))  # 設定 20 秒超時

                        sql =   """
                            SELECT TOP (1000) [CONTEXTID],[FIELD_34]
                              FROM [AIUPS].[dbo].[PROCESS_BCDRY]
                              WHERE CONTEXTID IN (""" + str(list(df_result['PIECEID'].unique()))[1:-1]  + """)

                        """         

                        query = conn.execute(text(sql))  
                        df_P21_MO1_SP_Setting = pd.DataFrame([dict(i) for i in query])

                    elapsed = time.time() - start_time
                    logging.info(f"df_P21_MO1_SP_Setting sql query time for {variable_Name}: {elapsed:.2f} seconds")                            
                except Exception as e:
                    df_P21_MO1_SP_Setting = pd.DataFrame()

                start_time = time.time()

                if not df_P21_MO1_SP_Setting.empty:
                    df_P21_MO1_SP_Setting['FIELD_34_UCL'] = np.array(df_P21_MO1_SP_Setting['FIELD_34'].astype(float))+3
                    df_P21_MO1_SP_Setting['FIELD_34_LCL'] = np.maximum(np.array(df_P21_MO1_SP_Setting['FIELD_34'].astype(float))-3, 0)                    
                else:
                    df_P21_MO1_SP_Setting['FIELD_34_UCL'] = 0
                    df_P21_MO1_SP_Setting['FIELD_34_LCL'] = 0

                if variable_Name == 'METROLOGY-COATINGWEIGHT':
                    df_result[variable_Name + '_UCL'] = 10
                    df_result[variable_Name + '_LCL'] = 0
                elif variable_Name == 'METROLOGY-COATINGWEIGHT-2SIGMA':
                    df_result[variable_Name + '_UCL'] = 10
                    df_result[variable_Name + '_LCL'] = 0          
                elif variable_Name == 'METROLOGY-P21-MO1-SP':
                    if not df_P21_MO1_SP_Setting.empty: 
                        df_result = df_result.merge(df_P21_MO1_SP_Setting,left_on='PIECEID',right_on='CONTEXTID',how='left')
                        df_result['METROLOGY-P21-MO1-SP_UCL'] = df_result['FIELD_34_UCL']
                        df_result['METROLOGY-P21-MO1-SP_LCL'] = df_result['FIELD_34_LCL']
                        df_result.drop(['CONTEXTID','FIELD_34','FIELD_34_UCL','FIELD_34_LCL'],axis = 1,inplace=True)
                    else:
                        df_result['METROLOGY-P21-MO1-SP_UCL'] = 0
                        df_result['METROLOGY-P21-MO1-SP_LCL'] = 0
                elif variable_Name == 'METROLOGY-P21-MO1-SP-2SIGMA':
                    df_result[variable_Name + '_UCL'] = 3
                    df_result[variable_Name + '_LCL'] = 0           
                else:
                    pass


                # 組裝目標數據
                target_series = {
                    "name": variable_Name,
                    "style": {"color": "#008C01"},
                    "show": True,
                    "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name])]
                }

                # 組裝目標數據
                target_series_NN = {
                    "name": "NN",
                    "style": {"color": "#008C01"},
                    "show": True,
                    "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result_NN["TIMETAG"], df_result_NN["NN"])]
                }                    

                target_series_UCL = {
                    "name": 'UCL',
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name+'_UCL'])]
                }        

                target_series_LCL = {
                    "name": 'LCL',
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name+'_LCL'])]
                }

                # 構造驗收標準的Json
                df_grouped_JSON = {
                    "name": "Acceptance criteria",
                    "points": [{"METROLOGYNAME": str(METROLOGYNAME), 
                                "METROLOGY_std": METROLOGY_std, "ERROR_MAE": ERROR_MAE, 
                                "METROLOGY_two_std": METROLOGY_two_std, "ERROR_95th": ERROR_95th, "Accept": Accept
                               } for METROLOGYNAME, METROLOGY_std, ERROR_MAE, 
                               METROLOGY_two_std, ERROR_95th, Accept in zip(df_grouped["METROLOGYNAME"],df_grouped["METROLOGY_std"],df_grouped["ERROR_MAE"],
                                                                           df_grouped["METROLOGY_two_std"],df_grouped["ERROR_95th"],df_grouped["Accept"])]
                }                                      

                # 建立最終 JSON 結構
                result_json = {
                    "metadata": {
                        "name": "主要數據1",
                        "source": "API_A",
                        "description": "包含目標數據與管制線（UCL、LCL）的數據"
                    },
                    "data": [{
                        "yaxis": "目標\n(單位)",
                        "series": [target_series,target_series_NN,target_series_UCL,target_series_LCL]
                    },{
                        "yaxis": "驗收標準",
                        "series": [df_grouped_JSON]
                    }]
                }
                
                elapsed = time.time() - start_time
                logging.info(f"prepross time for {variable_Name}: {elapsed:.2f} seconds")   
                
                try:
                    # 快取 10 分鐘（可自行調整）
                    self.redis.setex(
                        redis_key,
                        60,
                        json.dumps(result_json, ensure_ascii=False)
                    )
                    logging.info(f"Redis set: {redis_key}")
                except Exception as e:
                    logging.warning(f"Redis set failed: {e}")                

                return result_json                  

            else:
                start_time = time.time()

                df_result = df_result[df_result['METROLOGYNAME']=='METROLOGY-COATINGWEIGHT']

                drop_idx = df_result[
                    df_result["VARIABLE_INDICATOR"].apply(
                        lambda x: list(x.values())[0] == 99999 if isinstance(x, dict) and x else False
                    )
                ].index
                df_result = df_result.drop(index=drop_idx).reset_index(drop=True)

                df_result[variable_Name] = df_result["VARIABLE_INDICATOR"].apply(lambda x: x.get(variable_Name, None))
                
                df_result[variable_Name + '_UCL'] = df_result["spec"].apply(
                    lambda x: x.get(variable_Name, {}).get("usl", None) if isinstance(x, dict) else None
                )
                df_result[variable_Name + '_LCL'] = df_result["spec"].apply(
                    lambda x: x.get(variable_Name, {}).get("lsl", None) if isinstance(x, dict) else None
                )                    

                # 組裝目標數據
                target_series = {
                    "name": variable_Name,
                    "style": {"color": "#008C01"},
                    "show": True,
                    "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name])]
                }

                target_series_UCL = {
                    "name": 'UCL',
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name+'_UCL'])]
                }        

                target_series_LCL = {
                    "name": 'LCL',
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name+'_LCL'])]
                }                

                # 建立最終 JSON 結構
                result_json = {
                    "metadata": {
                        "name": "主要數據1",
                        "source": "API_A",
                        "description": "包含目標數據與管制線（UCL、LCL）的數據"
                    },
                    "data": [{
                        "yaxis": "目標\n(單位)",
                        "series": [target_series,target_series_UCL,target_series_LCL]
                    }]
                }

                elapsed = time.time() - start_time
                logging.info(f"prepross time for {variable_Name}: {elapsed:.2f} seconds")

                return result_json
        else:
        # 20250318 如果先知沒有提供結果 則需要自己組裝資料 STDB
            if variable_Name in ['METROLOGY-COATINGWEIGHT','METROLOGY-COATINGWEIGHT-2SIGMA','METROLOGY-P21-MO1-SP','METROLOGY-P21-MO1-SP-2SIGMA']:
                try:
                    start_time = time.time()

                    srv_SRVAIUPSPRA1 = self.servers['SRVAIUPSPRA1'] 
                    with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
                        conn.execute(text("SET LOCK_TIMEOUT 2000"))  # 設定 20 秒超時

                        sql =   """
                            SELECT [CONTEXTID]
                                  ,[TIMETAG]
                                  ,[FIELD_2]
                                  ,[FIELD_3]
                                  ,[FIELD_4]
                                  ,[FIELD_5]
                              FROM [AIUPS].[dbo].[METROLOGY]
                              where CONTEXTID like '%AVG'
                              AND TIMETAG >='"""+str(stime)+"""' AND TIMETAG <='"""+str(etime)+"""'
                              order by TIMETAG
                        """         

                        query = conn.execute(text(sql))  
                        df_result = pd.DataFrame([dict(i) for i in query])        

                    with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
                        conn.execute(text("SET LOCK_TIMEOUT 2000"))  # 設定 20 秒超時

                        sql =   """
                            SELECT [CONTEXTID],[FIELD_34]
                              FROM [AIUPS].[dbo].[PROCESS_BCDRY]
                              WHERE 1=1
                              AND TIMETAG >='"""+str(stime)+"""' 
                              AND TIMETAG <='"""+str(etime)+"""'
                              AND CONTEXTID like '%AVG'
                              ORDER BY TIMETAG
                        """         

                        query = conn.execute(text(sql))  
                        df_P21_MO1_SP_Setting = pd.DataFrame([dict(i) for i in query])
                except Exception as e:
                    df_P21_MO1_SP_Setting = pd.DataFrame()

                elapsed = time.time() - start_time
                logging.info(f"STDB sql query time for {variable_Name}: {elapsed:.2f} seconds") 


                start_time = time.time()

                if not df_result.empty:
                    if not df_P21_MO1_SP_Setting.empty:
                        df_P21_MO1_SP_Setting['FIELD_34_UCL'] = np.array(df_P21_MO1_SP_Setting['FIELD_34'].astype(float))+3
                        df_P21_MO1_SP_Setting['FIELD_34_LCL'] = np.maximum(np.array(df_P21_MO1_SP_Setting['FIELD_34'].astype(float))-3, 0)                    
                    else:
                        df_P21_MO1_SP_Setting['FIELD_34_UCL'] = 0
                        df_P21_MO1_SP_Setting['FIELD_34_LCL'] = 0

                    if variable_Name == 'METROLOGY-COATINGWEIGHT':
                        df_result[variable_Name] = df_result['FIELD_2']
                        df_result[variable_Name + '_UCL'] = 10
                        df_result[variable_Name + '_LCL'] = 0
                    elif variable_Name == 'METROLOGY-COATINGWEIGHT-2SIGMA':
                        df_result[variable_Name] = df_result['FIELD_4']
                        df_result[variable_Name + '_UCL'] = 10
                        df_result[variable_Name + '_LCL'] = 0
                    elif variable_Name == 'METROLOGY-P21-MO1-SP':
                        df_result[variable_Name] = df_result['FIELD_3']
                        if not df_P21_MO1_SP_Setting.empty: 
                            df_result = df_result.merge(df_P21_MO1_SP_Setting,left_on='CONTEXTID',right_on='CONTEXTID',how='left')
                            df_result['METROLOGY-P21-MO1-SP_UCL'] = df_result['FIELD_34_UCL']
                            df_result['METROLOGY-P21-MO1-SP_LCL'] = df_result['FIELD_34_LCL']
                            df_result.drop(['CONTEXTID','FIELD_34','FIELD_34_UCL','FIELD_34_LCL'],axis = 1,inplace=True)
                        else:
                            df_result['METROLOGY-P21-MO1-SP_UCL'] = 0
                            df_result['METROLOGY-P21-MO1-SP_LCL'] = 0
                    elif variable_Name == 'METROLOGY-P21-MO1-SP-2SIGMA':
                        df_result[variable_Name] = df_result['FIELD_5']
                        df_result[variable_Name + '_UCL'] = 3
                        df_result[variable_Name + '_LCL'] = 0           
                    else:
                        pass

                    df_result[variable_Name] = df_result[variable_Name].replace({np.nan: None})
                    df_result[variable_Name + '_UCL'] = df_result[variable_Name + '_UCL'].replace({np.nan: None})
                    df_result[variable_Name + '_LCL'] = df_result[variable_Name + '_LCL'].replace({np.nan: None})                    

                    # 組裝目標數據
                    target_series = {
                        "name": variable_Name,
                        "style": {"color": "#008C01"},
                        "show": True,
                        "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name])]
                    }

                    target_series_NN = {
                        "name": 'NN',
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": []
                    }                        

                    target_series_UCL = {
                        "name": 'UCL',
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name+'_UCL'])]
                    }        

                    target_series_LCL = {
                        "name": 'LCL',
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v} for t, v in zip(df_result["TIMETAG"], df_result[variable_Name+'_LCL'])]
                    }
                else:
                    # 組裝目標數據
                    target_series = {
                        "name": variable_Name,
                        "style": {"color": "#008C01"},
                        "show": True,
                        "points": []
                    }

                    target_series_NN = {
                        "name": 'NN',
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": []
                    }                        

                    target_series_UCL = {
                        "name": 'UCL',
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": []
                    }        

                    target_series_LCL = {
                        "name": 'LCL',
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": []
                    } 

                # 建立最終 JSON 結構
                result_json = {
                    "metadata": {
                        "name": "主要數據1",
                        "source": "API_A",
                        "description": "包含目標數據與管制線（UCL、LCL）的數據"
                    },
                    "data": [{
                        "yaxis": "目標\n(單位)",
                        "series": [target_series,target_series_NN,target_series_UCL,target_series_LCL]
                    },{
                        "yaxis": "驗收標準",
                        "series": []
                    }]
                }

                elapsed = time.time() - start_time
                logging.info(f"STDB preprocessing time for {variable_Name}: {elapsed:.2f} seconds")                     

                return result_json                        

            else:
                # 組裝目標數據
                target_series = {
                    "name": variable_Name,
                    "style": {"color": "#008C01"},
                    "show": True,
                    "points": []
                }

                target_series_NN = {
                    "name": 'NN',
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": []
                }                    

                target_series_UCL = {
                    "name": 'UCL',
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": []
                }        

                target_series_LCL = {
                    "name": 'LCL',
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": []
                }                

            # 建立最終 JSON 結構
            result_json = {
                "metadata": {
                    "name": "主要數據1",
                    "source": "API_A",
                    "description": "包含目標數據與管制線（UCL、LCL）的數據"
                },
                "data": [{
                    "yaxis": "目標\n(單位)",
                    "series": [target_series,target_series_NN,target_series_UCL,target_series_LCL]
                },{
                    "yaxis": "驗收標準",
                    "series": []
                }]
            }

            return result_json


# In[ ]:


class GET_GZ_data_feature_importance:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, variable_Name: str, MachineName: str): 
        startTime = time.time() 
        
        if not stime:
            return {'success': False, 'message': 'Missing Stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing Etime parameter'}        
        if not variable_Name:
            return {'success': False, 'message': 'Missing VariableName parameter'} 
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'} 
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}        
        
        if variable_Name in ['METROLOGY-COATINGWEIGHT','METROLOGY-COATINGWEIGHT-2SIGMA','METROLOGY-P21-MO1-SP','METROLOGY-P21-MO1-SP-2SIGMA']:            
            select_stime = stime
            select_etime = etime

            srv_SRVAD1 = self.servers['SRVAD1']
            with srv_SRVAD1['create_engine'][0].connect() as conn:
                sql =   """
                    SELECT TOP 1
                        relno,
                        dateadd(MINUTE,-[btime],[pdate]) AS stime,
                        pdate, 
                        bdate,
                        ptype,
                        gramg
                    FROM [SRVAD1].[AMIS].[dbo].[amreel] reel
                    WHERE 1=1
                    AND mname='21' 
                    AND pdate >= '"""+ str(select_etime) +"""'
                    order by pdate                          
                """
                query = conn.execute(text(sql))  
                df_SRVAD1 = pd.DataFrame([dict(i) for i in query])

            if df_SRVAD1.empty:
                with srv_SRVAD1['create_engine'][0].connect() as conn:
                    sql =   """
                        SELECT 
                                relno,
                                pdate AS stime,
                                GETDATE() AS pdate, 
                                bdate,
                                ptype,
                                gramg
                        FROM
                        (
                            SELECT TOP 1
                                relno,
                                dateadd(MINUTE,-[btime],[pdate]) AS stime,
                                pdate, 
                                bdate,
                                ptype,
                                gramg
                            FROM [SRVAD1].[AMIS].[dbo].[amreel] reel
                            WHERE 1=1
                            AND mname='21' 
                            order by pdate desc
                        ) m
                    """
                    query = conn.execute(text(sql))  
                    df_SRVAD1 = pd.DataFrame([dict(i) for i in query])   

            all_stime = df_SRVAD1.loc[0,'stime']
            all_etime = df_SRVAD1.loc[0,'pdate']                

            srv_YFYAIUPSVISA1 = self.servers['YFYAIUPSVISA1']
            with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:
                sql =   """
                    SELECT * 
                    FROM
                    (            
                        SELECT 
                            [PIECEID]
                            ,[METROLOGYNAME]
                            ,[TIMETAG]
                            ,[INDICATOR]
                            ,[VARIABLE_NAME]
                            ,CASE WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT' THEN METROLOGY.FIELD_2
                            WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP' THEN METROLOGY.FIELD_3
                            WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT-2SIGMA' THEN METROLOGY.FIELD_4
                            WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP-2SIGMA' THEN METROLOGY.FIELD_5
                            END AS METROLOGY
                        FROM [AIUPS_CDB].[dbo].[RESULT]
                        LEFT JOIN (SELECT [CONTEXTID],[FIELD_2],[FIELD_3],[FIELD_4],[FIELD_5] FROM [AI41_AVM2_RESULT_PIVOT].[dbo].[METROLOGY]) [METROLOGY] 
                        ON [METROLOGY].CONTEXTID = [RESULT].PIECEID
                        WHERE TIMETAG >='"""+ str(all_stime) +"""' AND TIMETAG <='"""+ str(all_etime) +"""'
                    ) t
                    WHERE METROLOGY IS NOT NULL   
                    ORDER BY TIMETAG
                    OPTION (RECOMPILE);
                """       
                query = conn.execute(text(sql))  
                df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query])

            if not df_YFYAIUPSVISA1.empty:

                df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1.drop_duplicates().reset_index(drop=True)

                allidlist = list(df_YFYAIUPSVISA1['PIECEID'].unique())

                with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:
                    sql =   """
                        SELECT * 
                        FROM
                        (            
                            SELECT 
                                [PIECEID]
                                ,[METROLOGYNAME]
                                ,[TIMETAG]
                                ,[INDICATOR]
                                ,[VARIABLE_NAME]
                                ,CASE WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT' THEN METROLOGY.FIELD_2
                                WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP' THEN METROLOGY.FIELD_3
                                WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT-2SIGMA' THEN METROLOGY.FIELD_4
                                WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP-2SIGMA' THEN METROLOGY.FIELD_5
                                END AS METROLOGY
                            FROM [AIUPS_CDB].[dbo].[RESULT]
                            LEFT JOIN (SELECT [CONTEXTID],[FIELD_2],[FIELD_3],[FIELD_4],[FIELD_5] FROM [AI41_AVM2_RESULT_PIVOT].[dbo].[METROLOGY]) [METROLOGY] 
                            ON [METROLOGY].CONTEXTID = [RESULT].PIECEID
                            WHERE TIMETAG >='"""+ str(select_stime) +"""' AND TIMETAG <='"""+ str(select_etime) +"""'
                        ) t
                        WHERE METROLOGY IS NOT NULL   
                        ORDER BY TIMETAG
                        OPTION (RECOMPILE);
                    """       
                    query = conn.execute(text(sql))  
                    df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query])

                df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1.drop_duplicates().reset_index(drop=True)

                selectedidlist = list(df_YFYAIUPSVISA1['PIECEID'].unique())

                start_time = time.time()
                try:
                    srv_GZ = self.servers['GZ'] 
                    with srv_GZ['create_engine'][0].connect() as conn:                        
                        sql =   """
                        SELECT model_id,piece_id,target,isi,spec
                          FROM public.indicator_result
                          WHERE piece_id IN (""" + str([list(df_YFYAIUPSVISA1['PIECEID'].unique())[0]])[1:-1]  + """)
                          AND target = '""" + variable_Name + """'
                        """         
                        query = conn.execute(text(sql))  
                        df_indicator_result = pd.DataFrame([dict(i) for i in query])

                    # API 端點
                    url = "http://10.10.24.192:5566/api/Datas/SearchISITop10"

                    # 準備傳送的 JSON 資料
                    payload = {
                        "modelid": df_indicator_result.head(1)['model_id'].item(),
                        "allidlist": allidlist,
                        "breakrange": [],
                        "excludetagrange": [
                            [{"xAxis": "20250216032710_AVG"}, {"xAxis": "20250216041350_AVG"}]
                        ],
                        "metrology": variable_Name,
                        "selectedidlist": selectedidlist
                    }

                    # 設定標頭
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                    try:
                        # 發送請求
                        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout = 300.0)
                        if response.status_code == 200:
                            result = response.json()  # 解析回應 JSON

                        feature_importance = pd.DataFrame({
                            'GZ_ISI': result.get('returndata', None).get('gzscore', None).get('name', None),
                            'O_ISI': result.get('returndata', None).get('isiscore', None).get('name', None),
                            'PY_ISI': result.get('returndata', None).get('pyscore', None).get('name', None),
                            'PY_Corr': result.get('returndata', None).get('pycorrscore', None).get('name', None)
                        })

                        elapsed = time.time() - start_time
                        logging.info(f"GET_GZ_data_feature_importance sql query time is: {elapsed:.2f} seconds")                            

                        # 定義一個函數來處理每個欄位的值，提取')'前的部分
                        def extract_before_parenthesis(text):
                            return re.sub(r'\)[^)]*', '', text)

                        # 對每個欄位應用此函數
                        feature_importance = feature_importance.applymap(extract_before_parenthesis)
                        feature_importance = feature_importance.apply(lambda col: col.str.replace('(', ''))

                        target_series_GZ_ISI = {
                            "name": "GZ_ISI",
                            "points": [{"value": v} for v in feature_importance["GZ_ISI"]]
                        }
                        target_series_O_ISI = {
                            "name": "O_ISI",
                            "points": [{"value": v} for v in feature_importance["O_ISI"]]
                        }
                        target_series_PY_ISI = {
                            "name": "PY_ISI",
                            "points": [{"value": v} for v in feature_importance["PY_ISI"]]
                        }
                        target_series_PY_Corr = {
                            "name": "PY_Corr",
                            "points": [{"value": v} for v in feature_importance["PY_Corr"]]
                        }                            
                    except Exception as e:
                        target_series_GZ_ISI = {
                            "name": "GZ_ISI",
                            "points": []
                        }
                        target_series_O_ISI = {
                            "name": "O_ISI",
                            "points": []
                        }
                        target_series_PY_ISI = {
                            "name": "PY_ISI",
                            "points": []
                        }
                        target_series_PY_Corr = {
                            "name": "PY_Corr",
                            "points": []
                        }     
                except:
                    target_series_GZ_ISI = {
                        "name": "GZ_ISI",
                        "points": []
                    }
                    target_series_O_ISI = {
                        "name": "O_ISI",
                        "points": []
                    }
                    target_series_PY_ISI = {
                        "name": "PY_ISI",
                        "points": []
                    }
                    target_series_PY_Corr = {
                        "name": "PY_Corr",
                        "points": []     
                    }

            else:
                target_series_GZ_ISI = {
                    "name": "GZ_ISI",
                    "points": []
                }
                target_series_O_ISI = {
                    "name": "O_ISI",
                    "points": []
                }
                target_series_PY_ISI = {
                    "name": "PY_ISI",
                    "points": []
                }
                target_series_PY_Corr = {
                    "name": "PY_Corr",
                    "points": []
                }                    


            # 建立最終 JSON 結構
            result_json = {
                "metadata": {
                    "name": "主要數據2",
                    "source": "API_A",
                    "description": "四個類別的重要參數"
                },
                "data": [{
                    "series": [target_series_GZ_ISI,target_series_O_ISI,target_series_PY_ISI,target_series_PY_Corr]
                }]
            }
            ExecutionTime = time.time() - startTime

            return result_json                  

        else: 
            return {'success': False, 'message': 'error VariableName parameter'}


# In[ ]:


class GET_GZ_data_gramg_speed:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, stime: str, etime: str, variable_Name: str, MachineName: str):  
        startTime = time.time()
        if not stime:
            return {'success': False, 'message': 'Missing Stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing Etime parameter'}        
        if not variable_Name:
            return {'success': False, 'message': 'Missing VariableName parameter'} 
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'} 
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}           

        start_time = time.time()

        try:
            srv_SRVAIUPSPRA1 = self.servers['SRVAIUPSPRA1'] 
            with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
                conn.execute(text("SET LOCK_TIMEOUT 2000"))  # 設定 20 秒超時

                sql =   """
                    SELECT [CONTEXTID]
                          ,[TIMETAG]
                          ,[FIELD_2]
                      FROM [AIUPS].[dbo].[PROCESS_BCDRY]
                      where 1=1
                      AND TIMETAG >='"""+str(stime)+"""' 
                      AND TIMETAG <='"""+str(etime)+"""'
                      AND CONTEXTID like '%AVG'
                      order by TIMETAG
                """         

                query = conn.execute(text(sql))  
                df_PROCESS_BCDRY = pd.DataFrame([dict(i) for i in query])        

            with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
                conn.execute(text("SET LOCK_TIMEOUT 2000"))  # 設定 20 秒超時

                sql =   """
                    SELECT TOP (1000) [CONTEXTID]
                          ,[TIMETAG]
                          ,[FIELD_27]
                      FROM [AIUPS].[dbo].[PROCESS_SHAP]
                      WHERE 1=1
                      AND CONTEXTID like '%AVG'
                      AND TIMETAG >='"""+str(stime)+"""' 
                      AND TIMETAG <='"""+str(etime)+"""'

                      ORDER BY TIMETAG
                """         

                query = conn.execute(text(sql))  
                df_PROCESS_SHAP = pd.DataFrame([dict(i) for i in query])
        except Exception as e:
            df_PROCESS_BCDRY = pd.DataFrame()
            df_PROCESS_SHAP = pd.DataFrame()

        elapsed = time.time() - start_time
        logging.info(f"GET_GZ_data_gramg_speed sql query time is: {elapsed:.2f} seconds") 

        start_time = time.time()
        
        # 初始化基礎結構
        target_series_gramg = {"name": 'gramg', "style": {"color": "#0000ff"}, "show": True, "points": []}
        target_series_speed = {"name": 'speed', "style": {"color": "#ff0000"}, "show": True, "points": []}        

        if (not df_PROCESS_BCDRY.empty) or (not df_PROCESS_SHAP.empty):

            df_PROCESS_BCDRY.columns = ['CONTEXTID','TIMETAG','gramg']
            df_PROCESS_SHAP.columns = ['CONTEXTID','TIMETAG','speed'] 

            df_result = df_PROCESS_BCDRY.merge(df_PROCESS_SHAP.loc[:,['CONTEXTID','speed']], on='CONTEXTID',how='left')            
            df_result["TIMETAG"] = pd.to_datetime(df_result["CONTEXTID"].str[:14], format="%Y%m%d%H%M%S")   
            df_result = df_result.sort_values(by='TIMETAG').reset_index(drop=True)

            df_result['gramg'] = df_result['gramg'].replace({np.nan: None})
            df_result['speed'] = df_result['speed'].replace({np.nan: None})
            
            # 關鍵優化：將時間轉換為 API 字串格式 (向量化 dt.strftime)
            df_result['time_str'] = df_result['TIMETAG'].dt.strftime("%Y-%m-%d %H:%M:%S")      
            
            # 5. 使用 to_dict('records') 快速生成 points 列表
            # 這樣寫比手寫 for zip 快 50-100 倍
            target_series_gramg["points"] = (
                df_result.rename(columns={'time_str': 'time', 'gramg': 'value'})
                [['time', 'value']]
                .to_dict(orient='records')
            )

            target_series_speed["points"] = (
                df_result.rename(columns={'time_str': 'time', 'speed': 'value'})
                [['time', 'value']]
                .to_dict(orient='records')
            )            

        # 建立最終 JSON 結構
        result_json = {
            "metadata": {
                "name": "主要數據1",
                "source": "API_A",
                "description": "基重與車速"
            },
            "data": [{
                "yaxis": "目標\n(單位)",
                "series": [target_series_gramg,target_series_speed]
            }]
        }

        elapsed = time.time() - start_time
        logging.info(f"GET_GZ_data_gramg_speed calculate time is: {elapsed:.2f} seconds")            

        ExecutionTime = time.time() - startTime

        return result_json                


# In[ ]:


class GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, variable_Name: str, MachineName: str): 
        startTime = time.time()
        if not stime:
            return {'success': False, 'message': 'Missing Stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing Etime parameter'}        
        if not variable_Name:
            return {'success': False, 'message': 'Missing VariableName parameter'} 
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'}    

        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}         
            
        stime_dt = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M:%S')  # 轉換成 datetime 物件
        stime_diff_ten_minutes = stime_dt - timedelta(minutes=10)  # 扣除 10 分鐘
        stime_diff_ten_minutes = stime_diff_ten_minutes.strftime('%Y-%m-%d %H:%M:%S')  # 轉回字串

        srv_SRVAIUPSPRA1 = self.servers['SRVAIUPSPRA1']
        with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
            sql =   """
                SELECT [CONTEXTID] 
                      ,[TIMETAG]
                      ,[MACHINE_RUN] 
                      ,[SHEET_BREAK_SIGNAL]
                      ,[SP_SCANNER_RUNNING]
                      ,[REEL_SCANNER_RUNNING]                          
                  FROM [AIUPS].[dbo].[STATUS]
                  WHERE TIMETAG >='"""+ str(stime_diff_ten_minutes) +"""' AND TIMETAG <='"""+ str(etime) +"""'
                  and CONTEXTID like '%AVG'
                  order by TIMETAG

            """
            query = conn.execute(text(sql))  
            df_STATUS = pd.DataFrame([dict(i) for i in query])

        if df_STATUS.empty:
            # 構造停車的 JSON 結構
            Stop_data = {
                "id": "停車",
                "ranges": [],
                "style": {"color": "rgba(173, 216, 230, 0.5)"}
            }            

            # 生成「停車後 10 分鐘」的 JSON
            Stop_after_10min_data = {
                "id": "停車後10分鐘",
                "ranges": [],
                "style": {"color": "rgba(255, 140, 0, 0.5)"}  # 設定不同顏色
            }                            

            # 構造標準化的 JSON 結構
            Scanner_Standardization_data = {
                "id": "標準化",
                "ranges": [],
                "style": {"color": "rgba(173, 216, 230, 0.5)"}
            }                                 
        else:            

            df_STATUS['MACHINE_RUN_SHEET_BREAK_SIGNAL'] = (df_STATUS['MACHINE_RUN'].astype(float).astype(bool)) | (df_STATUS['SHEET_BREAK_SIGNAL'].astype(float).astype(bool))

            # 找出產品變更的索引位置
            df_STATUS['MACHINE_RUN_SHEET_BREAK_SIGNAL_change'] = df_STATUS['MACHINE_RUN_SHEET_BREAK_SIGNAL'] != df_STATUS['MACHINE_RUN_SHEET_BREAK_SIGNAL'].shift()

            # 生成每段產品的 group id
            df_STATUS['group'] = df_STATUS['MACHINE_RUN_SHEET_BREAK_SIGNAL_change'].cumsum()

            df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data = df_STATUS.groupby('group').agg(
                            Status=('MACHINE_RUN_SHEET_BREAK_SIGNAL', 'first'),
                            start=('TIMETAG', 'first'),
                            end=('TIMETAG', 'last')
                        ).reset_index(drop=True)                        

            df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data = df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data[df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data['Status']==True].reset_index(drop=True)

            df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data['end_ten_minutes'] =             pd.to_datetime(df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data['end']) + pd.Timedelta(minutes=10)            

            # 構造停車的 JSON 結構
            Stop_data = {
                "id": "停車",
                "ranges": [{"start": str(start), "end": str(end)} for start, end in zip(df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data["start"], df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data["end"])],
                "style": {"color": "rgba(173, 216, 230, 0.5)"}
            }            

            # 生成「停車後 10 分鐘」的 JSON
            Stop_after_10min_data = {
                "id": "停車後10分鐘",
                "ranges": [{"start": str(start), "end": str(end)} for start, end in zip(df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data["end"], df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data["end_ten_minutes"])],
                "style": {"color": "rgba(255, 140, 0, 0.5)"}  # 設定不同顏色
            }            

            df_STATUS['Standardization'] = np.where(
                (df_STATUS['SP_SCANNER_RUNNING']=='4.0') | (df_STATUS['REEL_SCANNER_RUNNING']=='4.0'),
                '標準化','非標準化'
            )

            # 找出產品變更的索引位置
            df_STATUS['Standardization_change'] = df_STATUS['Standardization'] != df_STATUS['Standardization'].shift()

            # 生成每段產品的 group id
            df_STATUS['group'] = df_STATUS['Standardization_change'].cumsum()

            # 計算每段產品的開始與結束時間
            df_Scanner_Standardization_data = df_STATUS.groupby('group').agg(
                Status=('Standardization', 'first'),
                start=('TIMETAG', 'first'),
                end=('TIMETAG', 'last')
            ).reset_index(drop=True)            

            df_Scanner_Standardization_data = df_Scanner_Standardization_data[df_Scanner_Standardization_data['Status']=='標準化'].reset_index(drop=True)

            # 構造標準化的 JSON 結構
            Scanner_Standardization_data = {
                "id": "標準化",
                "ranges": [{"start": str(start), "end": str(end)} for start, end in zip(df_Scanner_Standardization_data["start"], df_Scanner_Standardization_data["end"])],
                "style": {"color": "rgba(173, 216, 230, 0.5)"}
            }                        

        # 20250220 新增車速劇烈變化
        srv_YFYAIUPSVISA1 = self.servers['YFYAIUPSVISA1']
        with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:            
            sql =   """
                SELECT * 
                FROM
                (            
                    SELECT 
                        [PIECEID]
                        ,[METROLOGYNAME]
                        ,[TIMETAG]
                        ,[INDICATOR]
                        ,[VARIABLE_NAME]
                        ,CASE WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT' THEN METROLOGY.FIELD_2
                        WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP' THEN METROLOGY.FIELD_3
                        WHEN [METROLOGYNAME] = 'METROLOGY-COATINGWEIGHT-2SIGMA' THEN METROLOGY.FIELD_4
                        WHEN [METROLOGYNAME] = 'METROLOGY-P21-MO1-SP-2SIGMA' THEN METROLOGY.FIELD_5
                        END AS METROLOGY
                    FROM [AIUPS_CDB].[dbo].[RESULT]
                    LEFT JOIN (SELECT [CONTEXTID],[FIELD_2],[FIELD_3],[FIELD_4],[FIELD_5] FROM [AI41_AVM2_RESULT_PIVOT].[dbo].[METROLOGY]) [METROLOGY] 
                    ON [METROLOGY].CONTEXTID = [RESULT].PIECEID
                    WHERE TIMETAG >='"""+ str(stime) +"""' AND TIMETAG <='"""+ str(etime) +"""'
                    AND METROLOGYNAME = '"""+ str(variable_Name) +"""'
                ) t
                WHERE METROLOGY IS NOT NULL
                OPTION (RECOMPILE);
            """       
            query = conn.execute(text(sql))  
            df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query])

        elapsed = time.time() - startTime
        logging.info(f"GET_GZ_data_gramg_speed calculate time is: {elapsed:.2f} seconds")                

        if df_YFYAIUPSVISA1.empty:
            # 轉換為 API 需要的格式
            excludetag_data = {
                "id": "除外資料",
                "ranges": [],
                "style": {"color": "rgba(173, 216, 230, 0.5)"}
            }                        
        else:
            df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1.drop_duplicates().reset_index(drop=True)

            start_time = time.time()

            try:
                srv_GZ = self.servers['GZ']
                with srv_GZ['create_engine'][0].connect() as conn:                    
                    sql =   """
                    SELECT model_id,piece_id,target,isi,spec
                      FROM public.indicator_result
                      WHERE piece_id IN (""" + str([list(df_YFYAIUPSVISA1['PIECEID'].unique())[0]])[1:-1]  + """)
                      AND target = '""" + variable_Name + """'

                    """         
                    query = conn.execute(text(sql))  
                    df_indicator_result = pd.DataFrame([dict(i) for i in query]) 

                # API 端點
                url = "http://10.10.24.192:5566/api/Datas/SearchMetrologyOutSpec"

                # 準備傳送的 JSON 資料
                payload = {
                    "modelid": df_indicator_result.head(1)['model_id'].item(),
                    "idlist": list(df_YFYAIUPSVISA1['PIECEID'].unique()),
                    'sdatetime': stime,
                    'edatetime': etime,
                    'target': variable_Name
                }

                # 設定標頭
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }

                try:
                    # 發送請求
                    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout = 30.0)

                    # 檢查回應
                    if response.status_code == 200:
                        result = response.json()  # 解析回應 JSON

                    api_result = result.get('returndata', None).get('excludetag', None)

                    # 解析 API 回傳的時間資料
                    time_ranges = []
                    for item in api_result['excludetag']:
                        start_str = item[0]['xAxis'].replace('_AVG', '')  # 移除 "_AVG"
                        end_str = item[1]['xAxis'].replace('_AVG', '')

                        # 轉換為 datetime 格式
                        start_dt = datetime.datetime.strptime(start_str, "%Y%m%d%H%M%S")
                        end_dt = datetime.datetime.strptime(end_str, "%Y%m%d%H%M%S")

                        # 存入列表
                        time_ranges.append({"start": start_dt, "end": end_dt})

                    # 建立 DataFrame
                    df_excludetag_data = pd.DataFrame(time_ranges)
                    # 20250324 憲毅新增
                    for i in range(0,len(df_excludetag_data)):
                        for j in range(0,len(df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data)):
                            if (df_excludetag_data.loc[i,'start'] > df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data.loc[j,'end'])                            & (df_excludetag_data.loc[i,'start'] < df_MACHINE_RUN_SHEET_BREAK_SIGNAL_change_data.loc[j,'end_ten_minutes']):
                                df_excludetag_data = df_excludetag_data.drop(i)
                                break

                    df_excludetag_data = df_excludetag_data.reset_index(drop=True)                          
                except:
                    df_excludetag_data = pd.DataFrame()
            except:
                df_excludetag_data = pd.DataFrame()

            elapsed = time.time() - start_time
            logging.info(f"GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung sql query time is: {elapsed:.2f} seconds")                 

            if df_excludetag_data.empty:
                # 轉換為 API 需要的格式
                excludetag_data = {
                    "id": "除外資料",
                    "ranges": [],
                    "style": {"color": "rgba(173, 216, 230, 0.5)"}
                }                        
            else:
                # 轉換為 API 需要的格式
                excludetag_data = {
                    "id": "除外資料",
                    "ranges": [{"start": str(start), "end": str(end)} for start, end in zip(df_excludetag_data["start"], df_excludetag_data["end"])],
                    "style": {"color": "rgba(173, 216, 230, 0.5)"}
                }        

        # 最終 JSON 結構
        result_json = {
            "metadata": {
                "name": "時間區間數據",
                "source": "API_E",
                "description": "斷紙和停車的區間"
            },
            "data": [Stop_data,Stop_after_10min_data,Scanner_Standardization_data,excludetag_data]
        }                 

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


class GET_GZ_data_Outputlist:
    def __init__(self, servers, redis_client):
        self.servers = servers
        self.redis = redis_client
    
    def fetch(self, MachineName: str):
        startTime = time.time()     
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'}    
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}  
        
        # ✅ Redis Key（這裡很重要）
        redis_key = f"GZ:Outputlist:{MachineName}"

        # =========================
        # ✅ 1. 先查 Redis
        # =========================
        try:
            cached = self.redis.get(redis_key)
            if cached:
                logging.info(f"Redis hit: {redis_key}")
                return json.loads(cached)
        except Exception as e:
            logging.warning(f"Redis get failed: {e}")

        # =========================
        # ✅ 2. 查 DB
        # =========================        
        
        srv_SRVMSDBA1 = self.servers['SRVMSDBA1'] 
        with srv_SRVMSDBA1['create_engine'][0].connect() as conn:            
            sql =   """
                SELECT [Name]
                      ,[Cname]
                      ,[Code]
                      ,[MachineCode]
                      ,[Category]
                      ,[IsEnabled]
                      ,[IsDeprecated]
                  FROM [AIMSFTAO].[dbo].[ooutputlist_m]
                  where [System] = 'PM21抄紙機'
            """
            query = conn.execute(text(sql))  
            df_Outputlist = pd.DataFrame([dict(i) for i in query])

        elapsed = time.time() - startTime
        logging.info(f"GET_GZ_data_Outputlist sql query time is: {elapsed:.2f} seconds")

        start_time = time.time()

        df_Outputlist.drop(['MachineCode','Category','IsEnabled','IsDeprecated'],axis=1,inplace=True)

        # 構造停車的 JSON 結構
        Outputlist_JSON = {
            "name": "Outputlist",
            "points": [{"Code": str(Code), "Name": str(Name), "Cname": str(Cname)} for Code, Name, Cname in zip(df_Outputlist["Code"],df_Outputlist["Name"],df_Outputlist["Cname"])],
        }

        # 最終 JSON 結構
        result_json = {
            "metadata": {
                "name": "Outputlist",
                "source": "API_E",
                "description": "PM21_Outputlist"
            },
            "data": [Outputlist_JSON]
        }                 
        
        try:
            # 建議 TTL：10分鐘 ~ 1小時（看你資料更新頻率）
            self.redis.setex(
                redis_key,
                86400,  # 秒（1小時）
                json.dumps(result_json)
            )
            logging.info(f"Redis set: {redis_key}")
        except Exception as e:
            logging.warning(f"Redis set failed: {e}")        

        elapsed = time.time() - startTime
        logging.info(f"GET_GZ_data_Outputlist calculate time is: {elapsed:.2f} seconds")            

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


class GET_GZ_data_out_spec_count:
    def __init__(self, servers):
        self.servers = servers
    
    def fetch(self, stime: str, etime: str, variable_Name: str, MachineName: str):  
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing Stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing Etime parameter'}        
        if not variable_Name:
            return {'success': False, 'message': 'Missing VariableName parameter'} 
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'}    
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'} 
        
        def parse_variable_indicator(row):
            var_list = row['VARIABLE_NAME'].strip('[]').split(';')
            ind_list = row['INDICATOR'].strip('[]').split(';')
            return dict(zip(var_list, map(float, ind_list))) 

        srv_YFYAIUPSVISA1 = self.servers['YFYAIUPSVISA1'] 
        with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:             
            sql =   """  
                SELECT 
                    [PIECEID]
                    ,[METROLOGYNAME]
                    ,[TIMETAG]
                    ,[INDICATOR]
                    ,[VARIABLE_NAME]
                FROM [AIUPS_CDB].[dbo].[RESULT]
                WHERE TIMETAG >='"""+ str(stime) +"""' AND TIMETAG <='"""+ str(etime) +"""'       
            """       
            query = conn.execute(text(sql))  
            df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query]) 

        if df_YFYAIUPSVISA1.empty:
            df_result = pd.DataFrame()
        else:    
            df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1.drop_duplicates().reset_index(drop=True)

            df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1[df_YFYAIUPSVISA1['INDICATOR'] != '[]'].reset_index(drop=True)

            df_YFYAIUPSVISA1["INDICATOR"] = df_YFYAIUPSVISA1["INDICATOR"].astype(str).str.replace("非數值", "99999")
            # 使用 apply 處理每一行
            df_YFYAIUPSVISA1['VARIABLE_INDICATOR'] = df_YFYAIUPSVISA1.apply(parse_variable_indicator, axis=1)                

            try:
                srv_GZ = self.servers['GZ'] 
                with srv_GZ['create_engine'][0].connect() as conn:                    
#                         conn.execute(text("SET statement_timeout = 20000"))  # 設定 20 秒查詢超時

                    sql =   """
                    SELECT piece_id,target,isi,spec
                      FROM public.indicator_result
                      WHERE piece_id IN (""" + str(list(df_YFYAIUPSVISA1['PIECEID'].unique()))[1:-1]  + """)

                    """         
                    query = conn.execute(text(sql))  
                    df_indicator_result = pd.DataFrame([dict(i) for i in query])  

                df_result = df_YFYAIUPSVISA1.merge(df_indicator_result,left_on=['PIECEID','METROLOGYNAME'], right_on=['piece_id','target'])                .drop(['INDICATOR','VARIABLE_NAME','piece_id','target'],axis=1)    

                df_result = df_result.loc[:,['PIECEID','TIMETAG','METROLOGYNAME','VARIABLE_INDICATOR','isi','spec']]

#                     drop_idx = df_result[df_result["VARIABLE_INDICATOR"].apply(lambda x: x.get('ACDRY-ABB_B87', None) == 99999)].index
                drop_idx = df_result[
                    df_result["VARIABLE_INDICATOR"].apply(
                        lambda x: list(x.values())[0] == 99999 if isinstance(x, dict) and x else False
                    )
                ].index                        
                df_result = df_result.drop(index=drop_idx).reset_index(drop=True)                    

                def check_out_of_spec(row):                          
                    variable_values = row['VARIABLE_INDICATOR']  # 實際值
                    spec_limits = row['spec']  # 規格
                    result = {}

                    for var, value in variable_values.items():                             
                        if var in spec_limits:
                            usl = spec_limits[var]['usl']
                            lsl = spec_limits[var]['lsl']
                            result[var] = 1 if (value > usl or value < lsl) else 0
                        else:
                            result[var] = 0  # 如果 spec 中沒有這個變數，預設不超標

                    return result

                # 應用到整個 DataFrame
                df_result['Out_of_Spec'] = df_result.apply(check_out_of_spec, axis=1)

                df_result = df_result.sort_values(by=['TIMETAG','METROLOGYNAME']).reset_index(drop=True)

            except:

                df_result = df_YFYAIUPSVISA1.copy()        

                df_result['isi'] = None
                df_result['spec'] = None
                df_result = df_result.loc[:,['PIECEID','TIMETAG','METROLOGYNAME','VARIABLE_INDICATOR','isi','spec']]
                df_result['Out_of_Spec'] = None            

                df_result = df_result.sort_values(by=['TIMETAG','METROLOGYNAME']).reset_index(drop=True)

        if not df_result.empty:

            df_result = df_result[df_result['METROLOGYNAME']==variable_Name]       

#                 df_result["Out_of_Spec_Variables"] = df_result.apply(
#                     lambda row: {k: row["VARIABLE_INDICATOR"].get(k, None) for k, v in row["Out_of_Spec"].items() if v == 1},
#                     axis=1
#                 )

            df_result["Out_of_Spec_Variables"] = df_result.apply(
                lambda row: {k: row["VARIABLE_INDICATOR"].get(k, None) for k, v in (row["Out_of_Spec"] or {}).items() if v == 1}
                if isinstance(row["Out_of_Spec"], dict) else {},
                axis=1
            )                

            def merge_dicts(dict_list):
                merged = defaultdict(list)
                for d in dict_list:
                    for k, v in d.items():
                        merged[k].append(v)  # 把相同 key 的值合併成 list
                return {k: v for k, v in merged.items()}  # 轉回普通字典

            df_merged = df_result.groupby("PIECEID")["Out_of_Spec_Variables"].agg(lambda x: merge_dicts(x)).reset_index()

            # 建立統計變數次數與最小/最大值的字典
            var_stats = defaultdict(lambda: {"count": 0, "min": float("inf"), "max": float("-inf")})

            # 遍歷 df_merged，統計變數的出現次數與 min/max
            for _, row in df_merged.iterrows():
                for var, values in row["Out_of_Spec_Variables"].items():
                    var_stats[var]["count"] += 1  # 出現次數
                    var_stats[var]["min"] = min(var_stats[var]["min"], *values)  # 計算最小值
                    var_stats[var]["max"] = max(var_stats[var]["max"], *values)  # 計算最大值

            df_var_stats = pd.DataFrame([
                {"Variable": var, "Count": stats["count"], "Min": stats["min"], "Max": stats["max"]}
                for var, stats in var_stats.items()
            ])
            if not df_var_stats.empty:
                df_var_stats = df_var_stats.sort_values(by=['Count','Variable'],ascending = [False,True]).reset_index(drop=True)

            for i in list(df_result['VARIABLE_INDICATOR'].head(1).item()):
                df_result[i] = df_result["VARIABLE_INDICATOR"].apply(lambda x: x.get(i, None))                
                df_result[i + '_UCL'] = df_result["spec"].apply(
                    lambda x: x.get(i, {}).get("usl", None) if isinstance(x, dict) else None
                )
                df_result[i + '_LCL'] = df_result["spec"].apply(
                    lambda x: x.get(i, {}).get("lsl", None) if isinstance(x, dict) else None
                )     
                df_result[i] = df_result[i].replace({np.nan: None})
                df_result[i + '_UCL'] = df_result[i + '_UCL'].replace({np.nan: None})
                df_result[i + '_LCL'] = df_result[i + '_LCL'].replace({np.nan: None})    
                df_result[i] = df_result[i].replace({99999: None})
                df_result[i + '_UCL'] = df_result[i + '_UCL'].replace({99999: None})
                df_result[i + '_LCL'] = df_result[i + '_LCL'].replace({99999: None})  
                df_result[i] = df_result[i].replace({999999999: None})
                df_result[i + '_UCL'] = df_result[i + '_UCL'].replace({999999999: None})
                df_result[i + '_LCL'] = df_result[i + '_LCL'].replace({999999999: None})                     

            if not df_var_stats.empty:
                variable_names = list(df_var_stats['Variable']) +                                [var for var in df_result['VARIABLE_INDICATOR'].head(1).item() if var not in df_var_stats['Variable'].values]

                # 存放所有變數的 result_json
                all_results = []

                df_columns = set(df_result.columns)
                # 過濾出 df_result 裡有的變數
                valid_variable_names = [var for var in variable_names if var in df_columns]

                for var_name in valid_variable_names:
                    # 取得違規次數
                    exceeded_count = df_var_stats.loc[df_var_stats['Variable'] == var_name, 'Count'].values
                    exceeded_count = exceeded_count[0].item() if len(exceeded_count) > 0 else 0

                    # 目標數據
                    target_series = {
                        "name": var_name,
                        "style": {"color": "#0000ff"},
                        "show": True,
                        "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v}
                                   for t, v in zip(df_result["TIMETAG"], df_result[var_name])]
                    }

                    # UCL 上管制線
                    target_series_UCL = {
                        "name": "UCL",
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v}
                                   for t, v in zip(df_result["TIMETAG"], df_result[var_name + "_UCL"])]
                    }

                    # LCL 下管制線
                    target_series_LCL = {
                        "name": "LCL",
                        "style": {"color": "#ff0000"},
                        "show": True,
                        "points": [{"time": t.strftime("%Y-%m-%d %H:%M:%S"), "value": v}
                                   for t, v in zip(df_result["TIMETAG"], df_result[var_name + "_LCL"])]
                    }

                    # 建立單一變數的 JSON 結構
                    result_json = {
                        "metadata": {
                            "name": f"數據-{var_name}",
                            "source": "API_A",
                            "description": f"變數 {var_name} 包含目標數據與管制線（UCL、LCL）"
                        },
                        "data": [{
                            "yaxis": "目標\n(單位)",
                            "out_spec_count": exceeded_count,  # 該變數的違規次數
                            "series": [target_series, target_series_UCL, target_series_LCL]
                        }]
                    }
                    # 將該變數的 JSON 存入總列表
                    all_results.append(result_json)

                # 最終的 JSON 結構（包含所有變數的 result_json）
                final_result_json = {"all_data": all_results}

                ExecutionTime = time.time() - startTime

                return final_result_json
            else:
                # 存放所有變數的 result_json
                all_results = []

                var_name = ''

                # 目標數據
                target_series = {
                    "name": var_name,
                    "style": {"color": "#0000ff"},
                    "show": True,
                    "points": []
                }

                # UCL 上管制線
                target_series_UCL = {
                    "name": "UCL",
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": []
                }

                # LCL 下管制線
                target_series_LCL = {
                    "name": "LCL",
                    "style": {"color": "#ff0000"},
                    "show": True,
                    "points": []
                }                

                # 建立單一變數的 JSON 結構
                result_json = {
                    "metadata": {
                        "name": "數據",
                        "source": "API_A",
                        "description": "變數包含目標數據與管制線（UCL、LCL）"
                    },
                    "data": [{
                        "yaxis": "目標\n(單位)",
                        "out_spec_count": 0,  # 該變數的違規次數
                        "series": [target_series, target_series_UCL, target_series_LCL]
                    }]
                }

                # 將該變數的 JSON 存入總列表
                all_results.append(result_json)

                # 最終的 JSON 結構（包含所有變數的 result_json）
                final_result_json = {"all_data": all_results}

                ExecutionTime = time.time() - startTime

                return final_result_json

        else:
            # 存放所有變數的 result_json
            all_results = []

            var_name = ''

            # 目標數據
            target_series = {
                "name": var_name,
                "style": {"color": "#0000ff"},
                "show": True,
                "points": []
            }

            # UCL 上管制線
            target_series_UCL = {
                "name": "UCL",
                "style": {"color": "#ff0000"},
                "show": True,
                "points": []
            }

            # LCL 下管制線
            target_series_LCL = {
                "name": "LCL",
                "style": {"color": "#ff0000"},
                "show": True,
                "points": []
            }                

            # 建立單一變數的 JSON 結構
            result_json = {
                "metadata": {
                    "name": f"數據",
                    "source": "API_A",
                    "description": f"變數包含目標數據與管制線（UCL、LCL）"
                },
                "data": [{
                    "yaxis": "目標\n(單位)",
                    "out_spec_count": 0,  # 該變數的違規次數
                    "series": [target_series, target_series_UCL, target_series_LCL]
                }]
            }

            # 將該變數的 JSON 存入總列表
            all_results.append(result_json)

            # 最終的 JSON 結構（包含所有變數的 result_json）
            final_result_json = {"all_data": all_results}

            ExecutionTime = time.time() - startTime

            return final_result_json


# In[ ]:


class GET_GZ_data_out_spec_count_reel:
    def __init__(self, servers):
        self.servers = servers
        
    def fetch(self, dFrom: str, MachineName: str):
        startTime = time.time()
        
        if not dFrom:
            return {'success': False, 'message': 'Missing dFrom parameter'}
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'}   
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}
        
        srv_SRVMSDBA2 = self.servers['SRVMSDBA2']
        with srv_SRVMSDBA2['create_engine'][0].connect() as conn:
            sql = f"""
                SELECT [relno]
                      ,[stime]
                      ,[pdate]
                      ,[bdate]
                      ,[ptype]
                      ,[gramg]
                      ,[out_spec_count]
                FROM [GREENZONE].[dbo].[out_spec_count]
                WHERE bdate ='{dFrom}'
            """
            query = conn.execute(text(sql))
            df_result = pd.DataFrame([dict(i) for i in query])

        if not df_result.empty:
            result_json = [{"reelNo": t, "count": v} for t, v in zip(df_result["relno"], df_result["out_spec_count"])]
        else:
            result_json = []

        ExecutionTime = time.time() - startTime
        return result_json        


# In[ ]:


class GET_GZ_data_user_favorite:
    def __init__(self, servers):
        self.servers = servers
    
    def fetch(self, MachineName: str, Isfavorite: str):  
        startTime = time.time()
        
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'} 
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}         
      
        try:
            srv_GZ = self.servers['GZ'] 
            with srv_GZ['create_engine'][0].connect() as conn:                
                sql =   """
                SELECT *
                  FROM public.favoritesensor

                """         
                query = conn.execute(text(sql))  
                df_favoritesensor = pd.DataFrame([dict(i) for i in query]) 


            srv_SRVAIUPSPRA1 = self.servers['SRVAIUPSPRA1'] 
            with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
                sql =   """
                    SELECT Code
                    FROM
                    (
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_ACDRY] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_BCDRY] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_COATER] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_FORMULA] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_MEDIC] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_NETDRY] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_PAPER_SUBSTRATE] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_PRESS] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_PRESSDRY] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_ROLL] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_SHAP] UNION ALL
                    SELECT [VARIABLENAME],REPLACE(DEFTABLE,'PROCESS_','') + '-' + VARIABLENAME AS Code FROM [AIUPS].[dbo].[PROCESSDEF_SPEED_INFO]
                    ) t
                    WHERE VARIABLENAME != 'STEP'
                """         
                query = conn.execute(text(sql))  
                df_PROCESSDEF = pd.DataFrame([dict(i) for i in query])     

                df_PROCESSDEF_merge = df_PROCESSDEF.merge(df_favoritesensor,left_on='Code',right_on='sensor',how ='left')
                df_PROCESSDEF_merge["favorite"] = df_PROCESSDEF_merge["sensor"].notna().astype(int)
                df_PROCESSDEF_merge.drop('sensor',axis = 1,inplace = True)


            srv_YFYAIUPSVISA1 = self.servers['YFYAIUPSVISA1'] 
            with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:                    
                sql =   """

                        SELECT TOP 1
                            [PIECEID]
                            ,[METROLOGYNAME]
                            ,[TIMETAG]
                            ,[INDICATOR]
                            ,[VARIABLE_NAME]
                        FROM [AIUPS_CDB].[dbo].[RESULT]
                        ORDER BY TIMETAG DESC

                """       
                query = conn.execute(text(sql))  
                df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query])

                df_YFYAIUPSVISA1 = df_YFYAIUPSVISA1.drop_duplicates().reset_index(drop=True)

                df_greenZoneSensor = pd.DataFrame(df_YFYAIUPSVISA1.loc[0,'VARIABLE_NAME'].strip("[]").split(";"), columns=["Variable_Name"])

                df_PROCESSDEF_merge = df_PROCESSDEF_merge.merge(df_greenZoneSensor,left_on='Code',right_on='Variable_Name',how ='left')
                df_PROCESSDEF_merge["GreenZone"] = df_PROCESSDEF_merge["Variable_Name"].notna().astype(int)
                df_PROCESSDEF_merge.drop('Variable_Name',axis = 1,inplace = True)                    

                # 用 request.args 取得 GET 參數
                try:
                    if Isfavorite is not None:  # 確保有值才轉換
                        Isfavorite = int(Isfavorite)  # 轉換為整數
                        if Isfavorite == 1:
                            df_PROCESSDEF_merge = df_PROCESSDEF_merge[df_PROCESSDEF_merge['favorite'] == 1].reset_index(drop=True)
                        elif Isfavorite == 0:
                            df_PROCESSDEF_merge = df_PROCESSDEF_merge[df_PROCESSDEF_merge['favorite'] == 0].reset_index(drop=True)
                except ValueError:  # 捕捉轉換錯誤
                    pass  

            # 建立 JSON 結構
            result_json = {
                "data": [
                    {
                        "Code": row["Code"],
                        "favorite": row["favorite"],
                        "greenzone": row["GreenZone"]
                    }
                    for _, row in df_PROCESSDEF_merge.iterrows()
                ]
            }   

        except:
            df_PROCESSDEF_merge = pd.DataFrame()



        # 建立 JSON 結構
        result_json = {
            "data": [
                {
                    "Code": row["Code"],
                    "favorite": row["favorite"],
                    "greenzone": row["GreenZone"]
                }
                for _, row in df_PROCESSDEF_merge.iterrows()
            ]
        }   


        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


class GET_GZ_data_diff_data:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, variable_Name: str, MachineName: str, ptype: str, smax: str, smin: str, bdate: str, wmax: str, wmin: str): 
        startTime = time.time()
     
        if not variable_Name:
            return {'success': False, 'message': 'Missing VariableName parameter'} 
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'}          
        if not ptype:
            return {'success': False, 'message': 'Missing ptype parameter'}           
        if not smax:
            return {'success': False, 'message': 'Missing smax parameter'}        
        if not smin:
            return {'success': False, 'message': 'Missing smin parameter'}        
        if not bdate:
            return {'success': False, 'message': 'Missing bdate parameter'}        
        if not wmax:
            return {'success': False, 'message': 'Missing wmax parameter'}    
        if not wmin:
            return {'success': False, 'message': 'Missing wmin parameter'}          
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'} 
        
        # API 端點
        url = "http://10.10.24.192:5566/api/Diff/SearchOData"

        # 準備傳送的 JSON 資料  
        payload = {
            "metrology": variable_Name,
            'ptype': ptype,
            'smax': smax,
            'smin': smin,
            'timetag': bdate,
            'wmax': wmax,
            'wmin': wmin
        }            

        # 設定標頭
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # 發送請求
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout = 300.0)

        result = response.json()  # 解析回應 JSON

        for date in result['returndata']:
            result['returndata'][date] = result['returndata'][date]['value']       


        series_list = []
        for variable_Name, data in result["returndata"].items():
            target_series = {
                "date": f"{variable_Name}",  # 標記該 series 為哪一天
                "points": [
                    {"time": f"{variable_Name} 00:00:00", "value": v}  # 確保 Decimal 格式
                    for v in data
                ]
            }

            # 加入 series 列表
            series_list.append(target_series)

        # 建立最終 JSON 結構
        result_json = {
            "metadata": {
                "name": "差異分析數據",
                "source": "API_A",
                "description": "包含差異分析的數據"
            },
            "data": [{
                "yaxis": "目標\n(單位)",
                "series": series_list  # 按天拆分的 series
            }]
        }                                

        return result_json


# In[ ]:


class GET_GZ_data_diff_data_feature_importance:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, variable_Name: str, MachineName: str, ptype: str, smax: str, smin: str,
                    timetag: str, bdate: str, cdate: str, wmax: str, wmin: str): 
        startTime = time.time() 
       
        if not variable_Name:
            return {'success': False, 'message': 'Missing VariableName parameter'} 
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'}          
        if not ptype:
            return {'success': False, 'message': 'Missing ptype parameter'}              
        if not smax:
            return {'success': False, 'message': 'Missing smax parameter'}        
        if not smin:
            return {'success': False, 'message': 'Missing smin parameter'}        
        if not timetag:
            return {'success': False, 'message': 'Missing qdate parameter'}         
        if not bdate:
            return {'success': False, 'message': 'Missing bdate parameter'} 
        if not cdate:
            return {'success': False, 'message': 'Missing cdate parameter'}           
        if not wmax:
            return {'success': False, 'message': 'Missing wmax parameter'}    
        if not wmin:
            return {'success': False, 'message': 'Missing wmin parameter'}          
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'} 
        
        # API 端點
        url = "http://10.10.24.192:5566/api/Diff/RunDiff"

        # 準備傳送的 JSON 資料  
        payload = {
            "btime" : bdate,
            "metrology": variable_Name,
            'keytime': datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S') + '.000',
            "mtime" : cdate,
            'ptype': ptype,
            'smax': smax,
            'smin': smin,
            'timetag': timetag,
            'wmax': wmax,
            'wmin': wmin
        }        

        # 設定標頭
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # 發送請求
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout = 300.0)

        result = response.json()  # 解析回應 JSON

        # 建立所有變數的 series（按日期分開）
        series_list = []
        for variable_Name, data in result["returndata"].items():
#             for variable_Name, data in list(result["returndata"].items())[:12]:
            # 取出 diff 值，並移除日期數據中的 "diff" key
            diff_value = data.get("diff", False)

            target_series = {
                "name": variable_Name,  # 變數名稱提升到外層
                "diff": diff_value,  # diff 變數提升到外層
                "grouppoints": []
            }

            # 取得所有日期並排序
            available_dates = sorted(data.keys())  # 取得現有日期並排序
            available_dates = [d for d in available_dates if d != "diff"]  # 過濾掉 'diff' 鍵

            if available_dates:
                max_date = max(available_dates)  # 找到最大日期
                max_date_dt = datetime.datetime.strptime(max_date, "%Y-%m-%d")  # 轉成 datetime 物件
            else:
                continue  # 如果沒有可用日期，跳過該變數

            # 產生最大日期往回扣 7 天的完整日期列表
            full_date_range = [
                (max_date_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)
            ]
            full_date_range.reverse()  # 讓日期順序從最早到最晚

            # 遍歷完整的日期範圍，補齊缺失的日期
            for date in full_date_range:
                values = list(data.get(date, []))  # 若 date 不存在，則 values 為 []

                target_series_extend = {
                    'date': date,
                    'values': values                        
                }

                target_series["grouppoints"].append(target_series_extend)

            # 加入 series 列表
            series_list.append(target_series)

        # 建立最終 JSON 結構
        result_json = {
            "metadata": {
                "name": "差異分析數據",
                "source": "API_A",
                "description": "包含差異分析的數據"
            },
            "data": [{
                "yaxis": "目標\n(單位)",
                "series": series_list  # 按天拆分的 series
            }]
        }

        return result_json


# In[ ]:


class GET_GZ_data_prediction_status:
    def __init__(self, servers):
        self.servers = servers    
    
    def fetch(self, MachineName: str): 
        startTime = time.time()
        
        if not MachineName:
            return {'success': False, 'message': 'Missing MachineName parameter'}      
        
        if MachineName != '21':
            return {'success': False, 'message': 'error MachineName parameter'}            
   
        try:
            start_time = time.time()

            srv_SRVMSDBA1 = self.servers['SRVMSDBA1'] 
            with srv_SRVMSDBA1['create_engine'][0].connect() as conn:                
                sql =   """
                    SELECT [Area],[Attribute],[FunctionCode],[Value]  FROM [AIMSFTAO].[dbo].[osignal_raw_m]
                      WHERE [Area] = 'FTA_Area_PM21_DCS' AND [Attribute] = 'MachineRun_dcs' AND [FunctionCode] = 'A'

                    UNION ALL

                    SELECT [Area],[Attribute],[FunctionCode],[Value]  FROM [AIMSFTAO].[dbo].[osignal_raw_m]
                    WHERE [Area] = 'FTA_Area_PM21_DCS' AND [Attribute] = 'Sheet_Bk' AND [FunctionCode] = 'A'

                    UNION ALL

                    SELECT [Area],[Attribute],[FunctionCode],[Value]  FROM [AIMSFTAO].[dbo].[osignal_raw_m]
                    WHERE [Area] = 'FTA_Area_PM21_DCS' AND [Attribute] = 'P21_PFC_SP' AND [FunctionCode] = 'A'
                """
                query = conn.execute(text(sql))  
                df_osignal_raw_m = pd.DataFrame([dict(i) for i in query])

            elapsed = time.time() - start_time
            logging.info(f"GET_GZ_data_prediction_status sql query 1 time is: {elapsed:.2f} seconds")                 

            if df_osignal_raw_m[df_osignal_raw_m['Attribute'].isin(['P21_PFC_SP'])]['Value'].astype(int).sum() != 2:

                # 建立 JSON 結構
                result_json = {
                    "success": True,
                    "data": {
                        "Content":{
                            "IsPredicting" : False,
                            "Cause" : "Scanner Error",
                            "Scanner1" : df_osignal_raw_m[df_osignal_raw_m['Attribute'].isin(['P21_PFC_SP'])]['Value'].astype(int).sum().astype(str)
                        }
                    }
                }                   

                return result_json     
            else:
                start_time = time.time()

                srv_YFYAIDBA3 = self.servers['YFYAIDBA3'] 
                with srv_YFYAIDBA3['create_engine'][0].connect() as conn:        
                    sql =   """

                        SELECT TOP 1 [runno],[ptype],[gramg] FROM [AI].[dbo].[amrunt_AI] where status = 'S' and y_mk > (Datepart(year,GETDATE())-10)

                    """       
                    query = conn.execute(text(sql))  
                    df_PM21_W_amrunt_temp = pd.DataFrame([dict(i) for i in query])

                srv_SRVAIUPSPRA1 = self.servers['SRVAIUPSPRA1'] 
                with srv_SRVAIUPSPRA1['create_engine'][0].connect() as conn:
                    sql =   """

                        SELECT TOP (1000) [PTYPE]
                              ,[PTYPE_GROUP_NAME]
                          FROM [AIUPS].[dbo].[DEFTABLE_PTYPE_GROUP_INFO]

                    """       
                    query = conn.execute(text(sql))  
                    df_DEFTABLE_PTYPE_GROUP_INFO = pd.DataFrame([dict(i) for i in query])

                elapsed = time.time() - start_time
                logging.info(f"GET_GZ_data_prediction_status sql query 2 time is: {elapsed:.2f} seconds")                        

                if df_DEFTABLE_PTYPE_GROUP_INFO[df_DEFTABLE_PTYPE_GROUP_INFO['PTYPE'] == df_PM21_W_amrunt_temp['ptype'].item()].empty:

                    # 建立 JSON 結構
                    result_json = {
                        "success": True,
                        "data": {
                            "Content":{
                                "IsPredicting" : False,
                                "Cause" : "Paper Type Error",
                                'PaperCode' : df_PM21_W_amrunt_temp['ptype'].item(),
                                'BaseWeight': str(df_PM21_W_amrunt_temp['gramg'].item())
                            }
                        }
                    }                   

                    return result_json                                   
                else:
                    start_time = time.time()
                    srv_YFYAIUPSVISA1 = self.servers['YFYAIUPSVISA1'] 
                    with srv_YFYAIUPSVISA1['create_engine'][0].connect() as conn:                        
                        sql =   """

                            SELECT TOP 1 DATEDIFF(S,[TIMETAG],GETDATE()) AS Diff_Second FROM [AIUPS_CDB].[dbo].[RESULT] order by NO desc

                        """       
                        query = conn.execute(text(sql))  
                        df_PM21_GZ_LastTime = pd.DataFrame([dict(i) for i in query])

                    elapsed = time.time() - start_time
                    logging.info(f"GET_GZ_data_prediction_status sql query 3 time is: {elapsed:.2f} seconds")                        

                    if df_PM21_GZ_LastTime['Diff_Second'].item() > 60:
                        # 建立 JSON 結構
                        result_json = {
                            "success": True,
                            "data": {
                                "Content":{
                                    "IsPredicting" : False,
                                    "Cause" : "Data 60 Error"
                                }
                            }
                        }                   

                        return result_json
                    else:                        
                        # 建立 JSON 結構
                        result_json = {
                            "success": True,
                            "data": {
                                "Content":{
                                    "IsPredicting" : True
                                }
                            }
                        }       


                        return result_json                            

        except:
            return {'success': False, 'message': 'mssql query error'}

