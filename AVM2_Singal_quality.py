#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sa_text
from sqlalchemy import text
import sqlalchemy
import warnings
from urllib.parse import quote_plus as urlquote

import os
import pyodbc

warnings.filterwarnings("ignore")

from sqlalchemy import text, bindparam
from sqlalchemy.exc import SQLAlchemyError
from concurrent.futures import ThreadPoolExecutor, as_completed

import re


# In[2]:


import logging
from logging.handlers import TimedRotatingFileHandler

log_filename = 'C:\PythonScheduler\AVM2_Singal_quality\dist\AVM2_Singal_quality.log'
handler = TimedRotatingFileHandler(log_filename, when='midnight', backupCount=7)
handler.suffix = '%Y-%m-%d.log'
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


# In[3]:


df_SERVER_SRVMIDDBA1 = pd.DataFrame([['SRVMIDDBA1','FTAWSP1']], columns=['SERVER', 'DB'])
df_SERVER_YFYASTADBA3 = pd.DataFrame([['YFYASTADBA3','FTAWSP_PIVOT']], columns=['SERVER', 'DB'])
df_SERVER_WSP2023R2HTA1 = pd.DataFrame([['WSP2023R2HTA1','Runtime']], columns=['SERVER', 'DB'])
df_SERVER_SRVMSDBA2 = pd.DataFrame([['SRVMSDBA2','FTA_HISTORY']], columns=['SERVER', 'DB'])

df_SERVER_SRVMIDDBA1['create_engine'] = ''
df_SERVER_SRVMIDDBA1['cnx'] = ''

df_SERVER_YFYASTADBA3['create_engine'] = ''
df_SERVER_YFYASTADBA3['cnx'] = ''

df_SERVER_WSP2023R2HTA1['create_engine'] = ''
df_SERVER_WSP2023R2HTA1['cnx'] = ''

df_SERVER_SRVMSDBA2['create_engine'] = ''
df_SERVER_SRVMSDBA2['cnx'] = ''


# In[4]:


df_SERVER_SRVMIDDBA1['create_engine'][0] = create_engine('mssql+pyodbc://ftawsp_r:fta12345@' + df_SERVER_SRVMIDDBA1['SERVER'][0] + '/' + df_SERVER_SRVMIDDBA1['DB'][0] + '?&driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True)
df_SERVER_SRVMIDDBA1['cnx'][0] = df_SERVER_SRVMIDDBA1['create_engine'][0].connect()

df_SERVER_YFYASTADBA3['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2023") + df_SERVER_YFYASTADBA3['SERVER'][0] + '/' + df_SERVER_YFYASTADBA3['DB'][0] + '?&driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True)
df_SERVER_YFYASTADBA3['cnx'][0] = df_SERVER_YFYASTADBA3['create_engine'][0].connect()   

df_SERVER_WSP2023R2HTA1['create_engine'][0] = create_engine('mssql+pyodbc://query_user:%s@' % urlquote("Fta@2025") + df_SERVER_WSP2023R2HTA1['SERVER'][0] + '/' + df_SERVER_WSP2023R2HTA1['DB'][0] + '?&driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True)
df_SERVER_WSP2023R2HTA1['cnx'][0] = df_SERVER_WSP2023R2HTA1['create_engine'][0].connect()

df_SERVER_SRVMSDBA2['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2022") + df_SERVER_SRVMSDBA2['SERVER'][0] + '/' + df_SERVER_SRVMSDBA2['DB'][0] + '?&driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True)
df_SERVER_SRVMSDBA2['cnx'][0] = df_SERVER_SRVMSDBA2['create_engine'][0].connect()   


# In[5]:


def mapping_df_types(df):
    dtypedict = {}
    for i, j in zip(df.columns, df.dtypes):
        if "object" in str(j):
            dtypedict.update({i: sqlalchemy.types.NVARCHAR(length=255)})
        if "float" in str(j):
            dtypedict.update({i: sqlalchemy.types.Float()})
        if "int" in str(j):
            dtypedict.update({i: sqlalchemy.types.Integer()})
        if "datetime" in str(j):
            dtypedict.update({i: sqlalchemy.DateTime()})
    return dtypedict


# In[6]:


full_tag_list = []

try:  
    file_path = r'C:\PythonScheduler\AVM2_Singal_quality\dist\PM21_signal.xlsx'

    # 用 ExcelFile 先讀出所有 sheet name
    with pd.ExcelFile(file_path) as xls:
        all_sheets = xls.sheet_names  # 取得所有 sheet 名稱
        
        dfs_signal = []  # 用來暫存每個 sheet 的 DataFrame

        for sheet_name in all_sheets:
            # 讀取該 sheet
            df_signal = pd.read_excel(
                xls,
                sheet_name=sheet_name,
                skiprows=0,
                header=None,
                names=["Code", "WspCode"]
            )
            # 加上來源 sheet 名稱
            df_signal['table_name'] = sheet_name
            # 加入 list
            dfs_signal.append(df_signal)
            
    # 合併所有 sheet
    df_all = pd.concat(dfs_signal, ignore_index=True)
except:                    
    file_path = r'C:\Users\Jason.Ouyang\Downloads\OuYang\Python\20230313_AVM2\PM21_signal.xlsx'
    
    # 用 ExcelFile 先讀出所有 sheet name
    with pd.ExcelFile(file_path) as xls:
        all_sheets = xls.sheet_names  # 取得所有 sheet 名稱
        
        dfs_signal = []  # 用來暫存每個 sheet 的 DataFrame

        for sheet_name in all_sheets:
            # 讀取該 sheet
            df_signal = pd.read_excel(
                xls,
                sheet_name=sheet_name,
                skiprows=0,
                header=None,
                names=["Code", "WspCode"]
            )
            # 加上來源 sheet 名稱
            df_signal['table_name'] = sheet_name
            # 加入 list
            dfs_signal.append(df_signal)
            
    # 合併所有 sheet
    df_all = pd.concat(dfs_signal, ignore_index=True)  
    
if not df_all.empty:
    full_tag_list = df_all['WspCode'].tolist()

def normalize_code(code):
    # A 類不處理
    if code.startswith("A"):
        return code
    
    # B/C/D 類補零：1 位數字 → 補成 2 位數（如 B1 → B01）
    return re.sub(r"^([BCD])(\d)$", r"\g<1>0\g<2>", code)

df_all["Code"] = df_all["Code"].apply(normalize_code)


# In[8]:


DAYS_BACK = 1  # 往前跑 30 天

MAX_RETRY = 3        # 最多重試 3 次
RETRY_DELAY = 2      # 第一次失敗後等 2 秒（後面會指數增加）
BATCH_SIZE = 6       # 每批查幾個 tag
MAX_WORKERS = 4      # 平行線程數

def execute_with_retry(sql, params, batch_id):
    """帶重試機制的 SQL 執行"""
    retry = 0
    start_time = time.time()
    logging.debug(f"[Batch {batch_id}] 開始查詢 {len(params['tag_list'])} 個 tag") 

    while True:
        try:
            # 每個線程建立自己的 engine + connection
            engine = create_engine(
                'mssql+pyodbc://query_user:%s@' % urlquote("Fta@2025") +
                df_SERVER_WSP2023R2HTA1['SERVER'][0] + '/' +
                df_SERVER_WSP2023R2HTA1['DB'][0] +
                '?&driver=ODBC+Driver+17+for+SQL+Server',
                fast_executemany=True
            )            

            with engine.connect() as conn:   # 每次都建立新的連線，查完自動關閉            
                query = conn.execute(sql, params)
                result = pd.DataFrame([dict(i) for i in query])       

                end_time = time.time()
                logging.debug(f"[Batch {batch_id}] 查詢完成，耗時 {end_time-start_time:.2f} 秒")
                return result

        except SQLAlchemyError as e:
            retry += 1
            logging.debug(f"[Batch {batch_id}] SQL Error 第 {retry} 次失敗: {e}")

            if retry >= MAX_RETRY:
                logging.debug(f"[Batch {batch_id}] 已達最大重試次數，放棄此次查詢")
                return None

            # 指數回退 delay
            sleep_seconds = RETRY_DELAY * (2 ** (retry - 1))
            logging.debug(f"[Batch {batch_id}] 等待 {sleep_seconds} 秒後重試...")
            time.sleep(sleep_seconds)

def execute_hour_with_retry(conn, sql, params, system, hour_idx):
    retry = 0
    start_time = time.time()

    while True:
        try:
            query = conn.execute(text(sql), params)
            df = pd.DataFrame([dict(i) for i in query])

            elapsed = time.time() - start_time
            logging.debug(
                f"[PM21_W_{system}][Hour {hour_idx:02d}] 查詢成功，"
                f"{len(df)} 筆，耗時 {elapsed:.2f}s"
            )
            return df

        except SQLAlchemyError as e:
            retry += 1
            logging.debug(
                f"[PM21_W_{system}][Hour {hour_idx:02d}] "
                f"SQL Error 第 {retry} 次失敗: {e}"
            )

            if retry >= MAX_RETRY:
                logging.debug(
                    f"[PM21_W_{system}][Hour {hour_idx:02d}] "
                    f"已達最大重試次數，略過此時段"
                )
                return None

            sleep_seconds = RETRY_DELAY * (2 ** (retry - 1))
            logging.debug(
                f"[PM21_W_{system}][Hour {hour_idx:02d}] "
                f"{sleep_seconds}s 後重試"
            )
            time.sleep(sleep_seconds)            
            
def split_batches(tag_list, batch_size=6):
    for i in range(0, len(tag_list), batch_size):
        yield tag_list[i:i+batch_size], i//batch_size + 1  # 回傳 batch_id
        
def fetch_hour_data(system):
    all_data = []
    
    try:
        conn = df_SERVER_SRVMIDDBA1['cnx'][0]
        sql = sql_template.replace("{{system}}", system)    

        for idx, (start_time, end_time) in enumerate(time_ranges, start=1):

            logging.debug(f"[PM21_W_{system}] 第 {idx:02d}/24 小時段 → {start_time} ~ {end_time}")

            hour_df = execute_hour_with_retry(
                conn=conn,
                sql=sql,
                params={
                    "start_time": start_time,
                    "end_time": end_time
                },
                system=system,
                hour_idx=idx
            )

            if hour_df is not None and not hour_df.empty:
                all_data.append(hour_df)
                
    except Exception as e:
        logging.exception(f"[PM21_W_{system}] fetch_hour_data 發生未預期錯誤: {e}")
        return pd.DataFrame()                

    if not all_data:
        logging.debug(f"[PM21_W_{system}] 無任何資料")
        return pd.DataFrame()

    total_rows = sum(len(df) for df in all_data)
    logging.debug(
        f"[PM21_W_{system}] 合併完成，共 {total_rows} 筆資料"
    )

    return pd.concat(all_data, ignore_index=True)

def clean(df):
    df['value'] = np.where(
        df['valuetype']=='f', df['valuefloat'],
        np.where(df['valuetype']=='b', df['valuebool'], df['valueint'])
    )
    df['tag_name'] = df['tag_name'].str.strip()
    df = df[['fta_dtm','tag_name','tag_quality','value']]
    df['value'] = df['value'].astype(float)
    return df        

sql = text("""
    SET NOCOUNT ON

    DECLARE @StartDate DateTime = :start
    DECLARE @EndDate DateTime = :next_start

    SET NOCOUNT OFF;    

    SELECT TagName,SUM(defect) AS Amount
    FROM
    (
    SELECT
        History.StartDateTime,
        History.DateTime,
        History.TagName,
        History.QualityDetail,
        History.Value,
        QualityMap.QualityString,
        Case When History.Value is null and History.QualityDetail = 192
        --Case When History.Value is null
             Then 1 ELSE 0 
             END AS defect
    FROM History
    LEFT JOIN QualityMap ON History.QualityDetail = QualityMap.QualityDetail
    WHERE 1=1
      AND History.TagName IN :tag_list
      AND History.wwRetrievalMode = 'cyclic'
      AND History.wwResolution = 1000
      AND History.wwQualityRule = 'Extended'
      AND History.wwVersion = 'Latest'
      AND History.DateTime >= @StartDate AND History.DateTime <= @EndDate
      AND History.StartDateTime >= @StartDate
    ) t
    GROUP BY TagName
    """).bindparams(
    bindparam("tag_list", expanding=True)   # 這行讓 list 能安全展開成 IN (...)
)  

        
sql_template = """
    SELECT *
    FROM [SRVMIDDBA1].[FTAWSP1].[dbo].[PM21_W_{{system}}]
    WHERE fta_dtm >= :start_time
      AND fta_dtm <  :end_time
    ORDER BY fta_dtm DESC
"""    

for day_offset in range(1, DAYS_BACK + 1):

    # 今日日期
    today = datetime.date.today() - datetime.timedelta(days=day_offset-1)
    # today = datetime.datetime(2025, 12, 12, 8, 0, 0)

    # 前一天
    yesterday = today - datetime.timedelta(days=1)

    # start = 昨天 08:00
    start = datetime.datetime.combine(yesterday, datetime.time(8, 0, 0))

    # end = 今天 08:00
    end = datetime.datetime.combine(today, datetime.time(8, 0, 0))

    bdate = datetime.datetime.combine(yesterday,datetime.time(0))

    logging.debug(f"=== 處理日期範圍: {start} ~ {end} ===")    
    
    nan_count_dict = {tag: 0 for tag in full_tag_list}

    # 使用 ThreadPoolExecutor 平行線程查詢
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:  # 4 個線程同時查詢
        futures = []
        for batch, batch_id in split_batches(full_tag_list, BATCH_SIZE):
            futures.append(
                executor.submit(
                    execute_with_retry,
                    sql,
                    {"start": start, "next_start": end, "tag_list": batch},
                    batch_id
                )
            )

        for future in as_completed(futures):
            df = future.result()
            if df is None or df.empty:
                continue
            # 直接更新 nan_count_dict
            for _, row in df.iterrows():
                tag = row['TagName']
                amount = row['Amount']
                nan_count_dict[tag] = amount

    logging.debug("平行查詢完成，結果存入 nan_count_dict")

    df_nan_count_dict = pd.DataFrame(list(nan_count_dict.items()), columns=['TagName', 'Amount'])

    df_result = df_all.merge(df_nan_count_dict,left_on='WspCode',right_on='TagName',how='left')

    # 你的合併結果 df_result
    df = df_result.copy()

    # 新增日期欄位
    df["fta_dtm"] = bdate
    df['busr'] = 'System'

    # 依 table_name 分組
    for tbl, df_grp in df.groupby("table_name"):

        logging.debug(f"處理 table: {tbl} (rows={len(df_grp)})")

        # pivot 成一筆資料
        df_pivot = df_grp.pivot_table(
            index=["fta_dtm","busr"],     # 日期成 index
            columns="Code",    # 每個 Code 變成一欄
            values="Amount",   # 欄位值 = Amount
            fill_value=0       # 空值補 0
        ).reset_index()

        # SQL Server 目標 table 名稱（可依需求調整）
        target_table = tbl   # 例如：FTA_PM21_ABB_m

        # 寫入 SQL Server
        df_pivot.to_sql(
            target_table,
            con=df_SERVER_SRVMSDBA2['cnx'][0],
            if_exists="append",     # 追加寫入
            index=False
        )

        logging.debug(f"已寫入 {target_table} → {df_pivot.shape[1]} 欄、1 列")
    
    time_ranges = [(start + timedelta(hours=h), start + timedelta(hours=h+1)) for h in range(24)]
    
    df_ABB = clean(fetch_hour_data("ABB"))
    df_DCS = clean(fetch_hour_data("DCS"))
    df_Siemens = clean(fetch_hour_data("Siemens"))
    df_SKF = clean(fetch_hour_data("SKF"))
    
    df_ABB['result'] = np.where((df_ABB['value'].isna()) & (df_ABB['tag_quality']==192),1,0)
    df_DCS['result'] = np.where((df_DCS['value'].isna()) & (df_DCS['tag_quality']==192),1,0)
    df_Siemens['result'] = np.where((df_Siemens['value'].isna()) & (df_Siemens['tag_quality']==192),1,0)
    df_SKF['result'] = np.where((df_SKF['value'].isna()) & (df_SKF['tag_quality']==192),1,0)

    # 展開 pivot
    df_PM21_merge_quality = (
        pd.concat([df_DCS, df_ABB, df_Siemens, df_SKF])
            .pivot_table(index='fta_dtm', columns='tag_name', values='result')
            .reset_index()
    )
    df_PM21_merge_quality.replace(1, np.nan, inplace=True)

    df_nan_count_dict = df_PM21_merge_quality.drop(['fta_dtm'],axis=1).isna().sum().to_frame().reset_index()
    df_nan_count_dict.rename(columns={'tag_name':'TagName',0:'Amount'},inplace=True)
    df_nan_count_dict["TagName"] = df_nan_count_dict["TagName"].apply(normalize_code)
    
    logging.debug("查詢完成，結果存入 nan_count_dict")

    df_result = df_all.merge(df_nan_count_dict,left_on='Code',right_on='TagName',how='left')

    # 你的合併結果 df_result
    df = df_result.copy()

    # 新增日期欄位
    df["fta_dtm"] = bdate
    df['busr'] = 'System'

    # 依 table_name 分組
    for tbl, df_grp in df.groupby("table_name"):

        logging.debug(f"處理 table: {tbl} (rows={len(df_grp)})")

        # pivot 成一筆資料
        df_pivot = df_grp.pivot_table(
            index=["fta_dtm","busr"],     # 日期成 index
            columns="Code",    # 每個 Code 變成一欄
            values="Amount",   # 欄位值 = Amount
            fill_value=0       # 空值補 0
        ).reset_index()

        # SQL Server 目標 table 名稱（可依需求調整）
        target_table = tbl + '_RawDB'   # 例如：FTA_PM21_ABB_m

        # 寫入 SQL Server
        df_pivot.to_sql(
            target_table,
            con=df_SERVER_SRVMSDBA2['cnx'][0],
            if_exists="append",     # 追加寫入
            index=False
        )

        logging.debug(f"已寫入 {target_table} → {df_pivot.shape[1]} 欄、1 列")    


# In[ ]:


# with open('C:\PythonScheduler\AVM2\dist\AVM2.log', 'w') as f:
#     f.write('')


# In[ ]:





# In[ ]:




