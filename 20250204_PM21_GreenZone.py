#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import date,timedelta
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sa_text
from sqlalchemy import text
import sqlalchemy
import warnings
from urllib.parse import quote_plus as urlquote
import threading
import schedule
from schedule import every, repeat, run_pending
import os
import pyodbc
import requests
import json
# from scipy import stats

import statistics

Time_Range = 0.5
Pushback_Seconds = 120
schedule.jobs.clear()
warnings.filterwarnings("ignore")


# In[2]:


import logging
from logging.handlers import TimedRotatingFileHandler

log_filename = 'C:\PythonScheduler\PM21_GreenZone\dist\PM21_GreenZone.log'
handler = TimedRotatingFileHandler(log_filename, when='midnight', backupCount=7, encoding='utf-8')
handler.suffix = '%Y-%m-%d.log'
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


# In[3]:


df_SERVER_GZ = pd.DataFrame([['10.10.24.192','AIUPS']], columns=['SERVER', 'DB'])

df_SERVER_GZ['create_engine'] = ''
df_SERVER_GZ['cnx'] = ''

df_SERVER_SRVMSDBA2 = pd.DataFrame([['SRVMSDBA2','GREENZONE']], columns=['SERVER', 'DB'])

df_SERVER_SRVMSDBA2['create_engine'] = ''
df_SERVER_SRVMSDBA2['cnx'] = ''

df_SERVER_YFYAIUPSVISA1 = pd.DataFrame([['YFYAIUPSVISA1','AIUPS_CDB']], columns=['SERVER', 'DB'])

df_SERVER_YFYAIUPSVISA1['create_engine'] = ''
df_SERVER_YFYAIUPSVISA1['cnx'] = ''

df_SERVER_SRVMSDBA1 = pd.DataFrame([['SRVMSDBA1','AIMSFTAO']], columns=['SERVER', 'DB'])

df_SERVER_SRVMSDBA1['create_engine'] = ''
df_SERVER_SRVMSDBA1['cnx'] = ''


# In[4]:


df_SERVER_GZ['create_engine'][0] = create_engine('postgresql+psycopg2://Aiups_OnlineDB:Aiups_OnlineDB@10.10.24.192:5432/Aiups_OnlineDB')
df_SERVER_GZ['cnx'][0] = df_SERVER_GZ['create_engine'][0].connect()

df_SERVER_SRVMSDBA2['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2022") + df_SERVER_SRVMSDBA2['SERVER'][0] + '/' + df_SERVER_SRVMSDBA2['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True)
df_SERVER_SRVMSDBA2['cnx'][0] = df_SERVER_SRVMSDBA2['create_engine'][0].connect() 

df_SERVER_YFYAIUPSVISA1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2024") + df_SERVER_YFYAIUPSVISA1['SERVER'][0] + '/' + df_SERVER_YFYAIUPSVISA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True)
df_SERVER_YFYAIUPSVISA1['cnx'][0] = df_SERVER_YFYAIUPSVISA1['create_engine'][0].connect() 

df_SERVER_SRVMSDBA1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk@") + df_SERVER_SRVMSDBA1['SERVER'][0] + '/' + df_SERVER_SRVMSDBA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True)
df_SERVER_SRVMSDBA1['cnx'][0] = df_SERVER_SRVMSDBA1['create_engine'][0].connect() 


# In[5]:


def mapping_df_types(df):
    dtypedict = {}
    for i, j in zip(df.columns, df.dtypes):
        if "object" in str(j):
            dtypedict.update({i: sqlalchemy.types.NVARCHAR(length=255)})
        if "float" in str(j):
            dtypedict.update({i: sqlalchemy.types.DECIMAL(precision=18, scale=8)})
        if "int" in str(j):
            dtypedict.update({i: sqlalchemy.types.Integer()})
        if "datetime" in str(j):
            dtypedict.update({i: sqlalchemy.DateTime()})
    return dtypedict


# In[16]:


def get_GZ_data_alarm(stime,etime):

    with df_SERVER_YFYAIUPSVISA1['create_engine'][0].connect() as conn:
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
            ) t
            WHERE METROLOGY IS NOT NULL            
        """       
        query = conn.execute(text(sql))  
        df_YFYAIUPSVISA1 = pd.DataFrame([dict(i) for i in query])
        
    if df_YFYAIUPSVISA1.empty:
        logging.debug('Dataframe YFYAIUPSVISA1 is Empty!')
        return pd.DataFrame(),''     
    else:
        with df_SERVER_GZ['create_engine'][0].connect() as conn:
            sql =   """
            SELECT *
              FROM public.test_tolerance
              WHERE piece_id IN :ids
            """         
            query = conn.execute(text(sql), {"ids": tuple(tuple(df_YFYAIUPSVISA1.PIECEID.unique()))})  
            df_test_tolerance = pd.DataFrame([dict(i) for i in query]) 

            df_test_tolerance = df_test_tolerance[df_test_tolerance['excludetag']==1]

        if len(df_test_tolerance)>0:

            df_YFYAIUPSVISA1[df_YFYAIUPSVISA1['PIECEID'].isin(list(df_test_tolerance.piece_id.unique()))].reset_index(drop=True)        

            def parse_variable_indicator(row):
                var_list = row['VARIABLE_NAME'].strip('[]').split(';')
                ind_list = row['INDICATOR'].strip('[]').split(';')
                return dict(zip(var_list, map(float, ind_list)))

            # 使用 apply 處理每一行
            df_YFYAIUPSVISA1['VARIABLE_INDICATOR'] = df_YFYAIUPSVISA1.apply(parse_variable_indicator, axis=1)   

            with df_SERVER_GZ['create_engine'][0].connect() as conn:
                sql =   """
                SELECT piece_id,target,isi,spec
                  FROM public.indicator_result
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

            df_result["Out_of_Spec_Variables"] = df_result.apply(
                lambda row: {k: row["VARIABLE_INDICATOR"].get(k, None) for k, v in row["Out_of_Spec"].items() if v == 1},
                axis=1
            )

            from collections import defaultdict

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

            # 轉成 DataFrame
            df_var_stats = pd.DataFrame([
                {"Variable": var, "Count": stats["count"], "Min": stats["min"], "Max": stats["max"]}
                for var, stats in var_stats.items()
            ])


            with df_SERVER_GZ['create_engine'][0].connect() as conn:
                sql =   """
                SELECT *
                  FROM public.favoritesensor
                """         
                query = conn.execute(text(sql))  
                df_favoritesensor = pd.DataFrame([dict(i) for i in query])  

            favoritesensor_list = list(df_favoritesensor['sensor']) + ['METROLOGY-COATINGWEIGHT'] + ['METROLOGY-P21-MO1-SP']            

            return df_var_stats[df_var_stats['Variable'].isin(favoritesensor_list)].reset_index(drop=True),df_test_tolerance.head(1)['paper_id'].item()
        else:
            return pd.DataFrame(),''


# In[146]:


logging.debug('--------------------Task Starts--------------------')

startTime_overall = time.time() 

logging.debug('--------------------The Crawling Task Starts--------------------')

startTime = time.time()

with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
    sql =   """
        SELECT * 
        FROM [SRVMSDBA1].[AIMSFTAO].[dbo].[ooutputlist_m]          
    """       
    query = conn.execute(text(sql))  
    df_ooutputlist_m = pd.DataFrame([dict(i) for i in query])

now = datetime.datetime.now()
stime = (now - timedelta(minutes=5) - timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S')
etime = (now - timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S')

# stime = '2025-02-12 09:00:00'
# etime = '2025-02-12 09:05:00'

df_alarm, ptype = get_GZ_data_alarm(stime,etime)

if ptype != '':

    if len(df_alarm[df_alarm['Variable']=='METROLOGY-P21-MO1-SP']['Count'])==0: 
        METROLOGY_P21_MO1_SP = 0.0 
    else: 
        METROLOGY_P21_MO1_SP = df_alarm[df_alarm['Variable']=='METROLOGY-P21-MO1-SP']['Count'].item()

    if len(df_alarm[df_alarm['Variable']=='METROLOGY-COATINGWEIGHT']['Count'])==0: 
        METROLOGY_COATINGWEIGHT = 0.0
    else: 
        METROLOGY_COATINGWEIGHT = df_alarm[df_alarm['Variable']=='METROLOGY-COATINGWEIGHT']['Count'].item()
        
    df_alarm['Code'] = df_alarm['Variable'].str.extract(r'_(\w+)$')
    df_alarm = df_alarm.merge(df_ooutputlist_m.loc[:,['Cname','Code']],on='Code')
    df_alarm['Variable'] = df_alarm['Variable'].str.replace(r'_(\w+)$', r'_(\1)', regex=True) + df_alarm['Cname']        

    alarm_dict = {
        row["Variable"]: {"count": row["Count"], "min": row["Min"], "max": row["Max"]}
        for _, row in df_alarm.iterrows()
    }

    # 加入額外的 key
    final_dict = {
        "塗前水分": METROLOGY_P21_MO1_SP,
        "塗佈量": METROLOGY_COATINGWEIGHT,
        **alarm_dict  # 合併兩個字典
    }

    import uuid

    # 先轉成 JSON 字串，確保中文字不轉 Unicode
    json_content = json.dumps(final_dict, ensure_ascii=False)

    # 建立 DataFrame
    df_alarmcontent = pd.DataFrame({
        'UUID': [str(uuid.uuid4()).upper()],  # 轉換為字串，避免 SQL Server 格式錯誤
        'paperid': [ptype],  
        'startdatetime': [stime],
        'enddatetime': [etime],
        'content': [json_content]  # 這裡存成 JSON 字串
    })

    execute_time = time.time() - startTime
    msg = f"Execution time(s) : {execute_time}"
    logging.debug(msg)

    logging.debug('--------------------The Crawling Task Finish--------------------')   

    logging.debug('----------Insert Task Starts----------')

    startTime = time.time()    

    if df_alarmcontent.empty:
        pass
        logging.debug("df_alarmcontent is empty")
    else:
#         df_alarmcontent['content'] = df_alarmcontent['content'].apply(lambda x: json.dumps(x, ensure_ascii=False))
        with df_SERVER_SRVMSDBA2['create_engine'][0].connect() as conn:
            dtypedict = mapping_df_types(df_alarmcontent)
            df_alarmcontent.to_sql(name='alarmcontent', con=conn, if_exists='append', index=False, dtype=dtypedict)  

    execute_time = time.time() - startTime
    msg = f"Execution time(s) : {execute_time}"
    logging.debug(msg)     

    logging.debug('----------Insert Task Finish----------')

    execute_time = time.time() - startTime_overall
    msg = f"Total Execution time(s) : {execute_time}"
    logging.debug(msg)

    logging.debug('--------------------Task Finish--------------------')
else:
    pass


# In[17]:


# entime = datetime.datetime(2025, 2, 27, 9, 5, 0)  # 初始 etime
# end_time = datetime.datetime(2025, 3, 3, 4, 30, 0)  # 最後 etime

# while entime <= end_time:
#     stime = (entime - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')  # stime 是 etime 的 5 分鐘前
#     etime = (entime).strftime('%Y-%m-%d %H:%M:%S')

#     logging.debug('--------------------Task Starts--------------------')

#     startTime_overall = time.time() 

#     logging.debug('--------------------The Crawling Task Starts--------------------')

#     startTime = time.time()

#     with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
#         sql =   """
#             SELECT * 
#             FROM [SRVMSDBA1].[AIMSFTAO].[dbo].[ooutputlist_m]          
#         """       
#         query = conn.execute(text(sql))  
#         df_ooutputlist_m = pd.DataFrame([dict(i) for i in query])

#     df_alarm, ptype = get_GZ_data_alarm(stime,etime)

#     if ptype != '':

#         if len(df_alarm[df_alarm['Variable']=='METROLOGY-P21-MO1-SP']['Count'])==0: 
#             METROLOGY_P21_MO1_SP = 0.0 
#         else: 
#             METROLOGY_P21_MO1_SP = df_alarm[df_alarm['Variable']=='METROLOGY-P21-MO1-SP']['Count'].item()

#         if len(df_alarm[df_alarm['Variable']=='METROLOGY-COATINGWEIGHT']['Count'])==0: 
#             METROLOGY_COATINGWEIGHT = 0.0
#         else: 
#             METROLOGY_COATINGWEIGHT = df_alarm[df_alarm['Variable']=='METROLOGY-COATINGWEIGHT']['Count'].item()

#         df_alarm['Code'] = df_alarm['Variable'].str.extract(r'_(\w+)$')
#         df_alarm = df_alarm.merge(df_ooutputlist_m.loc[:,['Cname','Code']],on='Code')
#         df_alarm['Variable'] = df_alarm['Variable'].str.replace(r'_(\w+)$', r'_(\1)', regex=True) + df_alarm['Cname']        

#         alarm_dict = {
#             row["Variable"]: {"count": row["Count"], "min": row["Min"], "max": row["Max"]}
#             for _, row in df_alarm.iterrows()
#         }

#         # 加入額外的 key
#         final_dict = {
#             "塗前水分": METROLOGY_P21_MO1_SP,
#             "塗佈量": METROLOGY_COATINGWEIGHT,
#             **alarm_dict  # 合併兩個字典
#         }

#         import uuid

#         # 先轉成 JSON 字串，確保中文字不轉 Unicode
#         json_content = json.dumps(final_dict, ensure_ascii=False)

#         # 建立 DataFrame
#         df_alarmcontent = pd.DataFrame({
#             'UUID': [str(uuid.uuid4()).upper()],  # 轉換為字串，避免 SQL Server 格式錯誤
#             'paperid': [ptype],  
#             'startdatetime': [stime],
#             'enddatetime': [etime],
#             'content': [json_content]  # 這裡存成 JSON 字串
#         })

#         execute_time = time.time() - startTime
#         msg = f"Execution time(s) : {execute_time}"
#         logging.debug(msg)

#         logging.debug('--------------------The Crawling Task Finish--------------------')   

#         logging.debug('----------Insert Task Starts----------')

#         startTime = time.time()    

#         if df_alarmcontent.empty:
#             pass
#             logging.debug("df_alarmcontent is empty")
#         else:
#     #         df_alarmcontent['content'] = df_alarmcontent['content'].apply(lambda x: json.dumps(x, ensure_ascii=False))
#             with df_SERVER_SRVMSDBA2['create_engine'][0].connect() as conn:
#                 dtypedict = mapping_df_types(df_alarmcontent)
#                 df_alarmcontent.to_sql(name='alarmcontent', con=conn, if_exists='append', index=False, dtype=dtypedict)  

#         execute_time = time.time() - startTime
#         msg = f"Execution time(s) : {execute_time}"
#         logging.debug(msg)     

#         logging.debug('----------Insert Task Finish----------')

#         execute_time = time.time() - startTime_overall
#         msg = f"Total Execution time(s) : {execute_time}"
#         logging.debug(msg)

#         logging.debug('--------------------Task Finish--------------------')
#     else:
#         pass    
    
#     entime += timedelta(minutes=5)  # etime 每次加 5 分鐘    

