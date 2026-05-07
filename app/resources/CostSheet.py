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

from dateutil.relativedelta import relativedelta


# In[ ]:


import logging
logger = logging.getLogger(__name__)  # 取得和主程式共用的 logger


# In[ ]:


# 成本單


# In[ ]:


class product_cost_details:
    def __init__(self, servers):
        self.servers = servers
    
    def fetch(self, stime: str, etime: str, mname: str, Product_Category: str, Product_two_ptype: str, two_month: str, level: str):
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        if not Product_Category:
            return {'success': False, 'message': 'Missing category parameter'}   
        if not Product_two_ptype:
            Product_two_ptype = ''
        if not two_month:
            two_month = '0'
        if not level:
            level = '1'
            
        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:            
            sql =   """
                SELECT '含浸原紙' AS [saleclass],'QE' AS [ptype2],'' AS [chsnm],'' AS [ptype],'' AS [chlnm] UNION ALL
                SELECT 'NCR原紙' AS [saleclass],'QC' AS [ptype2],'' AS [chsnm],'' AS [ptype],'' AS [chlnm] UNION ALL            
                SELECT [saleclass]
                      ,[ptype2]
                      ,[chsnm]
                      ,[ptype]
                      ,[chlnm]
                  FROM [AMIS].[dbo].[ampaper_category]
                  WHERE plant_id like 'A%'
                  AND len(saleclass) > 0
                  order by saleclass,ptype2,ptype
            """
            query = conn.execute(text(sql))  
            df_Ampaper_category = pd.DataFrame([dict(i) for i in query])
            
        if level == '2':
            Product_two_ptype = Product_Category
            Product_Category = df_Ampaper_category.loc[df_Ampaper_category['ptype2']==Product_two_ptype].head(1)['saleclass'].item()                       
            
        if level == '3':
            Product_two_ptype = Product_Category[:2]
            Product_Category = df_Ampaper_category.loc[df_Ampaper_category['ptype2']==Product_two_ptype].head(1)['saleclass'].item()                               

        if mname == "18":
            mname = 'PM18'
            mname_t = "'18'"
            sub_r = "'R'"
        elif mname == "19":
            mname = 'PM19'
            mname_t = "'19','C2'"
            sub_r = "'S'"
        elif mname == "20":
            mname = 'PM20'
            mname_t = "'20','C7','C8','C9'"
            sub_r = "'T'"
        elif mname == "21":
            mname = 'PM21'
            mname_t = "'21','C1','C6'"
            sub_r = "'W'"
        else:
            pass
        
        if Product_Category == 'NCR':
            mname = 'NCR'
        elif Product_Category == '含浸美紋':
            mname = '含浸'

        def Product_Cost_Details(stime,etime,mname,Product_Category,Product_two_ptype,df_Product_cost_schedule_Items_schema=None,NCR_Base_Paper=None):
            def Work_In_Process(df):
                df = df.dropna(how='all')
                df = df[df['年'].notna()].reset_index(drop=True)
                df['年'] = df['年'].astype(int)
                df['月'] = df['月'].astype(int)
                df['日'] = df['日'].astype(int)

                # 選取欄位

                df = df.loc[:,['年月','年', '月', '日', '號機', '紙別', '基重(原紙)','基重(成品)', '塗佈前', 
                                       '壓光前','複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']]
                # 計算欄位

                df['總計(噸數)'] = df[['塗佈前', '壓光前', '複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']].sum(axis=1, skipna=True).round(3)

                df['基重(原紙)'] = df['基重(原紙)'].apply(
                    lambda x: str(int(x)) if pd.notna(x) and float(x) == int(float(x))
                    else (str(x) if pd.notna(x) else None)
                )

                df['基重(成品)'] = df['基重(成品)'].apply(
                    lambda x: str(int(x)) if pd.notna(x) and float(x) == int(float(x))
                    else (str(x) if pd.notna(x) else None)
                )                    

                df['紙別基重(塗前)'] = df['號機'].astype(str) + df['紙別'].astype(str) + df['基重(原紙)'].astype(str)

                df['塗前'] = df[['塗佈前']].sum(axis=1, skipna=True)
                df['塗後'] = df[['壓光前', '複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']].sum(axis=1, skipna=True).round(3)

                df = df.replace({pd.NA: None, np.nan: None})

                return df.copy()  

            def classify_pn4(value):
                if pd.isna(value):
                    return None

                value_str = str(value)

                # 若中間為 NCR 或開頭為 UCR
                if value_str[1:4] == 'NCR' or value_str.startswith('UCR'):
                    return 'QC'
                elif value_str.startswith('M'):
                    return 'QE'
                elif value_str.isdigit():
                    return value_str[:2]  # 數字，取前兩位字串
                else:
                    return value_str[:2]  # 其他，一樣取前兩碼     
                
            # 讀取期末在產品(MES)
            def search_InProcess_MES(etime):

                dt = datetime.datetime.strptime(etime, "%Y%m")
                etime_t = (dt + relativedelta(months=1) - timedelta(days=1))
                etime_t = etime_t.strftime('%Y-%m-%d')

                srv_SRVAD1 = self.servers['SRVAD1'] 
                with srv_SRVAD1['create_engine'][0].connect() as conn:                
                    sql =   """
                        ;with raw_data as
                        (
                            select 
                                a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                            from openquery([10.10.1.27],'select * from [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] where Creation_date >= dateadd(m,-6,getdate())') a
                            inner join adpack b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass <> 'A') and substring(batch_no,10,2) = 'SH'
                            where 1=1
                            and bdate between '"""+ str(etime_t) +"""' and '"""+ str(etime_t) +"""' 
                            and re <> 0 and a.status_code = 'S'

                            union

                            select a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                            from openquery([10.10.1.27],'select * from [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] where Creation_date >= dateadd(m,-6,getdate())') a
                            inner join adsel b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass IN ('B','P') or b.pclass is null) and substring(batch_no,10,2) = 'SH'
                            where 1=1
                            and bdate between '"""+ str(etime_t) +"""' and '"""+ str(etime_t) +"""' 
                            and nstation not in('SP','WP','WH') 
                            and re <> 0 and a.status_code = 'S'
                            --order by runno, batch_no, ptype, psize1, psize2, x_yn, bhno
                        )
                        SELECT mname_2 AS mname,ptype,pgramg,SUM(T) AS T
                        FROM
                        (
                            SELECT runno,mname_2,bdate,batch_no,ptype,pgramg,psize1,psize2,store,ExportSales,pclass,rewt,SUM(re) AS re,SUM(T) AS T,
                            count(*) as amount
                            FROM
                            (
                                SELECT *,rewt*re*0.0004535924 AS T,
                                CASE WHEN x_yn = 'Y' Then '外銷' ELSE '內銷' END AS ExportSales,
                                CASE WHEN x_yn = 'Y' Then 'A4FG'
                                WHEN x_yn = 'N' AND substring(runno,1,1) = 'R' THEN 'A3FG'
                                WHEN x_yn = 'N' AND substring(runno,1,1) = 'S' THEN 'A2FG'
                                WHEN x_yn = 'N' AND substring(runno,1,1) = 'W' THEN 'A1FG'
                                END AS store,
                                CASE WHEN ptype like 'H%' THEN 'NCR'
                                     WHEN left(runno,1) = 'R' THEN 'PM18'
                                     WHEN left(runno,1) = 'S' THEN 'PM19'
                                     WHEN left(runno,1) = 'T' THEN 'PM20'
                                     WHEN left(runno,1) = 'W' THEN 'PM21'
                                END AS mname_2
                                FROM raw_data
                            ) t
                            GROUP BY runno,mname_2,bdate,batch_no,ptype,pgramg,psize1,psize2,store,ExportSales,pclass,rewt
                        ) m
                        GROUP BY mname_2,ptype,pgramg          
                    """       
                    query = conn.execute(text(sql))  
                    df_ERP_SH = pd.DataFrame([dict(i) for i in query]) 

                    sql =   """
                        SELECT 
                            mname_2 AS mname,
                            ptype,
                            pgramg,
                            sum(weigh) as T 

                        FROM
                        (
                            SELECT *,CASE 
                                WHEN x_yn = 'Y' AND pstatus = '成品' THEN 'A4FG'
                                WHEN pstatus = '成品' THEN 
                                    CASE 
                                        WHEN left(relno,1) = 'R' AND prodn <> 'R' THEN 'A3FG'
                                        WHEN left(relno,1) = 'S' AND prodn <> 'R' THEN 'A2FG'
                                        WHEN (left(relno,1) = 'T' AND prodn <> 'R') 
                                             OR (left(relno,1) = 'R' AND prodn <> 'R') 
                                             OR (left(relno,1) = 'S' AND prodn <> 'R') THEN 'A6FG'
                                        WHEN left(relno,1) = 'W' AND prodn <> 'R' THEN 'A7FG'   
                                        ELSE NULL  -- 如果沒有符合條件，不設值
                                    END
                                ELSE 'FTA.SFG.SR.PM' + CAST(left(relno,1) AS VARCHAR)  -- 非 "成品" 情況，store 依 mname 設定
                            END AS store,
                            CASE WHEN left(relno,1) = 'R' THEN 'PM18'
                                 WHEN left(relno,1) = 'S' THEN 'PM19'
                                 WHEN left(relno,1) = 'T' THEN 'PM20'
                                 WHEN left(relno,1) = 'W' THEN 'PM21'
                            END AS mname_2
                            FROM
                            (
                                select *,
                                CASE 
                                    WHEN prod = '1' THEN 
                                        CASE 
                                            WHEN LEFT(ptype, 1) = 'H' AND CAST(width AS FLOAT) >= 100 
                                                THEN RIGHT('00' + CAST(width AS VARCHAR), 4) + 'RL00'
                                            WHEN LEFT(ptype, 1) = 'H' OR CAST(width AS FLOAT) < 100 
                                                THEN 
                                                    CASE 
                                                        WHEN RIGHT(CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) AS VARCHAR), 1) = '5' 
                                                            THEN RIGHT('00' + CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) - 1 AS VARCHAR), 3) + 'KRL00'
                                                        WHEN RIGHT(CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) AS VARCHAR), 1) = '8' 
                                                            THEN RIGHT('00' + CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) - 2 AS VARCHAR), 3) + 'KRL00'
                                                        ELSE RIGHT('00' + CAST(CAST(width AS FLOAT) * 10 AS VARCHAR), 3) + 'KRL00'
                                                    END
                                            ELSE 
                                                RIGHT('00' + CAST(width AS VARCHAR), 4) + 'RL00'
                                        END
                                    WHEN prod IN ('2', '4', '7', '8') THEN 'R'
                                    ELSE NULL 
                                END AS prodn,
                                CASE WHEN prod = 1 THEN '成品'
                                WHEN prod = 2 Then '裁切'
                                WHEN prod = 4 Then '中倉'
                                WHEN prod = 7 Then '分條'
                                WHEN prod = 8 Then '含浸' END AS pstatus

                                from adwind 
                                where 1=1
                                and bdate between '"""+ str(etime_t) +"""' and '"""+ str(etime_t) +"""'  
                                and prod not in('3','5','6','9') 
                                --order by runno, prod, ptype, pclass, width, pgramg, x_yn, relno, swinno
                            ) m
                        ) t
                        WHERE store NOT LIKE '%SR%'
                        GROUP BY mname_2,ptype,pgramg
                    """
                    query = conn.execute(text(sql))  
                    df_ERP_SR = pd.DataFrame([dict(i) for i in query])   

                srv_SRVAD2 = self.servers['SRVAD2'] 
                with srv_SRVAD2['create_engine'][0].connect() as conn:                    
                    sql =   """
                        --ACAA040I3.ASP
                        DECLARE @sdate varchar(10) = '"""+ str(etime_t) +"""'
                        DECLARE @edate varchar(10) = '"""+ str(etime_t) +"""'

                        ;With raw_data as
                        (
                            SELECT *
                            FROM
                            (
                                --SRVAD2
                                select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation,sptype,
                                CASE WHEN pm='W' AND nstation = 'WR' Then '再捲機'
                                WHEN pm='W' AND nstation = 'WC' Then '塗佈機'
                                WHEN pm='W' AND nstation = 'WE' Then '壓光機'
                                WHEN pm='W' AND nstation = 'WW' Then '複捲機'

                                WHEN pm='T' AND nstation = 'TR' Then '再捲機'
                                WHEN pm='T' AND nstation = 'TC' Then '塗佈機'
                                WHEN pm='T' AND nstation = 'TE' Then '壓光機'
                                WHEN pm='T' AND nstation = 'TW' Then '複捲機'

                                WHEN pm='S' AND nstation = 'SW' Then '複捲機'
                                WHEN pm='R' AND nstation = 'RW' Then '複捲機'

                                END AS 機台
                                from [pm21].[dbo].[adbuff_prod] where cbdate between @sdate and @edate

                                UNION ALL

                                select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation,sptype,
                                CASE WHEN pm='W' AND nstation = 'WC' Then '塗佈機'
                                WHEN pm='W' AND nstation = 'WS' Then '裁切機'
                                WHEN pm='W' AND nstation = 'WW' Then '分條機'
                                WHEN pm='W' AND nstation = 'WE' Then '壓光機'

                                WHEN pm='T' AND nstation = 'TR' Then '再捲機'
                                WHEN pm='T' AND nstation = 'TC' Then '塗佈機'
                                WHEN pm='T' AND nstation = 'TE' Then '壓光機'
                                WHEN pm='T' AND nstation = 'TS' Then '裁切機'

                                WHEN pm='S' AND nstation = 'SE' Then '壓光機'
                                WHEN pm='S' AND nstation = 'SC' Then '塗佈機'
                                WHEN pm='S' AND nstation = 'SS' Then '裁切機'
                                WHEN pm='S' AND nstation = 'SW' Then '分條機'

                                WHEN pm='R' AND nstation = 'RS' Then '裁切機'

                                END AS 機台

                                from [SRVAD2].[pm21].[dbo].[adwind_prod] where cbdate between @sdate and @edate
                                UNION ALL
                                select cbdate,pm,mname,ptype,gramg,pgramg,(rewt*re/2204.62),nstation as weigh,sptype,
                                CASE WHEN pm='W' AND nstation = 'WH' Then '選紙班'
                                WHEN pm='W' AND nstation = 'WP' Then '包裝機'

                                WHEN pm='T' AND nstation = 'TH' Then '選紙班'
                                WHEN pm='T' AND nstation = 'TP' Then '包裝機'

                                WHEN pm='S' AND nstation = 'SH' Then '選紙班'
                                WHEN pm='S' AND nstation = 'SP' Then '包裝機'

                                WHEN pm='R' AND nstation = 'RH' Then '選紙班'
                                END AS 機台

                                from [SRVAD2].[pm21].[dbo].[adstock_prod] where cbdate between @sdate and @edate
                            ) t
                            WHERE 1=1
                            AND 機台 is not null --AND gramg is not null 
                            AND len(ptype) > 0
                            --AND ptype = 'KL00' AND pgramg = '58'
                        )
                        SELECT 
                        YEAR(cbdate) AS 年,
                        MONTH(cbdate) AS 月,
                        DAY(cbdate) AS 日,
                        CASE WHEN pm='R' THEN 'PM18' WHEN pm='S' THEN 'PM19' WHEN pm='T' THEN 'PM20' WHEN pm='W' THEN 'PM21' ELSE '' END AS 號機,
                        ptype AS 紙別,
                        pgramg AS '基重(原紙)',
                        pgramg AS '基重(成品)',
                        ISNULL(SUM([塗佈前]),0) AS [塗佈前],
                        ISNULL(SUM([壓光前]),0) AS [壓光前],
                        ISNULL(SUM([複捲前(含中間倉)]),0) AS [複捲前(含中間倉)],
                        ISNULL(SUM([截切前]),0) AS [截切前],
                        ISNULL(SUM([包裝前]),0) AS [包裝前],
                        ISNULL(SUM([已包未入庫]),0) AS [已包未入庫]
                        FROM (
                            SELECT 
                                cbdate,pm,ptype,gramg,pgramg,sptype,
                                CASE WHEN ptype like '%NCR' Then ''
                                WHEN ptype like '%MM' Then ''
                                WHEN 機台 IN ('再捲機','塗佈機') THEN '塗佈前'
                                WHEN 機台 = '壓光機' THEN '壓光前'
                                WHEN 機台 IN ('複捲機','分條機') THEN '複捲前(含中間倉)'
                                WHEN 機台 = '裁切機' THEN '截切前'
                                WHEN 機台 IN ('選紙班','包裝機') THEN '包裝前'
                                END AS 機台,
                                weigh
                            FROM raw_data
                        ) AS source
                        PIVOT (
                            SUM(weigh)
                            FOR 機台 IN ([塗佈前],[壓光前],[複捲前(含中間倉)],[截切前],[包裝前],[已包未入庫])
                        ) AS pivot_table
                        --WHERE pm = 'W'
                        GROUP BY cbdate,pm,ptype,pgramg
                        ORDER BY cbdate,pm desc,ptype,pgramg
                    """       
                    query = conn.execute(text(sql))  
                    df_InProcess = pd.DataFrame([dict(i) for i in query])

                df_ERP_SR_SH = pd.concat([df_ERP_SR,df_ERP_SH],ignore_index=True)
                df_ERP_SR_SH['年'] = df_InProcess.loc[0,'年']
                df_ERP_SR_SH['月'] = df_InProcess.loc[0,'月']
                df_ERP_SR_SH['日'] = df_InProcess.loc[0,'日']
                df_ERP_SR_SH.rename(columns={'mname':'號機','ptype':'紙別','pgramg':'基重(成品)','T':'已包未入庫'},inplace=True)
                df_ERP_SR_SH['基重(原紙)'] = df_ERP_SR_SH['基重(成品)'].copy()
                df_ERP_SR_SH['塗佈前'] = 0.0
                df_ERP_SR_SH['壓光前'] = 0.0
                df_ERP_SR_SH['複捲前(含中間倉)'] = 0.0
                df_ERP_SR_SH['截切前'] = 0.0
                df_ERP_SR_SH['包裝前'] = 0.0
                df_ERP_SR_SH['已包未入庫'] = df_ERP_SR_SH['已包未入庫'].astype(float)
                
                df_result = pd.concat([df_InProcess,df_ERP_SR_SH],ignore_index=True)
                
                df_result['號機'] = np.where(
                    df_result['紙別'].str.endswith('NCR'),
                    df_result['號機'],
                    np.where(
                        df_result['紙別'].str.startswith('H'), 
                        'NCR',
                        np.where(
                            df_result['紙別'].str.startswith('TR'),
                            '含浸',
                            df_result['號機']
                        )
                    )
                )                    

                df_result = df_result.groupby(['年','月','日','號機','紙別','基重(原紙)','基重(成品)'])                    .agg(a=('塗佈前','sum'), 
                         b=('壓光前','sum'),
                         c=('複捲前(含中間倉)','sum'), 
                         d=('截切前','sum'),
                         e=('包裝前','sum'),
                         f=('已包未入庫','sum'),
                        ).reset_index()  

                df_result = df_result.rename(columns={
                    'a': '塗佈前',
                    'b': '壓光前',
                    'c': '複捲前(含中間倉)',
                    'd': '截切前',
                    'e': ' 包裝前',
                    'f': '已包未入庫',
                })
                
                df_result['年月'] = etime

                return df_result         
            
            
            # 讀取入庫量(MES)
            def search_Inventory_MES(etime):

                yearmonth = etime

                dt = datetime.datetime.strptime(etime, "%Y%m")
                stime = dt.strftime('%Y-%m-%d')
                etime = (dt + relativedelta(months=1) - timedelta(days=1)).strftime('%Y-%m-%d')  

                df_RE_transRate = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\FTA平版料號轉換率\FTA 平版料號轉換率.xlsx',
                                          sheet_name='工作表1',skiprows=0)
                df_RE_transRate = df_RE_transRate[df_RE_transRate['TO 單位類別'] != 'Length']
                df_RE_transRate['料號_2'] = df_RE_transRate['料號'].str[-13:]
                df_RE_transRate_reduce = df_RE_transRate.groupby(['料號_2','轉換率']).size().reset_index().groupby(['料號_2'])['轉換率'].min().reset_index()

                srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
                with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:                
                    sql =   """
                        SELECT [PROCESS_CODE]
                              ,[SERVER_CODE]
                              ,[BATCH_ID]
                              ,[BATCH_LINE_ID]
                              ,[STATUS_CODE]
                              ,[ORGCODE]
                              ,[RXID]
                              ,[PREVIOUS_RXID]
                              ,[BATCH_NO]
                              ,[MACHINE_NO]
                              ,[ITEM_NO]
                              ,SUBSTRING([ITEM_NO],2,4) as ptype
                              ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                              ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                              ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                              ,[SUBINVENTORY_CODE]
                              ,[LOCATOR]
                              ,[TRANSACTION_QUANTITY]
                              ,[TRANSACTION_UOM]
                              ,[SECONDARY_TRANSACTION_QUANTITY]
                              ,[SECONDARY_UOM_CODE]
                              ,[TRANSACTION_DATE]
                              ,convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) as bdate
                              ,[LOT_NUMBER]
                              ,[STATUS]
                          FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST]
                          WHERE 1=1
                          AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                          AND MACHINE_NO IN ('18','19','20','21')
                          AND SUBINVENTORY_CODE != 'SFG'
                          AND STATUS_CODE = 'S'

                          UNION ALL

                        SELECT [PROCESS_CODE]
                              ,[SERVER_CODE]
                              ,[BATCH_ID]
                              ,[BATCH_LINE_ID]
                              ,[STATUS_CODE]
                              ,[ORGCODE]
                              ,[RXID]
                              ,[PREVIOUS_RXID]
                              ,[BATCH_NO]
                              ,[MACHINE_NO]
                              ,[ITEM_NO]
                              ,SUBSTRING([ITEM_NO],2,4) as ptype
                              ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                              ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                              ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                              ,[SUBINVENTORY_CODE]
                              ,[LOCATOR]
                              ,[TRANSACTION_QUANTITY]
                              ,[TRANSACTION_UOM]
                              ,[SECONDARY_TRANSACTION_QUANTITY]
                              ,[SECONDARY_UOM_CODE]
                              ,[TRANSACTION_DATE]
                              ,convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) as bdate
                              ,[LOT_NUMBER]
                              ,[STATUS]
                          FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P211_IN_MMT_PROD_ST]
                          where 1=1
                          AND (
                            (SUBSTRING([ITEM_NO],2,4) like 'MM%' AND [ITEM_NO] like '%R') 
                            OR 
                            (RIGHT(SUBSTRING([ITEM_NO],2,4),3) = 'NCR' AND [ITEM_NO] like '%R')
                          )
                          AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                          AND [STATUS_CODE] = 'S'          
                    """       
                    query = conn.execute(text(sql))
                    df_inventory_250 = pd.DataFrame([dict(i) for i in query])

                df_inventory_250['料號_2'] = df_inventory_250['ITEM_NO'].str[-13:]   

                df_inventory_250_C = df_inventory_250[df_inventory_250['STATUS'] == 'C']
                df_inventory_250_M = df_inventory_250[df_inventory_250['STATUS'] == 'M']
                df_inventory_250_C = df_inventory_250_C[~df_inventory_250_C['RXID'].isin(list(df_inventory_250[df_inventory_250['STATUS'] == 'M']['PREVIOUS_RXID']))]
                df_inventory_250_M = df_inventory_250_M.loc[df_inventory_250_M.groupby('PREVIOUS_RXID')['TRANSACTION_DATE'].idxmax()]

                df_inventory_250_latest = pd.concat([df_inventory_250_C,df_inventory_250_M],ignore_index=True)
                df_inventory_250_latest = df_inventory_250_latest.loc[:,['bdate','MACHINE_NO','ptype', 'gramg','ITEM_NO','TRANSACTION_QUANTITY','TRANSACTION_UOM',
                                              'SECONDARY_TRANSACTION_QUANTITY','SECONDARY_UOM_CODE','料號_2']]
                df_inventory_250_latest = df_inventory_250_latest.merge(df_RE_transRate_reduce,on='料號_2',how='left')
                df_inventory_250_latest['weigh'] = np.where(
                    df_inventory_250_latest['SECONDARY_UOM_CODE'].isna(),
                    df_inventory_250_latest['TRANSACTION_QUANTITY'] * 1000,
                    df_inventory_250_latest['SECONDARY_TRANSACTION_QUANTITY'].astype(float) * df_inventory_250_latest['轉換率'] / 1000.0
                )
                df_inventory_250_latest['gramg'] = df_inventory_250_latest['gramg'].astype(float) / 10.0
                df_inventory_250_latest['MACHINE_NO'] = np.where(
                    df_inventory_250_latest['ptype'].str.endswith('NCR'),
                    'PM' + df_inventory_250_latest['MACHINE_NO'],
                    np.where(
                        df_inventory_250_latest['ptype'].str.startswith('H'),
                        'NCR',
                        np.where(
                            df_inventory_250_latest['ptype'].str.startswith('T'),
                            '含浸',
                            'PM' + df_inventory_250_latest['MACHINE_NO']
                        )        
                    )
                )
                df_inventory_250_result = df_inventory_250_latest.groupby(['MACHINE_NO','ptype','gramg'])['weigh'].sum().reset_index()

                df_inventory_250_result.rename(columns={'MACHINE_NO':'機台','ptype':'PN4','gramg':'基重','weigh':'合計(kg)'},inplace=True)

                df_inventory_250_result['基重'] = df_inventory_250_result['基重'].round(1).astype(str)

                df_inventory_250_result['合計(kg)'] = df_inventory_250_result['合計(kg)'].astype(float).round(1)
                df_inventory_250_result['紙別基重'] = df_inventory_250_result['機台'] + df_inventory_250_result['PN4'] + df_inventory_250_result['基重']
                df_inventory_250_result['紙別基重'] = df_inventory_250_result['紙別基重'].str.replace(r'\.0$', '', regex=True)
                df_inventory_250_result['年月'] = yearmonth

                return df_inventory_250_result
            
            def material_data(etime,df_Equivalent_Output_Before_Apportionment):

                df_RMData = None

                # 讀取原物料名稱_成本
                etime_sheet_name = str(int(etime[:4])-1911)

                base_path = r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供'

                # 先試主檔
                try:
                    df_RMData = pd.read_excel(
                        fr'{base_path}\RMData_料號成本.xlsx',
                        sheet_name=etime_sheet_name,
                        header=0
                    )
                except Exception:
                    pass    

                # 如果主檔沒有，再找歷史檔
                if df_RMData is None:
                    for year in range(int(etime[:4]), 2015, -1):
                        try:
                            file_path = fr'{base_path}\RMData_料號成本_{year}.xlsx'

                            df_RMData = pd.read_excel(
                                file_path,
                                sheet_name=etime_sheet_name,
                                header=0
                            )
                            print(f'使用檔案: {file_path}')
                            break

                        except Exception:
                            continue    

                # 防呆檢查
                if df_RMData is None:
                    raise RuntimeError(f'找不到含 sheet {etime_sheet_name} 的 RMData Excel')                      

                month_map = {
                    '01': '1月','02': '2月','03': '3月','04': '4月','05': '5月','06': '6月','07': '7月',
                    '08': '8月','09': '9月','10': '10月','11': '11月','12': '12月'
                }

                etime_cost_col = month_map.get(etime[4:], '未知月份')
                df_RMData.rename(columns={etime_cost_col:'COST_2'},inplace=True)    

                # 讀取 原物料 用量 Data_

                stime_d = (datetime.datetime.strptime(etime, "%Y%m")).strftime('%Y-%m-%d')
                etime_d = (datetime.datetime.strptime(etime, "%Y%m") + relativedelta(months=1)).strftime('%Y-%m-%d')

                srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
                with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:
                    sql =   """
                    SELECT CASE WHEN P210.[TRANSACTION_UOM] = 'KG' THEN [TRANSACTION_QUANTITY]
                                ELSE [TRANSACTION_QUANTITY] * 1000.0 END AS KG
                          ,CASE WHEN len(P210.[BATCH_NO]) = 17 THEN 'JB'
                                WHEN P210.[BATCH_NO] like '%SR%' THEN 'SR'
                                ELSE 'SH' END AS BATCH_Sort
                          ,'' AS RM_Kind
                          ,'' AS RMN
                          ,CASE WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'R' THEN '18'
                                WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'S' THEN '19'
                                WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'T' THEN '20'
                                WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'W' THEN '21' 
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'R' THEN '18' 
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'S' THEN '19' 
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'T' THEN '20'
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'W' THEN '21'
                                ELSE '' END AS 號機
                          ,'' AS PD
                          ,SUBSTRING(P208.[RECIPE_NO],3,2) AS PN2
                          ,SUBSTRING(P208.[RECIPE_NO],3,4) AS PN4
                          ,'' AS COST
                          ,P210.[ITEM_NO] AS '料號'
                          ,P210.[TRANSACTION_DATE] AS '異動日期'
                          ,P210.[TRANSACTION_QUANTITY] * -1 AS '主要數量'
                          ,P210.[TRANSACTION_UOM] AS '主要單位'
                          ,P210.[BATCH_NO] AS '工單'
                          --,P210.[SUBINVENTORY_CODE]
                          --,P210.[LOCATOR]
                          --,[SECONDARY_TRANSACTION_QUANTITY]
                          --,[SECONDARY_UOM_CODE]
                          --,[LOT_NUMBER]
                          --,P210.[STATUS]
                          ,CASE WHEN len(P210.[BATCH_NO]) = 17 THEN CAST(RIGHT(P208.[ITEM_NO],5) AS float) / 10.0
                                ELSE CAST(LEFT(RIGHT(P208.[ITEM_NO],6),5) AS float) / 10.0 END AS BW
                      FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P210_IN_MMT_INGR_ST] P210
                      LEFT JOIN (
                        SELECT distinct [BATCH_NO],[ITEM_NO],[RECIPE_NO] FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST]
                        WHERE [XXIF_CHP_P208_IN_CRE_BATCH_ST].[STATUS_CODE] = 'S'
                      ) P208 ON P208.BATCH_NO = P210.BATCH_NO
                      where 1=1
                      --AND P210.[ITEM_NO] ='903412200046'
                      AND P210.[TRANSACTION_DATE]>='"""+ str(stime_d) +""" 08:00:00' AND P210.TRANSACTION_DATE<'"""+ str(etime_d) +""" 08:00:00'
                      AND P210.[STATUS_CODE] = 'S'
                      AND P210.[SUBINVENTORY_CODE] = 'RM'
                      order by TRANSACTION_DATE
                    """       
                    query = conn.execute(text(sql))
                    df_reel_material = pd.DataFrame([dict(i) for i in query])  

                    df_reel_material = df_reel_material.sort_values(by=['異動日期','KG']).reset_index(drop=True)

                    # 條件一：號機為 '21' 且 BATCH_NO 結尾為 '199'
                    condition_21 = (df_reel_material['號機'] == '21') & (df_reel_material['工單'].astype(str).str.endswith('199'))

                    # 條件二：號機為 '19' 且 BATCH_NO 結尾為 '199'
                    condition_19 = (df_reel_material['號機'] == '19') & (df_reel_material['工單'].astype(str).str.endswith('199'))

                    # 設定 PN4
                    df_reel_material['PN4'] = np.where(condition_21, '2000',
                                               np.where(condition_19, '1000', df_reel_material['PN4']))

                    # 設定 PN2
                    df_reel_material['PN2'] = np.where(condition_21, '20',
                                               np.where(condition_19, '10', df_reel_material['PN2']))

                    df_reel_material['BW'] = np.where(condition_21, 0,
                                               np.where(condition_19, 0, df_reel_material['BW']))

                    df_reel_material['PN2'] = np.where(df_reel_material['PN4'].astype(str).str.startswith('MM'), 'QE', df_reel_material['PN2'])
                    df_reel_material['PN2'] = np.where(df_reel_material['PN4'].astype(str).str.endswith('NCR'), 'QC', df_reel_material['PN2'])

                    def RM_Kind_mapping(k_value):
                        if k_value.startswith('2') or k_value.startswith('3') or k_value.startswith('90'):
                            mid_result = '纖維'
                        else:
                            # 從 RMP 表找對應
                            mid_result = df_RMData.loc[df_RMData['料號'] == k_value, '類別']
                            mid_result = mid_result.iloc[0] if not mid_result.empty else None  

                        if mid_result == '化工':
                            mid_result = 'CH'
                        elif mid_result == '塗料':
                            mid_result = 'CT'
                        elif mid_result == '填料':
                            mid_result = 'CY'
                        elif mid_result == '纖維':
                            mid_result = 'FB'

                        return mid_result

                    df_reel_material['RM_Kind'] = df_reel_material['料號'].apply(RM_Kind_mapping)

                    df_reel_material = df_reel_material.merge(df_RMData.loc[:,['料號','中文名稱','COST_2','塗料淨量率']],on='料號',how='left')
                    df_reel_material['RMN'] = df_reel_material['中文名稱'].copy()
                    df_reel_material['COST'] = df_reel_material['COST_2'].copy()
                    df_reel_material['COST'] = df_reel_material['COST'] * df_reel_material['主要數量'] * (-1.0)

                    df_reel_material = df_reel_material.merge(df_ptype_category.loc[:,['兩碼紙別','類別']].rename(columns={'兩碼紙別':'PN2','類別':'分類別'}),
                                                              on='PN2',how='left')

                    df_reel_material['PD'] = np.where(
                            df_reel_material['PN2'].isin(['K8','HI','HK','HL','HP','HQ','HR','HS','HU','HV','UQ','UR','US']),
                            '78',
                            np.where(
                                df_reel_material['PN2'].isin(['TD','TF','TR','TS','A017','A020']),
                                '95',
                                df_reel_material['號機']
                            )
                        )

                    mapping = {'CT': '塗料','CH': '化工','FB': '纖維','CY': '填料'}

                    df_reel_material['類別'] = df_reel_material['RM_Kind'].map(mapping)

                    df_reel_material['Nqty'] = np.where(
                        df_reel_material['RM_Kind'] == 'CT',
                        df_reel_material['KG'] * df_reel_material['塗料淨量率'] / 100.0,
                        df_reel_material['KG']
                    )

                    df_reel_material = df_reel_material.loc[:,['分類別', 'KG', 'BATCH_Sort', 'RM_Kind', 'RMN', '號機', 'PD', 'PN2', 'PN4', 'COST',
                           '料號', '異動日期', '主要數量', '主要單位', '工單', 'Nqty', 'BW', '類別']]        

                    # 創建日結_表格
                    df_material = df_reel_material.groupby(['PD','PN4','BW','類別'])['KG','Nqty'].sum().reset_index().pivot_table(
                        index=['PD', 'PN4', 'BW'],
                        columns='類別',
                        values=['Nqty', 'KG'],
                        aggfunc='sum',
                        fill_value=0
                    ).reset_index()

                    df_material.columns = [f'{val}_{col}' for val, col in df_material.columns]
                    df_material = df_material.reset_index(drop=True)
                    df_material = df_material.loc[:,['PD_', 'PN4_', 'BW_','Nqty_纖維','Nqty_塗料','Nqty_填料','Nqty_化工',
                                               'KG_纖維', 'KG_塗料','KG_填料','KG_化工']]

                    df_material.columns = ['PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', '纖維.1','塗料.1', '填料.1', '化工.1',]

                    mapping = {'18': 'PM18','19': 'PM19','20': 'PM20','21': 'PM21','78': 'NCR','95': '含浸'}

                    df_material['機台'] = df_material['PD'].map(mapping)

                    df_material['紙別成品基重'] = df_material['機台'] + df_material['PN4'] + df_material['BW'].astype(str)
                    df_material['紙別成品基重'] = df_material['紙別成品基重'].str.replace(r'\.0$', '', regex=True)

                    df_material = df_material.loc[:,['機台', '紙別成品基重', 'PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', 
                                                     '纖維.1','塗料.1', '填料.1', '化工.1']]        

                    # 計算初出紙用漿量
                    df_reel_material_first = df_reel_material[(df_reel_material['PN4'].isin(['1000','2000'])) &                                      (df_reel_material['RM_Kind'].isin(['FB']))]                                    .groupby(['號機','PN2','RM_Kind','料號','RMN'])['KG','Nqty','COST'].sum().reset_index()
                    df_reel_material_first['機台'] = 'PM' + df_reel_material_first['號機']        

                    # 讀取計算約當量(分攤前)
                    df_Equivalent_Output_Before_Apportionment['PN2'] = df_Equivalent_Output_Before_Apportionment['PN4'].apply(classify_pn4)
                    df_Equivalent_Output_Before_Apportionment['類別'] = df_Equivalent_Output_Before_Apportionment['PN2'].map(df_ptype_category.set_index('兩碼紙別')['類別'])

                    df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['機台'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['PN4'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['基重'].astype(str)

                    df_Equivalent_Output_Before_Apportionment['塗前期初在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗後期初在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗前期末在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                       df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗後期末在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                       df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['入庫量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_Inventory[df_Inventory['年月'] == etime].reset_index(drop=True).set_index('紙別基重')['合計(kg)']/1000.0
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment.loc[
                        df_Equivalent_Output_Before_Apportionment['PN2'].isin(['QE', 'QC']),
                        ['塗前期初在產品(噸)', '塗後期初在產品(噸)','塗前期末在產品(噸)','塗後期末在產品(噸)']
                    ] = None

                    df_Equivalent_Output_Before_Apportionment['塗前約當量(噸)'] = (df_Equivalent_Output_Before_Apportionment['塗前期末在產品(噸)'] -                                                                    df_Equivalent_Output_Before_Apportionment['塗前期初在產品(噸)']).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗後約當量(噸)'] = (df_Equivalent_Output_Before_Apportionment['入庫量(噸)'] +                                                                    df_Equivalent_Output_Before_Apportionment['塗後期末在產品(噸)'].fillna(0) -                                                                    df_Equivalent_Output_Before_Apportionment['塗後期初在產品(噸)'].fillna(0)).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗前塗佈克數(g)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_coatingweight.drop_duplicates(subset='紙別原紙基重').reset_index(drop=True).set_index('紙別原紙基重')['機上\n塗佈(g)'].rename_axis('紙別成品基重')
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment.loc[df_Equivalent_Output_Before_Apportionment['塗前約當量(噸)']==0,'塗前塗佈克數(g)'] = 0

                    df_Equivalent_Output_Before_Apportionment['塗後塗佈克數(g)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_coatingweight.drop_duplicates(subset='紙別成品基重').reset_index(drop=True).set_index('紙別成品基重')['塗佈合計(g)']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['理論塗佈產量(噸)'] = df_Equivalent_Output_Before_Apportionment.apply(
                        lambda row: (
                            (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                            (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                        ) if row['基重'] not in [0, None, np.nan] else 0,
                        axis=1
                    )

                    df_Equivalent_Output_Before_Apportionment['理論填料產量(噸)'] = df_Equivalent_Output_Before_Apportionment.apply(
                        lambda row: (
                            (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                            (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                        ) if row['基重'] not in [0, None, np.nan] else 0,
                        axis=1
                    )

                    df_Equivalent_Output_Before_Apportionment['理論填料產量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['填料']*0.75/1000
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['理論纖維產量(噸)'] = df_Equivalent_Output_Before_Apportionment['塗前約當量(噸)'] +                                                                    df_Equivalent_Output_Before_Apportionment['塗後約當量(噸)'] -                                                                    df_Equivalent_Output_Before_Apportionment['理論塗佈產量(噸)'] -                                                                    df_Equivalent_Output_Before_Apportionment['理論填料產量(噸)']

                    df_Equivalent_Output_Before_Apportionment['塗料領用量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['塗料']/1000
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['填料領用量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['填料']/1000
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['纖維領用量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['纖維']/1000
                    ).fillna(0)  

                    # 讀取損紙攤提比重
                    df_Broken_paper_amortization_ratio_table = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\紙機損紙_初出紙用漿.xlsx',
                                              sheet_name='損紙攤提比重',skiprows=0)
                    df_Broken_paper_amortization_ratio_table = df_Broken_paper_amortization_ratio_table.iloc[:,1:4]

                    # 開始計算攤提
                    df_Broken_paper_amortization_ratio = df_Equivalent_Output_Before_Apportionment                                                        [~df_Equivalent_Output_Before_Apportionment['機台'].isin(['NCR','含浸'])]
                    df_Broken_paper_amortization_ratio =                             df_Broken_paper_amortization_ratio.merge(df_Broken_paper_amortization_ratio_table,on=['機台','PN2'],how='left')                            .loc[:,['機台','PN4','基重','損紙攤提比重','塗前約當量(噸)','塗後約當量(噸)','纖維領用量(噸)']]

                    df_Broken_paper_amortization_ratio['攤提基準(纖維用量)'] = df_Broken_paper_amortization_ratio['損紙攤提比重'] *                                                                               df_Broken_paper_amortization_ratio['纖維領用量(噸)']

                    df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)'] = np.where(
                        df_Broken_paper_amortization_ratio['攤提基準(纖維用量)']<0,
                        0,
                        df_Broken_paper_amortization_ratio['攤提基準(纖維用量)']
                    )

                    df_Broken_paper_amortization_ratio_sum = df_Broken_paper_amortization_ratio.groupby(['機台'])['攤提基準(約當量)(排除負纖維產量)'].sum().reset_index()
                    df_Broken_paper_amortization_ratio_sum.columns = ['機台','攤提基準(約當量)(排除負纖維產量)加總']

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_Broken_paper_amortization_ratio_sum,on='機台')

                    df_Broken_paper_amortization_ratio['佔比(纖維產量)'] = np.where(
                        df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)加總']==0,
                        0,
                        df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)'] / df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)加總']
                    )

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio[df_Broken_paper_amortization_ratio['佔比(纖維產量)']>0].reset_index(drop=True)


                    df_reel_material_first_pivot = df_reel_material_first.loc[:,['機台','料號','KG']].pivot_table(
                        index=['機台'],
                        columns='料號',
                        values=['KG'],
                        aggfunc='sum',
                        fill_value=0
                    ).reset_index()

                    df_reel_material_first_pivot.columns = [f'{val}_{col}' for val, col in df_reel_material_first_pivot.columns]

                    df_reel_material_first_pivot.rename(columns={'機台_':'機台'},inplace=True)
                    df_reel_material_first_pivot.columns = df_reel_material_first_pivot.columns.str.replace('^KG_', '', regex=True)

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_reel_material_first_pivot,on='機台',how='left')

                    for col in df_reel_material_first_pivot.columns[1:]:
                        df_Broken_paper_amortization_ratio[col] = df_Broken_paper_amortization_ratio[col] *                                                                  df_Broken_paper_amortization_ratio['佔比(纖維產量)'] * -1

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.groupby(['機台','PN4','基重'])[list(df_reel_material_first_pivot.columns[1:])].sum().reset_index()

                    df_Broken_paper_amortization_ratio[[col for col in df_reel_material_first_pivot.columns if col.endswith('P')]] =                     df_Broken_paper_amortization_ratio[[col for col in df_reel_material_first_pivot.columns if col.endswith('P')]] / 1000.0

                    df_Broken_paper_amortization_ratio = pd.melt(df_Broken_paper_amortization_ratio,
                            id_vars=['機台','PN4','基重'],
                            var_name = '料號',
                            value_name = '主要數量'
                    )

                    df_Broken_paper_amortization_ratio['號機'] = df_Broken_paper_amortization_ratio['機台'].str[2:]
                    df_Broken_paper_amortization_ratio['PN2'] = df_Broken_paper_amortization_ratio['PN4'].str[:2]
                    df_Broken_paper_amortization_ratio.rename(columns={'基重':'BW'},inplace=True)
                    df_Broken_paper_amortization_ratio['RM_Kind'] = df_Broken_paper_amortization_ratio['料號'].apply(RM_Kind_mapping)
                    df_Broken_paper_amortization_ratio['主要單位'] = np.where(
                        df_Broken_paper_amortization_ratio['料號'].str.endswith('P'),
                        'ADT',
                        'KG'
                    )
                    df_Broken_paper_amortization_ratio['BATCH_Sort'] = 'JB'

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_RMData.loc[:,['料號','中文名稱','COST_2','塗料淨量率']],on='料號',how='left')
                    df_Broken_paper_amortization_ratio['RMN'] = df_Broken_paper_amortization_ratio['中文名稱'].copy()
                    df_Broken_paper_amortization_ratio['COST'] = df_Broken_paper_amortization_ratio['COST_2'].copy()
                    df_Broken_paper_amortization_ratio['COST'] = df_Broken_paper_amortization_ratio['COST'] * df_Broken_paper_amortization_ratio['主要數量'] * (-1.0)

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_ptype_category.loc[:,['兩碼紙別','類別']].rename(columns={'兩碼紙別':'PN2','類別':'分類別'}),
                                                              on='PN2',how='left')

                    df_Broken_paper_amortization_ratio['PD'] = df_Broken_paper_amortization_ratio['號機']

                    mapping = {'CT': '塗料','CH': '化工','FB': '纖維','CY': '填料'}

                    df_Broken_paper_amortization_ratio['類別'] = df_Broken_paper_amortization_ratio['RM_Kind'].map(mapping)

                    df_Broken_paper_amortization_ratio['KG'] = np.where(
                        df_Broken_paper_amortization_ratio['主要單位'] == 'KG',
                        df_Broken_paper_amortization_ratio['主要數量'] * (-1),
                        df_Broken_paper_amortization_ratio['主要數量'] * (-1) * 1000
                    )

                    df_Broken_paper_amortization_ratio['Nqty'] = np.where(
                        df_Broken_paper_amortization_ratio['RM_Kind'] == 'CT',
                        df_Broken_paper_amortization_ratio['KG'] * df_Broken_paper_amortization_ratio['塗料淨量率'] / 100.0,
                        df_Broken_paper_amortization_ratio['KG']
                    )

                    df_Broken_paper_amortization_ratio['異動日期'] = np.nan
                    df_Broken_paper_amortization_ratio['工單'] = np.nan

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.loc[:,['分類別', 'KG', 'BATCH_Sort', 'RM_Kind', 'RMN', '號機', 'PD', 'PN2', 'PN4', 'COST',
                           '料號', '異動日期', '主要數量', '主要單位', '工單', 'Nqty', 'BW', '類別']]        

                    # 更新 原物料 用量 Data_
                    df_reel_material = pd.concat([df_reel_material,df_Broken_paper_amortization_ratio],ignore_index=True)     

                    return df_reel_material    
                
            # --------成本單這裡開始--------
            start_time = time.time()
            

            # 讀取期末在產品
#             df_End_work_in_process_current_period = search_InProcess_MES(etime)
#             df_End_work_in_process_current_period = Work_In_Process(df_End_work_in_process_current_period)

#             df_End_work_in_process_Last_period = search_InProcess_MES(stime)
#             df_End_work_in_process_Last_period = Work_In_Process(df_End_work_in_process_Last_period)

#             df_End_work_in_process_current_period = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
#                                       sheet_name='期末在產品_'+etime,skiprows=1)
            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                   
                    sql =   """
                        SELECT * FROM [CostSheet].[dbo].[End_work_in_process] WHERE [年月] = '"""+ str(etime) +"""'
                    """       
                    query = conn.execute(text(sql))  
                    df_End_work_in_process_current_period = pd.DataFrame([dict(i) for i in query])
                if df_End_work_in_process_current_period.empty:
                    df_End_work_in_process_current_period = search_InProcess_MES(etime)
                    df_End_work_in_process_current_period = Work_In_Process(df_End_work_in_process_current_period)
            except:
                df_End_work_in_process_current_period = search_InProcess_MES(etime)
                df_End_work_in_process_current_period = Work_In_Process(df_End_work_in_process_current_period)

#             if etime == '202501':
#                 df_End_work_in_process_Last_period = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
#                                           sheet_name='期初在產品_'+stime,skiprows=1)
#             else:
#                 df_End_work_in_process_Last_period = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
#                                           sheet_name='期末在產品_'+stime,skiprows=1)

            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                  
                    sql =   """
                        SELECT * FROM [CostSheet].[dbo].[End_work_in_process] WHERE [年月] = '"""+ str(stime) +"""'
                    """       
                    query = conn.execute(text(sql))  
                    df_End_work_in_process_Last_period = pd.DataFrame([dict(i) for i in query])
                if df_End_work_in_process_Last_period.empty:
                    df_End_work_in_process_Last_period = search_InProcess_MES(stime)
                    df_End_work_in_process_Last_period = Work_In_Process(df_End_work_in_process_Last_period)
            except:
                df_End_work_in_process_Last_period = search_InProcess_MES(stime)
                df_End_work_in_process_Last_period = Work_In_Process(df_End_work_in_process_Last_period)   
        
            elapsed = time.time() - start_time
            logging.info(f"Work_In_Process time is: {elapsed:.2f} seconds")        
            
#             if etime =='202505':
#                 df_End_work_in_process_current_period.loc[df_End_work_in_process_current_period['紙別'] == 'A800','紙別基重(塗前)'] = 'PM21A800100'
#                 df_End_work_in_process_current_period.loc[df_End_work_in_process_current_period['紙別'] == 'KYC2','紙別基重(塗前)'] = 'PM21KYC2120'
#                 df_End_work_in_process_current_period.loc[df_End_work_in_process_current_period['紙別'] == 'KYC3','紙別基重(塗前)'] = 'PM21KYC3120'            

            # 讀取紙別分類
            start_time = time.time()
        
            try:
                df_ptype_category = pd.read_excel(r'E:\AP\Api\dist\計算約當量_2025_分類別.xlsx',
                                          sheet_name='紙別分類',skiprows=0)                
            except:
                df_ptype_category = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
                                          sheet_name='紙別分類',skiprows=0)

            df_ptype_category = df_ptype_category.iloc[1:115,[14,15,16,18]].reset_index(drop=True)
            df_ptype_category.iloc[0,3] = '類別'            
            df_ptype_category.columns = df_ptype_category.iloc[0]
            df_ptype_category = df_ptype_category[1:].reset_index(drop=True)

            # 讀取入庫量
            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                  
                    sql =   """
                        SELECT * FROM [CostSheet].[dbo].[ERP_Inventory] WHERE [年月] = '"""+ str(etime) +"""'
                    """       
                    query = conn.execute(text(sql))  
                    df_Inventory = pd.DataFrame([dict(i) for i in query])
                if df_Inventory.empty:
                    df_Inventory = search_Inventory_MES(etime)
            except:
                df_Inventory = search_Inventory_MES(etime)
                
            elapsed = time.time() - start_time
            logging.info(f"Inventory time is: {elapsed:.2f} seconds")         

            start_time = time.time()
            # 讀取塗佈克數
            try:
                df_coatingweight = pd.read_excel(r'E:\AP\Api\dist\計算約當量_2025_分類別.xlsx',
                                          sheet_name='塗佈克數_data',skiprows=0)                
            except:            
                df_coatingweight = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
                                          sheet_name='塗佈克數_data',skiprows=0)
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_1 time is: {elapsed:.2f} seconds")             
            
            # 讀取範例schema檔案
            start_time = time.time()
            try:
                df_mname_ptype_gramg_schema = pd.read_excel(r'E:\AP\Api\dist\計算約當量_2025_分類別.xlsx',
                                      sheet_name='計算約當量_202504',skiprows=0)                
            except:                 
                df_mname_ptype_gramg_schema = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
                                      sheet_name='計算約當量_202504',skiprows=0)
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_2 time is: {elapsed:.2f} seconds")
            
            start_time = time.time()

            dt = datetime.datetime.strptime(etime, "%Y%m")
            etime_t = (dt + relativedelta(months=1) - timedelta(days=1))

            df_mname_ptype_gramg_schema = df_mname_ptype_gramg_schema.loc[:df_mname_ptype_gramg_schema[df_mname_ptype_gramg_schema['類別'].isna()].head(1).index[0]-1,:]            
            df_mname_ptype_gramg_schema['年'] = etime_t.year
            df_mname_ptype_gramg_schema['月'] = etime_t.month
            df_mname_ptype_gramg_schema['日'] = etime_t.day
            df_mname_ptype_gramg_schema = df_mname_ptype_gramg_schema.loc[:,['年', '月', '日', '機台', 'PN4', '基重']]
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_3 time is: {elapsed:.2f} seconds")
            
            start_time = time.time()

            # 找出不在舊資料的四碼紙別基重
            df_mname_ptype_gramg_schema_new = pd.concat([
                df_End_work_in_process_Last_period.loc[:,['號機','紙別', '基重(成品)']],
                df_End_work_in_process_current_period.loc[:,['號機','紙別', '基重(成品)']],
                df_Inventory.rename(columns={'PN4':'紙別','基重':'基重(成品)','機台':'號機'}).loc[:,['號機','紙別', '基重(成品)']]
            ],ignore_index=True
            ).drop_duplicates()

            df_mname_ptype_gramg_schema_new = df_mname_ptype_gramg_schema_new.merge(df_mname_ptype_gramg_schema,left_on=['號機','紙別', '基重(成品)'],
                                                  right_on=['機台','PN4', '基重'],how='left')
            df_mname_ptype_gramg_schema_new = df_mname_ptype_gramg_schema_new[df_mname_ptype_gramg_schema_new['年'].isna()].reset_index(drop=True)
            df_mname_ptype_gramg_schema_new = df_mname_ptype_gramg_schema_new.loc[:,['號機','紙別', '基重(成品)']]
            df_mname_ptype_gramg_schema_new['年'] = etime_t.year
            df_mname_ptype_gramg_schema_new['月'] = etime_t.month
            df_mname_ptype_gramg_schema_new['日'] = etime_t.day
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_4 time is: {elapsed:.2f} seconds")
            
            start_time = time.time()
            
            def convert_weight(x):
                try:
                    x_float = float(x)
                    if x_float.is_integer():
                        return int(x_float)  # 轉成 int
                    else:
                        return round(x_float, 1)  # 精確到小數一位
                except Exception as e:
                    return x  # 如果轉換失敗就原值保留

            converted = [convert_weight(x) for x in df_mname_ptype_gramg_schema_new['基重(成品)']]
            df_mname_ptype_gramg_schema_new['基重(成品)'] = pd.Series(converted, dtype='object')            

            df_Equivalent_Output_Before_Apportionment = pd.concat([df_mname_ptype_gramg_schema,
                       df_mname_ptype_gramg_schema_new.rename(columns={'紙別':'PN4','基重(成品)':'基重','號機':'機台'})],ignore_index=True).drop_duplicates().reset_index(drop=True)               

            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_5 time is: {elapsed:.2f} seconds") 
            
            start_time = time.time()             
            
            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                
                    sql =   """
                        SELECT [分類別],[KG],[BATCH_Sort],[RM_Kind],[RMN],[號機],[PD],[PN2],[PN4],[COST],[料號],
                                [異動日期],[主要數量],[主要單位],[工單],[Nqty],[BW],[類別]
                          FROM [CostSheet].[dbo].[ERP_Inventory_Material]
                          WHERE [年月] = '"""+ str(etime) +"""'
                    """       
                    query = conn.execute(text(sql))
                    df_reel_material = pd.DataFrame([dict(i) for i in query])

                    df_Equivalent_Output_Before_Apportionment['PN2'] = df_Equivalent_Output_Before_Apportionment['PN4'].apply(classify_pn4)
                    df_Equivalent_Output_Before_Apportionment['類別'] = df_Equivalent_Output_Before_Apportionment['PN2'].map(df_ptype_category.set_index('兩碼紙別')['類別'])        

                    df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['機台'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['PN4'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['基重'].astype(str)        
                if df_reel_material.empty:
                    df_reel_material = material_data(etime,df_Equivalent_Output_Before_Apportionment)
            except:
                df_reel_material = material_data(etime,df_Equivalent_Output_Before_Apportionment)
            
            # 讀取原物料日結
            df_material = df_reel_material.groupby(['PD','PN4','BW','類別'])['KG','Nqty'].sum().reset_index().pivot_table(
                index=['PD', 'PN4', 'BW'],
                columns='類別',
                values=['Nqty', 'KG'],
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            df_material.columns = [f'{val}_{col}' for val, col in df_material.columns]
            df_material = df_material.reset_index(drop=True)
            df_material = df_material.loc[:,['PD_', 'PN4_', 'BW_','Nqty_纖維','Nqty_塗料','Nqty_填料','Nqty_化工',
                                       'KG_纖維', 'KG_塗料','KG_填料','KG_化工']]

            df_material.columns = ['PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', '纖維.1','塗料.1', '填料.1', '化工.1',]

            mapping = {'18': 'PM18','19': 'PM19','20': 'PM20','21': 'PM21','78': 'NCR','95': '含浸'}

            df_material['機台'] = df_material['PD'].map(mapping)

            df_material['紙別成品基重'] = df_material['機台'] + df_material['PN4'] + df_material['BW'].astype(str)
            df_material['紙別成品基重'] = df_material['紙別成品基重'].str.replace(r'\.0$', '', regex=True)

            df_material = df_material.loc[:,['機台', '紙別成品基重', 'PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', 
                                             '纖維.1','塗料.1', '填料.1', '化工.1']]
            
            elapsed = time.time() - start_time
            logging.info(f"df_material time is: {elapsed:.2f} seconds")            

            # 讀取原物料 原紙耗用
            start_time = time.time() 
            
            stime_d = (datetime.datetime.strptime(etime, "%Y%m")).strftime('%Y-%m-%d')
            etime_d = (datetime.datetime.strptime(etime, "%Y%m") + relativedelta(months=1)  - timedelta(days=1)).strftime('%Y-%m-%d')
            
            srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
            with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:                            
                sql =   """
                ;With raw_data as
                (
                    SELECT *
                    FROM
                    (
                    SELECT [RXID]
                            ,[PREVIOUS_RXID]
                            ,[BATCH_NO]
                            ,[ITEM_NO]
                        ,SUBSTRING([ITEM_NO],2,4) as ptype
                        ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                        ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                        ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                            ,[SUBINVENTORY_CODE]
                            ,[LOCATOR]
                            ,[TRANSACTION_QUANTITY]
                            ,[TRANSACTION_UOM]
                            ,[SECONDARY_TRANSACTION_QUANTITY]
                            ,[SECONDARY_UOM_CODE]
                            ,[TRANSACTION_DATE]
                            ,[STATUS]
                        FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P210_IN_MMT_INGR_ST]
                        WHERE 1=1
                        AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime_d) +"""' and '"""+ str(etime_d) +"""'
                        AND [STATUS_CODE] = 'S'
                    ) s
                    WHERE 1=1
                    AND (ptype like '%NCR' or ptype like 'MM%') AND length  = 'R'
                )
                SELECT PN4,BW,[原紙紙別],SUM([紙用量(kg)]) AS 合計 FROM
                (
                    SELECT t.BATCH_NO,SUBSTRING(MAX(P250.[ITEM_NO]),2,4) as PN4,CAST(SUBSTRING(MAX(P250.[ITEM_NO]),7,5) AS INT) / 10.0 as BW,
                    MAX(t.ptype) 原紙紙別, MAX(t.gramg) / 10.0 原紙基重, MAX(t.[TRANSACTION_QUANTITY]) AS [紙用量(kg)]
                    FROM
                    (
                        SELECT BATCH_NO,ptype,gramg,sum([TRANSACTION_QUANTITY]) AS [TRANSACTION_QUANTITY]
                        FROM
                        (
                            SELECT * FROM raw_data
                            WHERE RXID NOT IN (SELECT DISTINCT PREVIOUS_RXID FROM raw_data WHERE PREVIOUS_RXID is not null)
                        ) s
                        WHERE 1=1
                        GROUP BY BATCH_NO,ptype,gramg
                    ) t
                    LEFT JOIN [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST] P250 ON t.BATCH_NO = P250.BATCH_NO 
                    GROUP BY t.BATCH_NO
                ) n
                WHERE PN4 IS NOT NULL AND BW IS NOT NULL
                GROUP BY PN4,BW,[原紙紙別]
                """       
                query = conn.execute(text(sql))
                df_reel_consume = pd.DataFrame([dict(i) for i in query])

            df_reel_consume['BW'] = df_reel_consume['BW'].astype(int)

            df_reel_consume['紙別成品基重'] = np.where(
                df_reel_consume['原紙紙別'].str.startswith('MM'),
                '含浸' + df_reel_consume['PN4']+ df_reel_consume['BW'].astype(str),
                np.where(
                    df_reel_consume['原紙紙別'].str.endswith('NCR'),
                    'NCR' + df_reel_consume['PN4']+ df_reel_consume['BW'].astype(str),
                    ''
                )
            )
            
            df_reel_consume = df_reel_consume.drop_duplicates(
                subset='紙別成品基重', keep='first'
            ).reset_index(drop=True)
            
            elapsed = time.time() - start_time
            logging.info(f"df_reel_consume time is: {elapsed:.2f} seconds") 
            
            
            start_time = time.time()
            
            # 讀取計算約當量
            df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].astype(str).str.replace(r'\.0$', '', regex=True)
            
            df_Equivalent_Output_current_period = df_Equivalent_Output_Before_Apportionment.loc[:,['年', '月', '日', '機台', 'PN4', '基重','PN2','類別','紙別成品基重']]

            df_Equivalent_Output_current_period['塗前期初在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
            ).fillna(0)

            df_Equivalent_Output_current_period['塗後期初在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
            ).fillna(0)

            df_Equivalent_Output_current_period['塗前期末在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
               df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
            ).fillna(0)

            df_Equivalent_Output_current_period['塗後期末在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
               df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
            ).fillna(0)

            df_Equivalent_Output_current_period['入庫量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_Inventory[df_Inventory['年月'] == etime].reset_index(drop=True).set_index('紙別基重')['合計(kg)']/1000.0
            ).fillna(0)

            df_Equivalent_Output_current_period.loc[
                df_Equivalent_Output_current_period['PN2'].isin(['QE', 'QC']),
                ['塗前期初在產品(噸)', '塗後期初在產品(噸)','塗前期末在產品(噸)','塗後期末在產品(噸)']
            ] = None

            df_Equivalent_Output_current_period['塗前約當量(噸)'] = (df_Equivalent_Output_current_period['塗前期末在產品(噸)'] -                                                            df_Equivalent_Output_current_period['塗前期初在產品(噸)']).fillna(0)

            df_Equivalent_Output_current_period['塗後約當量(噸)'] = (df_Equivalent_Output_current_period['入庫量(噸)'] +                                                            df_Equivalent_Output_current_period['塗後期末在產品(噸)'].fillna(0) -                                                            df_Equivalent_Output_current_period['塗後期初在產品(噸)'].fillna(0)).fillna(0)

            df_Equivalent_Output_current_period['塗前塗佈克數(g)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_coatingweight.drop_duplicates(subset='紙別原紙基重').reset_index(drop=True).set_index('紙別原紙基重')['機上\n塗佈(g)'].rename_axis('紙別成品基重')
            ).fillna(0)

            df_Equivalent_Output_current_period.loc[df_Equivalent_Output_current_period['塗前約當量(噸)']==0,'塗前塗佈克數(g)'] = 0

            df_Equivalent_Output_current_period['塗後塗佈克數(g)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_coatingweight.drop_duplicates(subset='紙別成品基重').reset_index(drop=True).set_index('紙別成品基重')['塗佈合計(g)']
            ).fillna(0)

            df_Equivalent_Output_current_period['理論塗佈產量(噸)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                    (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                ) if row['基重'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_Equivalent_Output_current_period['理論填料產量(噸)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                    (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                ) if row['基重'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_Equivalent_Output_current_period['理論填料產量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['填料']*0.75/1000
            ).fillna(0)

            df_Equivalent_Output_current_period['理論纖維產量(噸)'] = df_Equivalent_Output_current_period['塗前約當量(噸)'] +                                                            df_Equivalent_Output_current_period['塗後約當量(噸)'] -                                                            df_Equivalent_Output_current_period['理論塗佈產量(噸)'] -                                                            df_Equivalent_Output_current_period['理論填料產量(噸)']

            df_Equivalent_Output_current_period['塗料領用量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['塗料']/1000
            ).fillna(0)

            df_Equivalent_Output_current_period['填料領用量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['填料']/1000
            ).fillna(0)

            df_Equivalent_Output_current_period['纖維領用量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['纖維']/1000
            ).fillna(0)

            df_Equivalent_Output_current_period.loc[df_Equivalent_Output_current_period['機台'].isin(['NCR','含浸']),'纖維領用量(噸)'] =                 df_Equivalent_Output_current_period.loc[df_Equivalent_Output_current_period['機台'].isin(['NCR','含浸']),'紙別成品基重'].map(
                    df_reel_consume.set_index('紙別成品基重')['合計']/1000
                ).fillna(0)


            df_Equivalent_Output_current_period['纖維得率(%)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_Equivalent_Output_current_period['塗料得率(%)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped = df_Equivalent_Output_current_period.groupby(['機台','PN2'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            # 對「機台」套用排序規則
            df_grouped['機台'] = pd.Categorical(df_grouped['機台'], categories=custom_order, ordered=True)

            # 再排序
            df_grouped = df_grouped.sort_values(['機台', 'PN2']).reset_index(drop=True)

            # df_grouped[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']] = df_grouped[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']].round(2)

            df_grouped = df_grouped.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped_2 = df_Equivalent_Output_current_period.groupby(['機台','類別'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            # 對「機台」套用排序規則
            df_grouped_2['機台'] = pd.Categorical(df_grouped_2['機台'], categories=custom_order, ordered=True)

            # 再排序
            df_grouped_2 = df_grouped_2.sort_values(['機台', '類別']).reset_index(drop=True)

#             df_grouped_2[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']] = df_grouped_2[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']].round(2)

            df_grouped_2 = df_grouped_2.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            df_grouped_2['纖維得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped_2['塗料得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped_2['填料得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論填料產量(噸)'] / row['填料領用量(噸)'])
                ) if row['填料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )


            df_grouped['纖維得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped['塗料得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped['填料得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論填料產量(噸)'] / row['填料領用量(噸)'])
                ) if row['填料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )
            
            def adjust_columns(df):
                cond = ((df['塗前約當量(噸)'] + df['塗後約當量(噸)']) > 0) & (df['纖維領用量(噸)'] == 0)
                for col in ['塗前約當量(噸)', '塗後約當量(噸)']:
                    df[col] = np.where(cond, 0, df[col])
                return df

            # 套用在兩個 DataFrame 上
            df_grouped = adjust_columns(df_grouped)
            df_grouped_2 = adjust_columns(df_grouped_2)
            
            elapsed = time.time() - start_time
            logging.info(f"df_grouped_2 time is: {elapsed:.2f} seconds")

            start_time = time.time() 

            df_Product_cost_schedule = pd.DataFrame(columns=[
                '月份','機台','類別','紙別','生產量(噸)','纖維得率','纖維配合率','填料得率','填料配合率','塗料得率','塗料配合率'
            ])

            df_Product_cost_schedule.loc[0,'機台'] = mname
            df_Product_cost_schedule.loc[0,'類別'] = Product_Category
            df_Product_cost_schedule.loc[0,'紙別'] = Product_two_ptype
            df_Product_cost_schedule.loc[0,'月份'] = etime

            if Product_two_ptype == '':
                df_Product_cost_schedule.loc[0,'生產量(噸)'] = df_grouped_2.loc[(df_grouped_2['類別']==Product_Category) &                                                                             (df_grouped_2['機台']==mname),
                                                                            ['塗前約當量(噸)','塗後約當量(噸)']].sum(axis=1).item()
                df_Product_cost_schedule.loc[0,'纖維得率'] = (df_grouped_2.loc[(df_grouped_2['類別']==Product_Category) &                                                                            (df_grouped_2['機台']==mname),
                                                                         '纖維得率(%)']*100).item()
                df_Product_cost_schedule.loc[0,'填料得率'] = (df_grouped_2.loc[(df_grouped_2['類別']==Product_Category) &                                                                             (df_grouped_2['機台']==mname),
                                                                         '填料得率(%)']*100).item()
                df_Product_cost_schedule.loc[0,'塗料得率'] = (df_grouped_2.loc[(df_grouped_2['類別']==Product_Category) &                                                                             (df_grouped_2['機台']==mname),
                                                                         '塗料得率(%)']*100).item()
                if df_Product_cost_schedule.loc[0,'生產量(噸)']!=0:   
                    df_Product_cost_schedule.loc[0,'塗料配合率'] = (df_grouped_2.loc[(df_grouped_2['類別']==Product_Category) &                                                                                 (df_grouped_2['機台']==mname),
                                                                    '理論塗佈產量(噸)']).item() / df_Product_cost_schedule.loc[0,'生產量(噸)'] *100
                    df_Product_cost_schedule.loc[0,'填料配合率'] = (df_grouped_2.loc[(df_grouped_2['類別']==Product_Category) &                                                                                 (df_grouped_2['機台']==mname),
                                                                    '理論填料產量(噸)']).item() / df_Product_cost_schedule.loc[0,'生產量(噸)'] *100
                else:
                    df_Product_cost_schedule.loc[0,'塗料配合率'] = 0
                    df_Product_cost_schedule.loc[0,'填料配合率'] = 0
                    
                df_Product_cost_schedule.loc[0,'纖維配合率'] = 100 - df_Product_cost_schedule.loc[0,'填料配合率'] -                                                                  df_Product_cost_schedule.loc[0,'塗料配合率']
            else:
                try:
                    df_Product_cost_schedule.loc[0,'生產量(噸)'] = df_grouped.loc[(df_grouped['PN2']==Product_two_ptype) &                                                                                (df_grouped['機台']==mname),
                                                                                ['塗前約當量(噸)','塗後約當量(噸)']].sum(axis=1).item()
                    df_Product_cost_schedule.loc[0,'纖維得率'] = (df_grouped.loc[(df_grouped['PN2']==Product_two_ptype) &                                                                                (df_grouped['機台']==mname),
                                                                             '纖維得率(%)']*100).item()
                    df_Product_cost_schedule.loc[0,'填料得率'] = (df_grouped.loc[(df_grouped['PN2']==Product_two_ptype) &                                                                                (df_grouped['機台']==mname),
                                                                             '填料得率(%)']*100).item()
                    df_Product_cost_schedule.loc[0,'塗料得率'] = (df_grouped.loc[(df_grouped['PN2']==Product_two_ptype) &                                                                                (df_grouped['機台']==mname),
                                                                             '塗料得率(%)']*100).item()                    
                except:
                    df_Product_cost_schedule.loc[0,'生產量(噸)'] = 0
                    df_Product_cost_schedule.loc[0,'纖維得率'] = 0.0
                    df_Product_cost_schedule.loc[0,'填料得率'] = 0.0
                    df_Product_cost_schedule.loc[0,'塗料得率'] = 0.0

                if df_Product_cost_schedule.loc[0,'生產量(噸)']!=0:
                    df_Product_cost_schedule.loc[0,'塗料配合率'] = (df_grouped.loc[(df_grouped['PN2']==Product_two_ptype) &                                                                                (df_grouped['機台']==mname),
                                                                    '理論塗佈產量(噸)']).item() / df_Product_cost_schedule.loc[0,'生產量(噸)'] *100
                    df_Product_cost_schedule.loc[0,'填料配合率'] = (df_grouped.loc[(df_grouped['PN2']==Product_two_ptype) &                                                                                (df_grouped['機台']==mname),
                                                                    '理論填料產量(噸)']).item() / df_Product_cost_schedule.loc[0,'生產量(噸)'] *100
                else:
                    df_Product_cost_schedule.loc[0,'塗料配合率'] = 0
                    df_Product_cost_schedule.loc[0,'填料配合率'] = 0
                    
                df_Product_cost_schedule.loc[0,'纖維配合率'] = 100 - df_Product_cost_schedule.loc[0,'填料配合率'] -                                                                  df_Product_cost_schedule.loc[0,'塗料配合率']  
                

            # 讀取原物料 原料量
            if Product_two_ptype == '':
                # 分類別
                df_reel_material_grouped = df_reel_material.groupby(['PD','分類別','RM_Kind','料號','RMN'])                    .agg(a=('KG','sum'),
                         b=('Nqty','sum'),
                         c=('COST','sum'), 
                        )\
                    .reset_index()
            else:
                # 分紙別
                df_reel_material_grouped = df_reel_material.groupby(['PD','分類別','PN2','RM_Kind','料號','RMN'])                    .agg(a=('KG','sum'),
                         b=('Nqty','sum'),
                         c=('COST','sum'), 
                        )\
                    .reset_index()    

            df_reel_material_grouped = df_reel_material_grouped.rename(columns={
                'a': 'KG',
                'b': 'Nqty',
                'c': 'COST',
            })

            df_reel_material_grouped['單價(元/單價)'] = df_reel_material_grouped.apply(
                lambda row: (
                    (row['COST'] / row['KG'])
                ) if row['KG'] not in [0, None, np.nan] else 0,
                axis=1
            )
            
            df_reel_material_grouped['PD'] = df_reel_material_grouped['PD'].astype(float)

            # 四碼紙別        

            # 讀取原物料 原料量
            
            # 20250529 工費分攤 讀取單位成本
            # 抓能源單價
            try:
                df_cost_energy = pd.read_excel(r'E:\AP\Api\dist\工費與能源資料_'+str(etime[:4])+'年.xlsx',
                                          sheet_name='能源單價',skiprows=0)                
            except:                             
                try:
                    df_cost_energy = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供\工費與能源資料_'+str(etime[:4])+'年.xlsx',
                                              sheet_name='能源單價',skiprows=0)
                except:            
                    df_cost_energy = pd.read_excel(rf'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供\{etime[:4]}\工費與能源資料_{etime[:4]}年.xlsx',
                        sheet_name='能源單價',skiprows=0
                    )                    

            month_map = {
                '01': '1月','02': '2月','03': '3月','04': '4月','05': '5月','06': '6月','07': '7月',
                '08': '8月','09': '9月','10': '10月','11': '11月','12': '12月'
            }

            etime_cost_col = month_map.get(etime[4:], '未知月份')
            df_cost_energy = df_cost_energy.loc[:,[etime[:4] + '年',etime_cost_col]]

            # 抓取分攤基準 原始資料

            try:  
                file_path = r'E:\AP\Api\dist\工費與能源資料_'+str(etime[:4])+'年.xlsx'
                
                with pd.ExcelFile(file_path) as xls:
                    first_sheet_name = xls.sheet_names[0]
                    df_cost_sharing_raw = pd.read_excel(xls, sheet_name=first_sheet_name, skiprows=1)             
            except:                    
                try:
                    file_path = r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供\工費與能源資料_'+str(etime[:4])+'年.xlsx'

                    with pd.ExcelFile(file_path) as xls:
                        first_sheet_name = xls.sheet_names[0]
                        df_cost_sharing_raw = pd.read_excel(xls, sheet_name=first_sheet_name, skiprows=1)
                except:
                    file_path = rf'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供\{etime[:4]}\工費與能源資料_{etime[:4]}年.xlsx'

                    with pd.ExcelFile(file_path) as xls:
                        first_sheet_name = xls.sheet_names[0]
                        df_cost_sharing_raw = pd.read_excel(xls, sheet_name=first_sheet_name, skiprows=1)                    
                
            df_cost_sharing_raw = df_cost_sharing_raw[~df_cost_sharing_raw['DP_Code'].isna()]          

            # 抓取分攤基準 機台紙別
            try:
                df_cost_sharing_rule = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                          sheet_name='分攤原則',skiprows=1)                
            except:      
                df_cost_sharing_rule = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                          sheet_name='分攤原則',skiprows=1)
                
            mask = df_cost_sharing_rule["流程\n(被分攤)"].isin(["調成", "紙機"])
            df_cost_sharing_rule.loc[mask, "分攤基準"] = df_cost_sharing_rule.loc[mask, "分攤基準"].fillna(method="ffill")                
            
            if etime in ['202501','202502','202503','202504','202505']:
                try:
                    df_cost_sharing = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_'+etime,skiprows=1)                
                except:                      
                    df_cost_sharing = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_'+etime,skiprows=1)
            else:
                try:
                    df_cost_sharing = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202505',skiprows=1)                
                except:                  
                    df_cost_sharing = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202505',skiprows=1)

            df_cost_sharing = df_cost_sharing.loc[:df_cost_sharing[df_cost_sharing['被分攤部門'].isna()].head(1).index[0]-1,
                                                  ['被分攤部門','分攤部門','機台','紙別','基準']]

            df_cost_sharing['__sort_index'] = range(len(df_cost_sharing))
            df_cost_sharing = df_cost_sharing.merge(df_ptype_category.loc[:,['兩碼紙別','類別']],left_on='紙別',right_on='兩碼紙別')

            df_cost_sharing = df_cost_sharing.loc[:,['類別','被分攤部門','分攤部門','機台','紙別','基準','__sort_index']]
           
            # 未online部分---
            try:
                df_cost_sharing_base_temp = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202501',skiprows=3,header=1)                
            except:              
                df_cost_sharing_base_temp = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202501',skiprows=3,header=1)
            df_cost_sharing_base_temp['年月'] = '202501'
            df_cost_sharing_base = df_cost_sharing_base_temp.loc[~df_cost_sharing_base_temp['日產能'].isna(),['機台PN2','機台','PN2','日產能','年月']]

            try:
                df_cost_sharing_base_temp = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202502',skiprows=2,header=2)                
            except:              
                df_cost_sharing_base_temp = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202502',skiprows=2,header=2)
            df_cost_sharing_base_temp['年月'] = '202502'
            df_cost_sharing_base = pd.concat([df_cost_sharing_base,
                                             df_cost_sharing_base_temp.loc[~df_cost_sharing_base_temp['日產能'].isna(),['機台PN2','機台','PN2','日產能','年月']]],
                                            ignore_index=True)
            try:
                df_cost_sharing_base_temp = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202503',skiprows=2,header=2)                
            except:              
                df_cost_sharing_base_temp = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202503',skiprows=2,header=2)
            df_cost_sharing_base_temp['年月'] = '202503'
            df_cost_sharing_base = pd.concat([df_cost_sharing_base,
                                             df_cost_sharing_base_temp.loc[~df_cost_sharing_base_temp['日產能'].isna(),['機台PN2','機台','PN2','日產能','年月']]],
                                            ignore_index=True)

            try:
                df_cost_sharing_base_temp = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202504',skiprows=4,header=2)                
            except:              
                df_cost_sharing_base_temp = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202504',skiprows=4,header=2)
            df_cost_sharing_base_temp['年月'] = '202504'
            df_cost_sharing_base = pd.concat([df_cost_sharing_base,
                                             df_cost_sharing_base_temp.loc[~df_cost_sharing_base_temp['日產能'].isna(),['機台PN2','機台','PN2','日產能','年月']]],
                                            ignore_index=True)
            
            try:
                df_cost_sharing_base_temp = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202505',skiprows=5,header=2)                
            except:              
                df_cost_sharing_base_temp = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='分攤基準_202505',skiprows=5,header=2)
            df_cost_sharing_base_temp['年月'] = '202505'
            df_cost_sharing_base = pd.concat([df_cost_sharing_base,
                                             df_cost_sharing_base_temp.loc[~df_cost_sharing_base_temp['日產能'].isna(),['機台PN2','機台','PN2','日產能','年月']]],
                                            ignore_index=True)            

            df_cost_sharing_base = df_cost_sharing_base[~df_cost_sharing_base['PN2'].isna()]

            df_cost_sharing_base = (
                df_cost_sharing_base.sort_values(by='年月', ascending=False)
                  .drop_duplicates(subset=['機台PN2','機台', 'PN2'])
                  .reset_index(drop=True)
            ).loc[:,['機台PN2','機台','PN2','日產能']]

            df_Inventory_temp = (df_Inventory.groupby(['機台','PN4'])['合計(kg)'].sum() / 1000.0).reset_index()
            df_Inventory_temp['PN2'] = df_Inventory_temp['PN4'].str[:2]
            df_Inventory_temp['入庫量'] = df_Inventory_temp['合計(kg)']

            df_cost_sharing = df_cost_sharing.loc[:,['類別','被分攤部門','分攤部門','機台','紙別','__sort_index']].merge(
                df_cost_sharing_base,left_on=['機台','紙別'],right_on=['機台','PN2'],how='left').merge(
                df_grouped.loc[:,['機台','PN2','塗前約當量(噸)','塗後約當量(噸)','塗料領用量(噸)']],
                                        left_on=['機台','紙別'],right_on=['機台','PN2'],how='left').merge(
                df_Inventory_temp.groupby(['機台','PN2'])['入庫量'].sum().reset_index(),
                                        left_on=['機台','紙別'],right_on=['機台','PN2'],how='left').sort_values(by=['機台PN2'])

            df_cost_sharing = df_cost_sharing.loc[:,['類別','被分攤部門','分攤部門','機台','紙別',
                                                     '塗前約當量(噸)','塗後約當量(噸)','入庫量','塗料領用量(噸)','__sort_index']]
            
            if etime=='202505':
                df_cost_sharing.loc[df_cost_sharing['紙別']=='YA','塗料領用量(噸)'] = 0.0

            df_cost_sharing['約當量'] = df_cost_sharing['塗前約當量(噸)'] + df_cost_sharing['塗後約當量(噸)']
            df_cost_sharing['約當量'] = df_cost_sharing['約當量'].fillna(0)
            df_cost_sharing['入庫量'] = df_cost_sharing['入庫量'].fillna(0)
            
            elapsed = time.time() - start_time
            logging.info(f"df_cost_sharing time is: {elapsed:.2f} seconds") 
            
            start_time = time.time()            

            # 20250617 抓取運轉時間
            dt = datetime.datetime.strptime(etime, "%Y%m")
            stime_t = dt.strftime('%Y-%m-%d')
            etime_t = (dt + relativedelta(months=1) - timedelta(days=1))
            etime_t = etime_t.strftime('%Y-%m-%d')    

            srv_SRVAD1 = self.servers['SRVAD1'] 
            with srv_SRVAD1['create_engine'][0].connect() as conn:       
                sql =   """
                    SELECT 'PM'+mname AS 機台,ptype_two AS 紙別,sum(ptime) as 運轉時間
                    FROM
                    (
                        SELECT mname,relno,ptype,
                            Case when ptype like 'MM%' AND mname=18 THEN 'QE'
                                 when ptype like '%NCR' AND mname=19 THEN 'QC'
                                 ELSE left(ptype,2) END AS ptype_two,
                            gramg,ptime
                        FROM Amreel
                        WHERE 1=1
                        AND bdate>='"""+ str(stime_t) + """' AND bdate<='"""+ str(etime_t) + """'
                        AND left(right(relno,2),1) <> 'B'
                    ) t
                    GROUP BY mname,ptype_two
                    ORDER BY mname,ptype_two
                """       
                query = conn.execute(text(sql))  
                df_amreel_ptime = pd.DataFrame([dict(i) for i in query])

            try:
                df_cost_sharing_rule_daily = pd.read_excel(r'E:\AP\Api\dist\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='日產量',skiprows=0)
            except:              
                df_cost_sharing_rule_daily = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\工費分攤計算_2025年_修正版.xlsx',
                                              sheet_name='日產量',skiprows=0)
            df_cost_sharing_rule_daily = df_cost_sharing_rule_daily.loc[:,['機台','PN2','日產能']]

            df_cost_sharing = df_cost_sharing.merge(df_cost_sharing_rule_daily,left_on=['機台','紙別'],right_on=['機台','PN2'],how='left')
            df_cost_sharing['以日產能換算天數'] = df_cost_sharing['日產能'].fillna(0)
            df_cost_sharing['以日產能換算天數'] = np.where(
                            (df_cost_sharing['日產能'].notna()) & (df_cost_sharing['日產能'] != 0),
                            (df_cost_sharing['約當量'].astype(float) / df_cost_sharing['日產能'].astype(float)).round(2) * 100,
                            0
                        )

#             df_cost_sharing = df_cost_sharing.merge(df_amreel_ptime,left_on=['機台','紙別'],right_on=['機台','紙別'],how='left')
#             df_cost_sharing['以日產能換算天數'] = df_cost_sharing['運轉時間'].fillna(0)

            df_cost_sharing['基準'] = 0.0
            df_cost_sharing['基準'] = np.where(
                df_cost_sharing['被分攤部門'].isin([45,47,48,66,67,68,69]),
                df_cost_sharing['以日產能換算天數'],
                np.where(
                    (df_cost_sharing['被分攤部門'].isin([76])) & (df_cost_sharing['紙別'] == 'KA'),
                    df_cost_sharing['入庫量'] * 1.2,
                    np.where(
                        (df_cost_sharing['被分攤部門'].isin([80])) & (df_cost_sharing['紙別'].isin(['KH','KZ'])),
                        df_cost_sharing['入庫量'] * 0.2,
                        np.where(
                            (df_cost_sharing['被分攤部門'].isin([83])) & (df_cost_sharing['紙別'].isin(['KH','KZ'])),
                            df_cost_sharing['入庫量'] * 0.8,                
                            np.where(
                                (df_cost_sharing['被分攤部門'].isin([83])) & (df_cost_sharing['紙別'].isin(['KX','SX','UK'])),
                                df_cost_sharing['入庫量'] * 1.4,
                                np.where(
                                    (df_cost_sharing['被分攤部門'].isin([83])) & (df_cost_sharing['紙別'].isin(['QE'])),
                                    df_cost_sharing['入庫量'] * 0.3,
                                    np.where(
                                        (df_cost_sharing['被分攤部門'].isin([83])) & (df_cost_sharing['紙別'].isin(['BK'])),
                                        df_cost_sharing['入庫量'] * 1.8,
                                        np.where(
                                            (df_cost_sharing['被分攤部門'].isin([83])) & (df_cost_sharing['紙別'].isin(['KB'])),
                                            df_cost_sharing['入庫量'] * 6,
                                            np.where(
                                                (df_cost_sharing['被分攤部門'].isin([83])) & (df_cost_sharing['紙別'].isin(['KF'])),
                                                df_cost_sharing['入庫量'] * 2.5,
                                                np.where(
                                                    (df_cost_sharing['被分攤部門'].isin([83])) & (df_cost_sharing['紙別'].isin(['QC'])),
                                                    df_cost_sharing['入庫量'] * 0.3,
                                                    np.where(
                                                        df_cost_sharing['被分攤部門'].isin([74,75,76,80,81,82,83,96]),
                                                        df_cost_sharing['入庫量'],
                                                        np.where(
                                                            df_cost_sharing['被分攤部門'].isin([85,86,87]),
                                                            df_cost_sharing['塗料領用量(噸)'],
                                                            np.where(
                                                                (df_cost_sharing['被分攤部門'].isin([92])) & (df_cost_sharing['紙別'].isin(['K4','KL','SL','A0'])),
                                                                df_cost_sharing['約當量'] * 0.25,
                                                                np.where(
                                                                    (df_cost_sharing['被分攤部門'].isin([94])) & (df_cost_sharing['紙別'].isin(['K4','KL','SL','A0'])),
                                                                    df_cost_sharing['約當量'] * 0.75,
                                                                    np.where(
                                                                        (df_cost_sharing['被分攤部門'].isin([94])) & (df_cost_sharing['紙別'].isin(['AA','AT','AX','A8','AD','YA','YT','KW','KY','SW'])),
                                                                        df_cost_sharing['約當量'] * 0.125,
                                                                        np.where(
                                                                             (df_cost_sharing['被分攤部門'].isin([94])) & (df_cost_sharing['紙別'].isin(['KW','KY','SW'])),
                                                                             df_cost_sharing['約當量'] * 0.125,
                                                                             np.where(
                                                                                df_cost_sharing['被分攤部門'].isin([78,79,91,92,94,95]),
                                                                                df_cost_sharing['約當量'],
                                                                                0.0
                                                                             )
                                                                        )
                                                                    )
                                                                )
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )

            df_cost_sharing['基準'] = np.where(
                df_cost_sharing['基準']<0,
                0.0,
                df_cost_sharing['基準']
            )

            df_cost_sharing = df_cost_sharing.loc[:,['類別','被分攤部門','分攤部門','機台','紙別','基準','入庫量','約當量','__sort_index']]
            # 未online部分---

            df_cost_sharing = df_cost_sharing.merge(df_cost_sharing.groupby('被分攤部門')['基準'].sum().reset_index(),on='被分攤部門',how='left')

            df_cost_sharing.rename(columns={'基準_x':'基準','基準_y':'基準母數'},inplace=True)
            df_cost_sharing['基準分攤比例'] = np.where(
                            (df_cost_sharing['基準母數'].notna()) & (df_cost_sharing['基準母數'] != 0),
                            df_cost_sharing['基準'].astype(float) / df_cost_sharing['基準母數'].astype(float),
                            0
                        )

            df_cost_sharing = df_cost_sharing.merge(df_cost_sharing_raw.loc[df_cost_sharing_raw['日期'] == int(etime),
                                 ['部門', '變動人工', '用人', '折舊','維修', '消耗', '其他', '服務部門分攤','蒸汽', '電力', '包材', '瓦斯']],
                                 left_on = '被分攤部門', right_on = '部門',how='left')

            for col in ['變動人工', '用人', '折舊', '維修', '消耗', '其他', '服務部門分攤','蒸汽', '電力', '包材', '瓦斯']:
                df_cost_sharing[col] = np.where(
                            (df_cost_sharing['基準分攤比例'].notna()) & (df_cost_sharing['基準分攤比例'] != 0),
                            df_cost_sharing[col].astype(float) * df_cost_sharing['基準分攤比例'].astype(float),
                            0
                        )

            df_cost_sharing = df_cost_sharing.merge(df_cost_sharing_rule.drop_duplicates(subset=['被分攤部門','機台','分攤基準']).reset_index(drop=True).loc[:,['被分攤部門','機台','分攤基準']],
                                                    on=['被分攤部門','機台'],how='left')

            df_cost_sharing = df_cost_sharing.merge(df_cost_sharing_base,left_on=['機台','紙別'],right_on=['機台','PN2'],how='left')

            df_cost_sharing = df_cost_sharing.sort_values('__sort_index').drop(columns='__sort_index').reset_index(drop=True)

            for col in ['變動人工', '用人', '折舊', '維修', '消耗', '其他', '服務部門分攤','蒸汽', '電力', '包材', '瓦斯']:    
                if col == '變動人工':
                    pass
                elif col == '用人':
                    df_cost_sharing['單位' + col] = np.where(
                                df_cost_sharing['分攤基準'] == '入庫量',
                                np.where(
                                    (df_cost_sharing['入庫量'].notna()) & (df_cost_sharing['入庫量'] != 0),
                                    (df_cost_sharing['變動人工'].astype(float) + df_cost_sharing[col].astype(float)) / df_cost_sharing['入庫量'].astype(float),
                                    0
                                ),
                                np.where(
                                    (df_cost_sharing['約當量'].notna()) & (df_cost_sharing['約當量'] != 0),
                                    (df_cost_sharing['變動人工'].astype(float) + df_cost_sharing[col].astype(float)) / df_cost_sharing['約當量'].astype(float),
                                    0
                                )                    

                            )            
                else:
                    df_cost_sharing['單位' + col] = np.where(
                                df_cost_sharing['分攤基準'] == '入庫量',
                                np.where(
                                    (df_cost_sharing['入庫量'].notna()) & (df_cost_sharing['入庫量'] != 0),
                                    (df_cost_sharing[col].astype(float)) / df_cost_sharing['入庫量'].astype(float),
                                    0
                                ),
                                np.where(
                                    (df_cost_sharing['約當量'].notna()) & (df_cost_sharing['約當量'] != 0),
                                    (df_cost_sharing[col].astype(float)) / df_cost_sharing['約當量'].astype(float),
                                    0
                                )                    

                            )     

            df_unit_cost_ptype = df_cost_sharing.groupby(['機台','紙別'])                .agg(a=('單位用人','sum'), 
                     b=('單位折舊','sum'),
                     c=('單位維修','sum'), 
                     d=('單位消耗','sum'),
                     e=('單位其他','sum'),
                     f=('單位服務部門分攤','sum'),
                     g=('單位蒸汽','sum'),
                     h=('單位電力','sum'),
                     i=('單位包材','sum'),
                     j=('單位瓦斯','sum')
                    ).reset_index()

            df_unit_cost_ptype['合計\n(元/噸)'] = (
                        df_unit_cost_ptype[['a', 'b','c', 'd','e', 'f',]]
                        .fillna(0).sum(axis=1)
                    )

            df_unit_cost_ptype['單位用汽(T/T)'] = (
                        df_unit_cost_ptype['g'].fillna(0) / df_cost_energy.iloc[0,1]
                    )

            df_unit_cost_ptype['單位用電(度/T)'] = (
                        df_unit_cost_ptype['h'].fillna(0) / df_cost_energy.iloc[1,1]
                    )

            df_unit_cost_ptype = df_unit_cost_ptype.rename(columns={
                'a': '加總 - 單位用人',
                'b': '加總 - 單位折舊',
                'c': '加總 - 單位維修',
                'd': '加總 - 單位消耗',
                'e': '加總 - 單位其他',
                'f': '加總 - 單位服務部門分攤',
                'g': '加總 - 單位蒸汽',
                'h': '加總 - 單位電力',
                'i': '加總 - 單位包材',
                'j': '加總 - 單位瓦斯',
            })        

            df_unit_cost_category =  df_cost_sharing.groupby(['機台','類別','被分攤部門','分攤基準',])                .agg(a=('變動人工','sum'),
                     b=('用人','sum'), 
                     c=('折舊','sum'),
                     d=('維修','sum'), 
                     e=('消耗','sum'),
                     f=('其他','sum'),
                     g=('服務部門分攤','sum'),
                     h=('蒸汽','sum'),
                     i=('電力','sum'),
                     j=('包材','sum'),
                     k=('瓦斯','sum'),
                     l=('約當量','sum'),
                     m=('入庫量','sum'),
                    ).reset_index()

            df_unit_cost_category = df_unit_cost_category.rename(columns={
                'a': '變動人工',
                'b': '用人',
                'c': '折舊',
                'd': '維修',
                'e': '消耗',
                'f': '其他',
                'g': '服務部門分攤',
                'h': '蒸汽',
                'i': '電力',
                'j': '包材',
                'k': '瓦斯',
                'l': '約當量',
                'm': '入庫量',
            })

            for col in ['變動人工', '用人', '折舊', '維修', '消耗', '其他', '服務部門分攤','蒸汽', '電力', '包材', '瓦斯']:    
                if col == '變動人工':
                    pass
                elif col == '用人':
                     df_unit_cost_category['單位' + col] = np.where(
                                df_unit_cost_category['分攤基準'] == '入庫量',
                                np.where(
                                    ( df_unit_cost_category['入庫量'].notna()) & ( df_unit_cost_category['入庫量'] != 0),
                                    ( df_unit_cost_category['變動人工'].astype(float) +  df_unit_cost_category[col].astype(float)) /  df_unit_cost_category['入庫量'].astype(float),
                                    0
                                ),
                                np.where(
                                    ( df_unit_cost_category['約當量'].notna()) & ( df_unit_cost_category['約當量'] != 0),
                                    ( df_unit_cost_category['變動人工'].astype(float) +  df_unit_cost_category[col].astype(float)) /  df_unit_cost_category['約當量'].astype(float),
                                    0
                                )                    

                            )            
                else:
                     df_unit_cost_category['單位' + col] = np.where(
                                df_unit_cost_category['分攤基準'] == '入庫量',
                                np.where(
                                    ( df_unit_cost_category['入庫量'].notna()) & ( df_unit_cost_category['入庫量'] != 0),
                                    ( df_unit_cost_category[col].astype(float)) /  df_unit_cost_category['入庫量'].astype(float),
                                    0
                                ),
                                np.where(
                                    ( df_unit_cost_category['約當量'].notna()) & ( df_unit_cost_category['約當量'] != 0),
                                    ( df_unit_cost_category[col].astype(float)) /  df_unit_cost_category['約當量'].astype(float),
                                    0
                                )                    

                            ) 

            df_unit_cost_category = df_unit_cost_category.groupby(['機台','類別',])                .agg(a=('單位用人','sum'), 
                     b=('單位折舊','sum'),
                     c=('單位維修','sum'), 
                     d=('單位消耗','sum'),
                     e=('單位其他','sum'),
                     f=('單位服務部門分攤','sum'),
                     g=('單位蒸汽','sum'),
                     h=('單位電力','sum'),
                     i=('單位包材','sum'),
                     j=('單位瓦斯','sum')
                    ).reset_index()

            df_unit_cost_category['合計\n(元/噸)'] = (
                        df_unit_cost_category[['a', 'b','c', 'd','e', 'f',]]
                        .fillna(0).sum(axis=1)
                    )

            df_unit_cost_category['單位用汽(T/T)'] = (
                        df_unit_cost_category['g'].fillna(0) / df_cost_energy.iloc[0,1]
                    )

            df_unit_cost_category['單位用電(度/T)'] = (
                        df_unit_cost_category['h'].fillna(0) / df_cost_energy.iloc[1,1]
                    )

            df_unit_cost_category = df_unit_cost_category.rename(columns={
                'a': '加總 - 單位用人',
                'b': '加總 - 單位折舊',
                'c': '加總 - 單位維修',
                'd': '加總 - 單位消耗',
                'e': '加總 - 單位其他',
                'f': '加總 - 單位服務部門分攤',
                'g': '加總 - 單位蒸汽',
                'h': '加總 - 單位電力',
                'i': '加總 - 單位包材',
                'j': '加總 - 單位瓦斯',
            })  
            
            elapsed = time.time() - start_time
            logging.info(f"df_unit_cost_category time is: {elapsed:.2f} seconds") 
            
            start_time = time.time()
            
            # 讀取內外銷成本
            month_list = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月']

            # 取得今年的年份
            current_year = datetime.datetime.now().year

            # 建立字典
            month_dict = {month: f"{current_year}{str(i+1).zfill(2)}" for i, month in enumerate(month_list)}
            
            # 預設檔案路徑
            excel_path = fr'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供\產品內外銷{current_year}年_for成本單.xlsx'

            with pd.ExcelFile(excel_path) as xls:
                all_sheets = xls.sheet_names
                sheet_name_map = {name.strip(): name for name in all_sheets}      

            df_cost_of_sales_concat_category = pd.DataFrame()
            df_cost_of_sales_concat_ptype = pd.DataFrame()

            # 讀取內外銷成本
            for m in month_list:
                try:
                    if m in sheet_name_map:
                        sheet_name = sheet_name_map[m]                    
                        try:
                            df_cost_of_sales = pd.read_excel(r'E:\AP\Api\dist\產品內外銷'+str(current_year)+'年_for成本單.xlsx',
                                                             sheet_name=sheet_name, skiprows=0, header=None)
                        except:                       
                            df_cost_of_sales = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供\產品內外銷'+str(current_year)+'年_for成本單.xlsx',
                                          sheet_name=sheet_name,skiprows=0,header=None)
                    else:
                        continue
            #         df_cost_of_sales = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\產品內外銷1~4月彙總表_for成本單.xlsx',
            #                           sheet_name=m,skiprows=0,header=None)        
                    df_cost_of_sales_temp = df_cost_of_sales.loc[df_cost_of_sales[df_cost_of_sales[0].fillna('').str.startswith('產品淨利表')].iloc[0,:].name:df_cost_of_sales[df_cost_of_sales[0].fillna('').str.startswith('產品淨利表')].iloc[1,:].name-1,0:7]
                    df_cost_of_sales_temp = df_cost_of_sales_temp.loc[df_cost_of_sales_temp[df_cost_of_sales_temp[0] == '銷別'].index[0]:,:].reset_index(drop=True)
                    df_cost_of_sales_temp.columns = df_cost_of_sales_temp.iloc[0]
                    df_cost_of_sales_temp = df_cost_of_sales_temp[1:].reset_index(drop=True)
                    df_cost_of_sales_temp = df_cost_of_sales_temp.loc[:df_cost_of_sales_temp[df_cost_of_sales_temp['銷別'] == '總計'].index[0]-1,:].reset_index(drop=True)
                    df_cost_of_sales_temp = df_cost_of_sales_temp[~df_cost_of_sales_temp['銷別'].isin(['D 合計','X 合計'])]
                    df_cost_of_sales_temp['銷別'] = df_cost_of_sales_temp['銷別'].fillna(method='ffill')
                    df_cost_of_sales_temp['類別'] = df_cost_of_sales_temp['類別'].fillna(method='ffill')
                    df_cost_of_sales_temp = df_cost_of_sales_temp[~df_cost_of_sales_temp['產品'].isna()].reset_index(drop=True)
                    df_cost_of_sales_temp['年月'] = month_dict[m]
                    df_cost_of_sales_concat_category = pd.concat([df_cost_of_sales_concat_category,df_cost_of_sales_temp]).reset_index(drop=True)        

                    df_cost_of_sales_temp = df_cost_of_sales.loc[df_cost_of_sales[df_cost_of_sales[0].fillna('').str.startswith('產品淨利表')].iloc[1,:].name:,0:6]
                    df_cost_of_sales_temp = df_cost_of_sales_temp.loc[df_cost_of_sales_temp[df_cost_of_sales_temp[0] == '銷別'].index[0]:,:].reset_index(drop=True)
                    df_cost_of_sales_temp.columns = df_cost_of_sales_temp.iloc[0]
                    df_cost_of_sales_temp = df_cost_of_sales_temp[1:].reset_index(drop=True)
                    df_cost_of_sales_temp['銷別'] = df_cost_of_sales_temp['銷別'].fillna(method='ffill')
                    try:
                        df_cost_of_sales_temp = df_cost_of_sales_temp[~df_cost_of_sales_temp['PN2'].isna()].reset_index(drop=True)
                    except:
                        df_cost_of_sales_temp.rename(columns={'PN ':'PN2'},inplace=True)
                        df_cost_of_sales_temp = df_cost_of_sales_temp[~df_cost_of_sales_temp['PN2'].isna()].reset_index(drop=True)
                    df_cost_of_sales_temp['年月'] = month_dict[m]
                    df_cost_of_sales_concat_ptype = pd.concat([df_cost_of_sales_concat_ptype,df_cost_of_sales_temp]).reset_index(drop=True)
                except:
                    break   

            df_cost_of_sales_ptype = df_cost_of_sales_concat_ptype.copy()
            df_cost_of_sales_category = df_cost_of_sales_concat_category.copy()            
            
            if (df_Product_cost_schedule_Items_schema is None) or mname in ['NCR','含浸']:
                dt = datetime.datetime.strptime(stime, "%Y%m")

                stime_1 = (dt - relativedelta(months=1)).strftime("%Y%m")
                stime_2 = (dt - relativedelta(months=2)).strftime("%Y%m")

                etime_1 = stime
                etime_2 = stime_1  

                # 讀取近三個月 各成本項目
                # 讀取原物料 原料量
                try:            
                    srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                    with srv_SRVMESDBA1['create_engine'][0].connect() as conn:   
                        sql =   """
                            SELECT [分類別],[KG],[BATCH_Sort],[RM_Kind],[RMN],[號機],[PD],[PN2],[PN4],[COST],[料號],
                                    [異動日期],[主要數量],[主要單位],[工單],[Nqty],[BW],[類別]
                              FROM [CostSheet].[dbo].[ERP_Inventory_Material]
                              WHERE [年月] = '"""+ str(etime) +"""'
                        """       
                        query = conn.execute(text(sql))
                        df_reel_material_t1 = pd.DataFrame([dict(i) for i in query])

                        df_Equivalent_Output_Before_Apportionment['PN2'] = df_Equivalent_Output_Before_Apportionment['PN4'].apply(classify_pn4)
                        df_Equivalent_Output_Before_Apportionment['類別'] = df_Equivalent_Output_Before_Apportionment['PN2'].map(df_ptype_category.set_index('兩碼紙別')['類別'])        

                        df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['機台'].astype(str) +                                                                       df_Equivalent_Output_Before_Apportionment['PN4'].astype(str) +                                                                       df_Equivalent_Output_Before_Apportionment['基重'].astype(str)        
                    if df_reel_material_t1.empty:
                        df_reel_material_t1 = material_data(etime,df_Equivalent_Output_Before_Apportionment)
                except:
                    df_reel_material_t1 = material_data(etime,df_Equivalent_Output_Before_Apportionment)
                
                if etime=='202501':
                    pass
                else:
                    try:
                        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:  
                            sql =   """
                                SELECT [分類別],[KG],[BATCH_Sort],[RM_Kind],[RMN],[號機],[PD],[PN2],[PN4],[COST],[料號],
                                        [異動日期],[主要數量],[主要單位],[工單],[Nqty],[BW],[類別]
                                  FROM [CostSheet].[dbo].[ERP_Inventory_Material]
                                  WHERE [年月] = '"""+ str(etime_1) +"""'
                            """       
                            query = conn.execute(text(sql))
                            df_reel_material_t2 = pd.DataFrame([dict(i) for i in query])

                            df_Equivalent_Output_Before_Apportionment['PN2'] = df_Equivalent_Output_Before_Apportionment['PN4'].apply(classify_pn4)
                            df_Equivalent_Output_Before_Apportionment['類別'] = df_Equivalent_Output_Before_Apportionment['PN2'].map(df_ptype_category.set_index('兩碼紙別')['類別'])        

                            df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['機台'].astype(str) +                                                                           df_Equivalent_Output_Before_Apportionment['PN4'].astype(str) +                                                                           df_Equivalent_Output_Before_Apportionment['基重'].astype(str)        
                        if df_reel_material_t2.empty:
                            df_reel_material_t2 = material_data(etime_1,df_Equivalent_Output_Before_Apportionment)
                    except:
                        df_reel_material_t2 = material_data(etime_1,df_Equivalent_Output_Before_Apportionment)
                        
                if etime == '202502':
                    pass
                elif etime == '202501':
                    pass
                else:
                    try:
                        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:     
                            sql =   """
                                SELECT [分類別],[KG],[BATCH_Sort],[RM_Kind],[RMN],[號機],[PD],[PN2],[PN4],[COST],[料號],
                                        [異動日期],[主要數量],[主要單位],[工單],[Nqty],[BW],[類別]
                                  FROM [CostSheet].[dbo].[ERP_Inventory_Material]
                                  WHERE [年月] = '"""+ str(etime_2) +"""'
                            """       
                            query = conn.execute(text(sql))
                            df_reel_material_t3 = pd.DataFrame([dict(i) for i in query])

                            df_Equivalent_Output_Before_Apportionment['PN2'] = df_Equivalent_Output_Before_Apportionment['PN4'].apply(classify_pn4)
                            df_Equivalent_Output_Before_Apportionment['類別'] = df_Equivalent_Output_Before_Apportionment['PN2'].map(df_ptype_category.set_index('兩碼紙別')['類別'])        

                            df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['機台'].astype(str) +                                                                           df_Equivalent_Output_Before_Apportionment['PN4'].astype(str) +                                                                           df_Equivalent_Output_Before_Apportionment['基重'].astype(str)        
                        if df_reel_material_t3.empty:
                            df_reel_material_t3 = material_data(etime_2,df_Equivalent_Output_Before_Apportionment)
                    except:
                        df_reel_material_t3 = material_data(etime_2,df_Equivalent_Output_Before_Apportionment)                      
                

                if mname == 'NCR':
                    if etime == '202502':
                        df_reel_material_concat = pd.concat([
                            df_reel_material_t1[df_reel_material_t1['分類別']=='NCR'].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t2[df_reel_material_t2['分類別']=='NCR'].groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        ]).groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)
                    elif etime =='202501':
                        df_reel_material_concat = df_reel_material_t1[df_reel_material_t1['分類別']=='NCR'].groupby(['RM_Kind','料號','RMN']).size().reset_index()                            .groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)                        
                    else:
                        df_reel_material_concat = pd.concat([
                            df_reel_material_t1[df_reel_material_t1['分類別']=='NCR'].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t2[df_reel_material_t2['分類別']=='NCR'].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t3[df_reel_material_t3['分類別']=='NCR'].groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        ]).groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)   
                elif mname == '含浸':
                    if etime == '202502':
                        df_reel_material_concat = pd.concat([
                            df_reel_material_t1[df_reel_material_t1['分類別']=='含浸美紋'].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t2[df_reel_material_t2['分類別']=='含浸美紋'].groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        ]).groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)
                    elif etime =='202501':
                        df_reel_material_concat = df_reel_material_t1[df_reel_material_t1['分類別']=='含浸美紋'].groupby(['RM_Kind','料號','RMN']).size().reset_index()                            .groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)                        
                    else:
                        df_reel_material_concat = pd.concat([
                            df_reel_material_t1[df_reel_material_t1['分類別']=='含浸美紋'].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t2[df_reel_material_t2['分類別']=='含浸美紋'].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t3[df_reel_material_t3['分類別']=='含浸美紋'].groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        ]).groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)                          
                else:
                    if etime == '202502':
                        df_reel_material_concat = pd.concat([
                            df_reel_material_t1[df_reel_material_t1['分類別']==Product_Category].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t2[df_reel_material_t2['分類別']==Product_Category].groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        ]).groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)                        
                    elif etime =='202501':
                        df_reel_material_concat = df_reel_material_t1[df_reel_material_t1['分類別']==Product_Category].groupby(['RM_Kind','料號','RMN']).size().reset_index()                            .groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)                        
                    else:
                        df_reel_material_concat = pd.concat([
                            df_reel_material_t1[df_reel_material_t1['分類別']==Product_Category].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t2[df_reel_material_t2['分類別']==Product_Category].groupby(['RM_Kind','料號','RMN']).size().reset_index(),
                            df_reel_material_t3[df_reel_material_t3['分類別']==Product_Category].groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        ]).groupby(['RM_Kind','料號','RMN']).size().reset_index()
                        df_reel_material_concat.drop([0],axis=1,inplace=True)

                # 加上流水號
                def add_serial(df, kind):
                    df_copy = df[df['RM_Kind'] == kind].copy()
                    df_copy['RM_Kind'] = df_copy['RM_Kind'] + (df_copy.groupby('RM_Kind').cumcount() + 1).astype(str)
                    return df_copy

                fb_rows_FB = add_serial(df_reel_material_concat, 'FB')
                fb_rows_CY = add_serial(df_reel_material_concat, 'CY')
                fb_rows_CT = add_serial(df_reel_material_concat, 'CT')
                fb_rows_CH = add_serial(df_reel_material_concat, 'CH')

                # 加上 COST 資料
                cost_data = [
                    ['COST1', '603-11', '燃料費'],
                    ['COST2', '603-11', '瓦斯費'],
                    ['COST3', '603-12', '電力費'],
                    ['COST4', '603-13', '包裝材料費'],
                    ['COST5', '', '變動製造費用'],
                    ['COST6', '', '變動製造成本'],
                    ['COST7', '', '固定製造成本'],
                    ['COST8', '', '生產成本'],
                    ['COST9', '內銷', '變動推銷費用'],
                    ['COST10', '內銷', '變動成本'],
                    ['COST11', '內銷', '邊際貢獻'],
                    ['COST12', '內銷', '管固銷研財費用'],
                    ['COST13', '內銷', '固定成本'],
                    ['COST14', '內銷', '總成本'],
                    ['COST15', '內銷', '銷售值'],
                    ['COST16', '內銷', '利潤'],
                    ['COST17', '外銷', '變動推銷費用'],
                    ['COST18', '外銷', '變動成本'],
                    ['COST19', '外銷', '邊際貢獻'],
                    ['COST20', '外銷', '管固銷研財費用'],
                    ['COST21', '外銷', '固定成本'],
                    ['COST22', '外銷', '總成本'],
                    ['COST23', '外銷', '銷售值'],
                    ['COST24', '外銷', '利潤'],
                ]

                if mname == 'NCR':
                    df_items = pd.concat([
                        fb_rows_FB,
                        pd.DataFrame(data={'RM_Kind': 'FB1', '料號': ' ', 'RMN': 'NCR原紙'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'FB', '料號': '', 'RMN': '纖維原料小計'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'WS', '料號': '', 'RMN': '損紙_白道林(二級)'}, index=[0]),
                        fb_rows_CY,
                        pd.DataFrame(data={'RM_Kind': 'CY1', '料號': '913160106503', 'RMN': '濕磨碳酸鈣 C65'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CY', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CY', '料號': '', 'RMN': '填料小計'}, index=[0]),
                        fb_rows_CT,
                        pd.DataFrame(data={'RM_Kind': 'CT', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CT', '料號': '', 'RMN': '塗料小計'}, index=[0]),    
                        fb_rows_CH,
                        pd.DataFrame(data={'RM_Kind': 'CH', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CH', '料號': '', 'RMN': '化工原料小計'}, index=[0]),     
                        pd.DataFrame(data={'RM_Kind': '', '料號': '', 'RMN': '直接原料合計'}, index=[0]),
                        pd.DataFrame(cost_data, columns=['RM_Kind', '料號', 'RMN'])
                    ], ignore_index=True)      
                elif mname == '含浸':
                    df_items = pd.concat([
                        fb_rows_FB,
                        pd.DataFrame(data={'RM_Kind': 'FB1', '料號': ' ', 'RMN': '含浸原紙'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'FB', '料號': '', 'RMN': '纖維原料小計'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'WS', '料號': '', 'RMN': '損紙_白道林(二級)'}, index=[0]),
                        fb_rows_CY,
                        pd.DataFrame(data={'RM_Kind': 'CY', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CY', '料號': '', 'RMN': '填料小計'}, index=[0]),
                        fb_rows_CT,
                        pd.DataFrame(data={'RM_Kind': 'CT', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CT', '料號': '', 'RMN': '塗料小計'}, index=[0]),    
                        fb_rows_CH,
                        pd.DataFrame(data={'RM_Kind': 'CH', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CH', '料號': '', 'RMN': '化工原料小計'}, index=[0]),     
                        pd.DataFrame(data={'RM_Kind': '', '料號': '', 'RMN': '直接原料合計'}, index=[0]),
                        pd.DataFrame(cost_data, columns=['RM_Kind', '料號', 'RMN'])
                    ], ignore_index=True)                       
                else:
                    df_items = pd.concat([
                        fb_rows_FB,
                        pd.DataFrame(data={'RM_Kind': 'FB', '料號': '', 'RMN': '纖維原料小計'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'WS', '料號': '', 'RMN': '損紙_白道林(二級)'}, index=[0]),
                        fb_rows_CY,
                        pd.DataFrame(data={'RM_Kind': 'CY', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CY', '料號': '', 'RMN': '填料小計'}, index=[0]),
                        fb_rows_CT,
                        pd.DataFrame(data={'RM_Kind': 'CT', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CT', '料號': '', 'RMN': '塗料小計'}, index=[0]),    
                        fb_rows_CH,
                        pd.DataFrame(data={'RM_Kind': 'CH', '料號': '', 'RMN': '其他'}, index=[0]),
                        pd.DataFrame(data={'RM_Kind': 'CH', '料號': '', 'RMN': '化工原料小計'}, index=[0]),     
                        pd.DataFrame(data={'RM_Kind': '', '料號': '', 'RMN': '直接原料合計'}, index=[0]),
                        pd.DataFrame(cost_data, columns=['RM_Kind', '料號', 'RMN'])
                    ], ignore_index=True)

                df_items.rename(columns={'RM_Kind':'代碼','RMN':'名稱'},inplace=True)
            else:
                df_items = df_Product_cost_schedule_Items_schema.copy()

            df_Product_cost_schedule_Items = pd.DataFrame(columns=[
                '月份','機台','類別','代碼','料號','名稱','材料單價','每噸用量','每噸成本'
            ])

            # 補上空欄位
            df_items['月份'] = etime
            df_items['機台'] = mname
            df_items['類別'] = Product_Category
            df_items['材料單價'] = None
            df_items['每噸用量'] = None
            df_items['每噸成本'] = None

            # 調整欄位順序
            df_items = df_items[['月份', '機台', '類別', '代碼', '料號', '名稱','材料單價','每噸用量','每噸成本']]

            # Append
            df_Product_cost_schedule_Items = pd.concat([df_Product_cost_schedule_Items, df_items], ignore_index=True)
            
            if mname == 'NCR':
                if Product_two_ptype == '':
                    df_Product_cost_schedule_Items['材料單價'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & \
                                                (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['單價(元/單價)']
                    )    
                    df_Product_cost_schedule_Items['每噸用量'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & \
                                                (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']\
                                                                                                / df_Product_cost_schedule.loc[0,'生產量(噸)']
                    )
                else:
                    df_Product_cost_schedule_Items['材料單價'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & \
                                                   (df_reel_material_grouped['PN2'] == Product_two_ptype) & \
                                                (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['單價(元/單價)']
                    )       
                    df_Product_cost_schedule_Items['每噸用量'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & \
                                                (df_reel_material_grouped['PN2'] == Product_two_ptype) & \
                                                (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']\
                                                                                                / df_Product_cost_schedule.loc[0,'生產量(噸)']
                    )

                df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['名稱']=='NCR原紙','材料單價'] =                     (NCR_Base_Paper.loc[(NCR_Base_Paper['名稱']=='生產成本') & (NCR_Base_Paper['月份']==etime)]['每噸成本'].item() / 1000.0)
                
                if Product_two_ptype == '':
                    df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['名稱']=='NCR原紙','每噸用量'] =                         (df_grouped_2.loc[(df_grouped_2['機台']=='NCR'),'纖維領用量(噸)'].item() * 1000.0)                                                                        / df_Product_cost_schedule.loc[0,'生產量(噸)']                    
                else:
                    df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['名稱']=='NCR原紙','每噸用量'] =                         (df_grouped.loc[(df_grouped['機台']=='NCR') & (df_grouped['PN2']==Product_two_ptype),'纖維領用量(噸)'].item() * 1000.0)                                                                        / df_Product_cost_schedule.loc[0,'生產量(噸)']
            elif mname == '含浸':
                if Product_two_ptype == '':
                    df_Product_cost_schedule_Items['材料單價'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & \
                                                (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['單價(元/單價)']
                    )    
                    df_Product_cost_schedule_Items['每噸用量'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & \
                                                (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['KG']\
                                                                                                / df_Product_cost_schedule.loc[0,'生產量(噸)']
                    )
                else:
                    df_Product_cost_schedule_Items['材料單價'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & \
                                                   (df_reel_material_grouped['PN2'] == Product_two_ptype) & \
                                                (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['單價(元/單價)']
                    )       
                    df_Product_cost_schedule_Items['每噸用量'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & \
                                                (df_reel_material_grouped['PN2'] == Product_two_ptype) & \
                                                (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['KG']\
                                                                                                / df_Product_cost_schedule.loc[0,'生產量(噸)']
                    )

                df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['名稱']=='含浸原紙','材料單價'] =                     (NCR_Base_Paper.loc[(NCR_Base_Paper['名稱']=='生產成本') & (NCR_Base_Paper['月份']==etime)]['每噸成本'].item() / 1000.0)
                
                if Product_two_ptype == '':
                    df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['名稱']=='含浸原紙','每噸用量'] =                         (df_grouped_2.loc[(df_grouped_2['機台']=='含浸'),'纖維領用量(噸)'].item() * 1000.0)                                                                        / df_Product_cost_schedule.loc[0,'生產量(噸)']                    
                else:
                    df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['名稱']=='含浸原紙','每噸用量'] =                         (df_grouped.loc[(df_grouped['機台']=='含浸') & (df_grouped['PN2']==Product_two_ptype),'纖維領用量(噸)'].item() * 1000.0)                                                                        / df_Product_cost_schedule.loc[0,'生產量(噸)']                
                
            else:
                if Product_two_ptype == '':
                    df_Product_cost_schedule_Items['材料單價'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & \
                                                (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['單價(元/單價)']
                    )    
                    df_Product_cost_schedule_Items['每噸用量'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & \
                                                (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']\
                                                                                                / df_Product_cost_schedule.loc[0,'生產量(噸)']
                    )
                else:
                    df_Product_cost_schedule_Items['材料單價'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & \
                                                   (df_reel_material_grouped['PN2'] == Product_two_ptype) & \
                                                (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['單價(元/單價)']
                    )       
                    df_Product_cost_schedule_Items['每噸用量'] = df_Product_cost_schedule_Items['料號'].map(
                        df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & \
                                                (df_reel_material_grouped['PN2'] == Product_two_ptype) & \
                                                (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']\
                                                                                                / df_Product_cost_schedule.loc[0,'生產量(噸)']
                    )    

            df_Product_cost_schedule_Items['每噸成本'] = df_Product_cost_schedule_Items['材料單價'] *                                                         df_Product_cost_schedule_Items['每噸用量']        

            index_FB = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='纖維原料小計'].index[0]
            index_WS = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='損紙_白道林(二級)'].index[0]
            index_CY = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='填料小計'].index[0]
            index_CT = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='塗料小計'].index[0]
            index_CH = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='化工原料小計'].index[0]  

            df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['代碼']=='FB','每噸用量'] =                                                             df_Product_cost_schedule_Items.loc[:index_FB,'每噸用量'].sum()
            df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['代碼']=='FB','每噸成本'] =                                                             df_Product_cost_schedule_Items.loc[:index_FB,'每噸成本'].sum()
            df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['代碼']=='FB','材料單價'] =                             df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['代碼']=='FB','每噸成本'] /                             df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['代碼']=='FB','每噸用量']
            
            df_Product_cost_schedule_Items.loc[df_Product_cost_schedule_Items['代碼']=='WS','每噸用量'] = 0.0
#             (df_Product_cost_schedule.loc[0, '纖維配合率'] / df_Product_cost_schedule.loc[0, '纖維得率'] * 1000) if df_Product_cost_schedule.loc[0, '纖維得率'] != 0 else 0

            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CY') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                                             df_Product_cost_schedule_Items.loc[index_CY-2,'每噸用量'].sum()
            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CY') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                                             df_Product_cost_schedule_Items.loc[index_CY-2,'每噸成本'].sum()
            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CY') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                             df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CY') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                             df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CY') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']
         
            
            if mname == 'NCR':
                if Product_two_ptype == '':

                    # 塗料小計
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()

                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['COST']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']

                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CT,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']

                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['COST']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']
                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                else:
                    # 塗料小計
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()

                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['COST']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']

                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CT,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼'] == 'CT') & (df_Product_cost_schedule_Items['名稱'] == '其他'), '材料單價'] =                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼'] == 'CT') & (df_Product_cost_schedule_Items['名稱'] == '其他'), '材料單價'].clip(lower=0)
                            
                            
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['COST']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']
                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']

            elif mname == '含浸':
                if Product_two_ptype == '':

                    # 塗料小計
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()

                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['COST']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']

                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CT,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']

                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['COST']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']
                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                else:
                    # 塗料小計
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()

                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['COST']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']

                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CT,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼'] == 'CT') & (df_Product_cost_schedule_Items['名稱'] == '其他'), '材料單價'] =                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼'] == 'CT') & (df_Product_cost_schedule_Items['名稱'] == '其他'), '材料單價'].clip(lower=0)
                            
                            
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['COST']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']
                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==95)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                    
            else:
                if Product_two_ptype == '':

                    # 塗料小計
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()

                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['COST']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']

                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CT,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']

                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['COST']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']
                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                else:
                    # 塗料小計
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()

                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['COST']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']

                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CT,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']

                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['Nqty']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] =                                     (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['COST']                                      / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']!='其他'),'每噸用量']
                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PN2'] == Product_two_ptype) & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].fillna(0).sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].fillna(0).sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']      
                    
            index_diff = index_CH+1 - 44

            # 直接原料合計

            df_Product_cost_schedule_Items.loc[44+index_diff,'每噸用量'] = df_Product_cost_schedule_Items.loc[[index_FB,index_CY,index_CT,index_CH],'每噸用量'].sum()
            df_Product_cost_schedule_Items.loc[44+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[[index_FB,index_CY,index_CT,index_CH],'每噸成本'].sum()
            df_Product_cost_schedule_Items.loc[44+index_diff,'材料單價'] = df_Product_cost_schedule_Items.loc[44+index_diff,'每噸成本'] / df_Product_cost_schedule_Items.loc[44+index_diff,'每噸用量']

            if Product_two_ptype == '':
                if Product_Category == 'NCR原紙':
                    # 燃料費
                    df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] = df_cost_energy.iloc[0,1]
                    df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QC') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['單位用汽(T/T)'].item()
                    df_Product_cost_schedule_Items.loc[45+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量']

                    # 瓦斯費
                    df_Product_cost_schedule_Items.loc[46+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QC') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['加總 - 單位瓦斯'].item()
                    # 電力費
                    df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] = df_cost_energy.iloc[1,1]
                    df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QC') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['單位用電(度/T)'].item()
                    df_Product_cost_schedule_Items.loc[47+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量']

                    df_Product_cost_schedule_Items.loc[48+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QC') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['加總 - 單位包材'].item()

                    df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff:48+index_diff,'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[49+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[[44+index_diff,49+index_diff],'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[50+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QC') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['合計\n(元/噸)'].item()
                    df_Product_cost_schedule_Items.loc[51+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] +                                                                        df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']
                    df_Product_cost_schedule_Items.loc[52+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本']/2204.62).round(2)        
                elif Product_Category == '含浸原紙':
                    # 燃料費
                    df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] = df_cost_energy.iloc[0,1]
                    df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QE') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['單位用汽(T/T)'].item()
                    df_Product_cost_schedule_Items.loc[45+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量']

                    # 瓦斯費
                    df_Product_cost_schedule_Items.loc[46+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QE') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['加總 - 單位瓦斯'].item()
                    # 電力費
                    df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] = df_cost_energy.iloc[1,1]
                    df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QE') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['單位用電(度/T)'].item()
                    df_Product_cost_schedule_Items.loc[47+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量']

                    df_Product_cost_schedule_Items.loc[48+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QE') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['加總 - 單位包材'].item()

                    df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff:48+index_diff,'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[49+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[[44+index_diff,49+index_diff],'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[50+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == 'QE') &                                                                                          (df_unit_cost_ptype['機台'] == mname)]['合計\n(元/噸)'].item()
                    df_Product_cost_schedule_Items.loc[51+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] +                                                                        df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']
                    df_Product_cost_schedule_Items.loc[52+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本']/2204.62).round(2)                            
                else:
                    if df_unit_cost_category[(df_unit_cost_category['類別'] == Product_Category) & (df_unit_cost_category['機台'] == mname)]['單位用汽(T/T)'].empty :
                        df_unit_cost_category = pd.concat([df_unit_cost_category,pd.DataFrame({'機台':mname,'類別':Product_Category},index=[0])],ignore_index=True).fillna(0)
                    
                    # 燃料費
                    df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] = df_cost_energy.iloc[0,1]

                    df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量'] = df_unit_cost_category[(df_unit_cost_category['類別'] == Product_Category) &                                                                                              (df_unit_cost_category['機台'] == mname)]['單位用汽(T/T)'].item()
                    df_Product_cost_schedule_Items.loc[45+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量']

                    # 瓦斯費
                    df_Product_cost_schedule_Items.loc[46+index_diff,'每噸成本'] = df_unit_cost_category[(df_unit_cost_category['類別'] == Product_Category) &                                                                                          (df_unit_cost_category['機台'] == mname)]['加總 - 單位瓦斯'].item()
                    # 電力費
                    df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] = df_cost_energy.iloc[1,1]
                    df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量'] = df_unit_cost_category[(df_unit_cost_category['類別'] == Product_Category) &                                                                                          (df_unit_cost_category['機台'] == mname)]['單位用電(度/T)'].item()
                    df_Product_cost_schedule_Items.loc[47+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量']

                    df_Product_cost_schedule_Items.loc[48+index_diff,'每噸成本'] = df_unit_cost_category[(df_unit_cost_category['類別'] == Product_Category) &                                                                                          (df_unit_cost_category['機台'] == mname)]['加總 - 單位包材'].item()

                    df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff:48+index_diff,'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[49+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[[44+index_diff,49+index_diff],'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[50+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本'] = df_unit_cost_category[(df_unit_cost_category['類別'] == Product_Category) &                                                                                          (df_unit_cost_category['機台'] == mname)]['合計\n(元/噸)'].item()
                    df_Product_cost_schedule_Items.loc[51+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']/2204.62).round(2)

                    df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] +                                                                        df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']
                    df_Product_cost_schedule_Items.loc[52+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本']/2204.62).round(2)
            else:
                if df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == Product_two_ptype) & (df_unit_cost_ptype['機台'] == mname)]['單位用汽(T/T)'].empty :
                    df_unit_cost_ptype = pd.concat([df_unit_cost_ptype,pd.DataFrame({'機台':mname,'紙別':Product_two_ptype},index=[0])],ignore_index=True).fillna(0)
                
                # 燃料費
                df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] = df_cost_energy.iloc[0,1]

                df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == Product_two_ptype) &                                                                                      (df_unit_cost_ptype['機台'] == mname)]['單位用汽(T/T)'].item()
                df_Product_cost_schedule_Items.loc[45+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[45+index_diff,'每噸用量']

                # 瓦斯費
                df_Product_cost_schedule_Items.loc[46+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == Product_two_ptype) &                                                                                      (df_unit_cost_ptype['機台'] == mname)]['加總 - 單位瓦斯'].item()
                # 電力費
                df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] = df_cost_energy.iloc[1,1]
                df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == Product_two_ptype) &                                                                                      (df_unit_cost_ptype['機台'] == mname)]['單位用電(度/T)'].item()
                df_Product_cost_schedule_Items.loc[47+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[47+index_diff,'材料單價'] * df_Product_cost_schedule_Items.loc[47+index_diff,'每噸用量']

                df_Product_cost_schedule_Items.loc[48+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == Product_two_ptype) &                                                                                      (df_unit_cost_ptype['機台'] == mname)]['加總 - 單位包材'].item()

                df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[45+index_diff:48+index_diff,'每噸成本'].sum()
                df_Product_cost_schedule_Items.loc[49+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[49+index_diff,'每噸成本']/2204.62).round(2)

                df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[[44+index_diff,49+index_diff],'每噸成本'].sum()
                df_Product_cost_schedule_Items.loc[50+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本']/2204.62).round(2)

                df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本'] = df_unit_cost_ptype[(df_unit_cost_ptype['紙別'] == Product_two_ptype) &                                                                                      (df_unit_cost_ptype['機台'] == mname)]['合計\n(元/噸)'].item()
                df_Product_cost_schedule_Items.loc[51+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']/2204.62).round(2)

                df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] +                                                                    df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本']
                df_Product_cost_schedule_Items.loc[52+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[52+index_diff,'每噸成本']/2204.62).round(2)

            # 內銷
            try:
                if Product_two_ptype != '':
                    df_Product_cost_schedule_Items.loc[53+index_diff,'每噸成本'] =                                             df_cost_of_sales_ptype[(df_cost_of_sales_ptype['銷別']=='D') &                                            (df_cost_of_sales_ptype['PN2']==Product_two_ptype) &                                            (df_cost_of_sales_ptype['年月']==etime)]['變動推'].item()   
                else:
                    df_Product_cost_schedule_Items.loc[53+index_diff,'每噸成本'] =                                             df_cost_of_sales_category[(df_cost_of_sales_category['銷別']=='D') &                                            (df_cost_of_sales_category['產品']==Product_Category) &                                            (df_cost_of_sales_category['年月']==etime)]['變動推'].item()
            except:
                df_Product_cost_schedule_Items.loc[53+index_diff,'每噸成本'] = 0

            df_Product_cost_schedule_Items.loc[54+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] +                                                                df_Product_cost_schedule_Items.loc[53+index_diff,'每噸成本']

            # 管固銷研財費用
            try:
                if Product_two_ptype != '':
                    df_Product_cost_schedule_Items.loc[56+index_diff,'每噸成本'] =                                             df_cost_of_sales_ptype[(df_cost_of_sales_ptype['銷別']=='D') &                                            (df_cost_of_sales_ptype['PN2']==Product_two_ptype) &                                            (df_cost_of_sales_ptype['年月']==etime)]['管研財'].item()   
                else:
                    df_Product_cost_schedule_Items.loc[56+index_diff,'每噸成本'] =                                             df_cost_of_sales_category[(df_cost_of_sales_category['銷別']=='D') &                                            (df_cost_of_sales_category['產品']==Product_Category) &                                            (df_cost_of_sales_category['年月']==etime)]['管研財'].item()
            except:
                df_Product_cost_schedule_Items.loc[56+index_diff,'每噸成本'] = 0

            df_Product_cost_schedule_Items.loc[57+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本'] +                                                                df_Product_cost_schedule_Items.loc[56+index_diff,'每噸成本']

            df_Product_cost_schedule_Items.loc[58+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[54+index_diff,'每噸成本'] +                                                                df_Product_cost_schedule_Items.loc[57+index_diff,'每噸成本']
            df_Product_cost_schedule_Items.loc[58+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[58+index_diff,'每噸成本']/2204.62).round(2)

            # 銷售值
            try:
                if Product_two_ptype != '':
                    df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本'] =                                             df_cost_of_sales_ptype[(df_cost_of_sales_ptype['銷別']=='D') &                                            (df_cost_of_sales_ptype['PN2']==Product_two_ptype) &                                            (df_cost_of_sales_ptype['年月']==etime)]['單價'].item() * 2204.62
                else:
                    df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本'] =                                             df_cost_of_sales_category[(df_cost_of_sales_category['銷別']=='D') &                                            (df_cost_of_sales_category['產品']==Product_Category) &                                            (df_cost_of_sales_category['年月']==etime)]['單價'].item() * 2204.62
            except:
                df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本'] = 0


            df_Product_cost_schedule_Items.loc[59+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本']/2204.62).round(2)

            df_Product_cost_schedule_Items.loc[60+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本'] -                                                                df_Product_cost_schedule_Items.loc[58+index_diff,'每噸成本']
            df_Product_cost_schedule_Items.loc[60+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[60+index_diff,'每噸成本']/2204.62).round(2)
            df_Product_cost_schedule_Items.loc[60+index_diff,'材料單價'] = df_Product_cost_schedule_Items.loc[60+index_diff,'每噸成本'] /                                                                df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本']

            df_Product_cost_schedule_Items.loc[55+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本'] -                                                                df_Product_cost_schedule_Items.loc[54+index_diff,'每噸成本']
            df_Product_cost_schedule_Items.loc[55+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[55+index_diff,'每噸成本']/2204.62).round(2)

            df_Product_cost_schedule_Items.loc[55+index_diff,'材料單價'] = df_Product_cost_schedule_Items.loc[55+index_diff,'每噸成本'] /                                                                df_Product_cost_schedule_Items.loc[59+index_diff,'每噸成本']

            # 外銷
            try:
                if Product_two_ptype != '':
                    df_Product_cost_schedule_Items.loc[61+index_diff,'每噸成本'] =                                             df_cost_of_sales_ptype[(df_cost_of_sales_ptype['銷別']=='X') &                                            (df_cost_of_sales_ptype['PN2']==Product_two_ptype) &                                            (df_cost_of_sales_ptype['年月']==etime)]['變動推'].item()   
                else:
                    df_Product_cost_schedule_Items.loc[61+index_diff,'每噸成本'] =                                             df_cost_of_sales_category[(df_cost_of_sales_category['銷別']=='X') &                                            (df_cost_of_sales_category['產品']==Product_Category) &                                            (df_cost_of_sales_category['年月']==etime)]['變動推'].item()
            except:
                df_Product_cost_schedule_Items.loc[61+index_diff,'每噸成本'] = 0


            df_Product_cost_schedule_Items.loc[62+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[50+index_diff,'每噸成本'] +                                                                df_Product_cost_schedule_Items.loc[61+index_diff,'每噸成本']
            # 管固銷研財費用
            try:
                if Product_two_ptype != '':
                    df_Product_cost_schedule_Items.loc[64+index_diff,'每噸成本'] =                                             df_cost_of_sales_ptype[(df_cost_of_sales_ptype['銷別']=='X') &                                            (df_cost_of_sales_ptype['PN2']==Product_two_ptype) &                                            (df_cost_of_sales_ptype['年月']==etime)]['管研財'].item()   
                else:
                    df_Product_cost_schedule_Items.loc[64+index_diff,'每噸成本'] =                                             df_cost_of_sales_category[(df_cost_of_sales_category['銷別']=='X') &                                            (df_cost_of_sales_category['產品']==Product_Category) &                                            (df_cost_of_sales_category['年月']==etime)]['管研財'].item()
            except:
                df_Product_cost_schedule_Items.loc[64+index_diff,'每噸成本'] = 0    


            df_Product_cost_schedule_Items.loc[65+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[51+index_diff,'每噸成本'] +                                                                df_Product_cost_schedule_Items.loc[64+index_diff,'每噸成本']

            df_Product_cost_schedule_Items.loc[66+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[62+index_diff,'每噸成本'] +                                                                df_Product_cost_schedule_Items.loc[65+index_diff,'每噸成本']
            df_Product_cost_schedule_Items.loc[66+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[66+index_diff,'每噸成本']/2204.62).round(2)

            # 銷售值
            try:
                if Product_two_ptype != '':
                    df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本'] =                                             df_cost_of_sales_ptype[(df_cost_of_sales_ptype['銷別']=='X') &                                            (df_cost_of_sales_ptype['PN2']==Product_two_ptype) &                                            (df_cost_of_sales_ptype['年月']==etime)]['單價'].item() * 2204.62
                else:
                    df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本'] =                                             df_cost_of_sales_category[(df_cost_of_sales_category['銷別']=='X') &                                            (df_cost_of_sales_category['產品']==Product_Category) &                                            (df_cost_of_sales_category['年月']==etime)]['單價'].item() * 2204.62
            except:
                df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本'] = 0


            df_Product_cost_schedule_Items.loc[67+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本']/2204.62).round(2)

            df_Product_cost_schedule_Items.loc[68+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本'] -                                                                df_Product_cost_schedule_Items.loc[66+index_diff,'每噸成本']
            df_Product_cost_schedule_Items.loc[68+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[68+index_diff,'每噸成本']/2204.62).round(2)
            df_Product_cost_schedule_Items.loc[68+index_diff,'材料單價'] = df_Product_cost_schedule_Items.loc[68+index_diff,'每噸成本'] /                                                                df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本']

            df_Product_cost_schedule_Items.loc[63+index_diff,'每噸成本'] = df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本'] -                                                                df_Product_cost_schedule_Items.loc[62+index_diff,'每噸成本']
            df_Product_cost_schedule_Items.loc[63+index_diff,'每噸用量'] = (df_Product_cost_schedule_Items.loc[63+index_diff,'每噸成本']/2204.62).round(2)

            df_Product_cost_schedule_Items.loc[63+index_diff,'材料單價'] = df_Product_cost_schedule_Items.loc[63+index_diff,'每噸成本'] /                                                                df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本']

            df_Product_cost_schedule_Items.loc[66+index_diff,'材料單價'] = df_Product_cost_schedule_Items.loc[66+index_diff,'每噸成本'] / 32.8
            df_Product_cost_schedule_Items.loc[67+index_diff,'材料單價'] = df_Product_cost_schedule_Items.loc[67+index_diff,'每噸成本'] / 32.8       
            
            if df_Product_cost_schedule_Items_schema is None:
                # 加上流水號
                def order_cost_ton(df, kind):
                    fb_rows = df[(df['代碼'].str.startswith(kind)) & (df['料號']!='')].copy()

                    if kind == 'FB': limit_length = 10
                    elif kind == 'CY': limit_length = 1
                    elif kind == 'CT': limit_length = 12
                    elif kind == 'CH': limit_length = 13    

                    fb_rows_sorted = fb_rows.sort_values('每噸成本', ascending=False).reset_index(drop=True).head(limit_length)
                    fb_rows_sorted['代碼'] = [kind + str(i+1) for i in range(0,len(fb_rows_sorted))]

                    subtotal_row = df[(df['代碼'] == kind) & (df['料號']=='')]

                    subtotal = pd.concat([fb_rows_sorted, subtotal_row], ignore_index=True)
                    return subtotal

                fb_rows_sort_FB = order_cost_ton(df_Product_cost_schedule_Items, 'FB')
                fb_rows_sort_CY = order_cost_ton(df_Product_cost_schedule_Items, 'CY')
                fb_rows_sort_CT = order_cost_ton(df_Product_cost_schedule_Items, 'CT')
                fb_rows_sort_CH = order_cost_ton(df_Product_cost_schedule_Items, 'CH')

                df_Product_cost_schedule_Items = pd.concat([fb_rows_sort_FB,
                                   df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['代碼'] == 'WS'],
                                   fb_rows_sort_CY,
                                   fb_rows_sort_CT,
                                   fb_rows_sort_CH,
                                  df_Product_cost_schedule_Items.loc[\
                                  df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='直接原料合計'].index[0]:,:]],
                                  ignore_index=True) 
                

                index_FB = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='纖維原料小計'].index[0]
                index_WS = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='損紙_白道林(二級)'].index[0]
                index_CY = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='填料小計'].index[0]
                index_CT = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='塗料小計'].index[0]
                index_CH = df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱']=='化工原料小計'].index[0]        

                if mname == 'NCR':
                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[28,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                        if df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'].item() < 0:
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] = 0
                        if df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'].item() < 0:
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] = 0                        


                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='NCR') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']        
                elif mname == '含浸':
                    if Product_Category not in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[28,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                         df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
                        if df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'].item() < 0:
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] = 0
                        if df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'].item() < 0:
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] = 0                        


                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].sum()
                    else:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                         (df_reel_material_grouped[(df_reel_material_grouped['分類別']=='含浸美紋') & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==78)].reset_index(drop=True).set_index('料號')['KG']                                          / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                         df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']        
                    
                else:
                    if Product_Category not in ['格拉新']:
                        if Product_two_ptype != '':
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                             (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==float(mname[2:])) & (df_reel_material_grouped['PN2']==Product_two_ptype)].reset_index(drop=True).set_index('料號')['KG']                                              / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].sum()
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                             df_Product_cost_schedule_Items.loc[28,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                             df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                             df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']            
                        else:                        
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                             (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CT') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']                                              / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸用量'].sum()
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                             df_Product_cost_schedule_Items.loc[28,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CY+1:index_CT-2,'每噸成本'].sum()
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                             df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                             df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CT') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']

                    if Product_Category in ['格拉新']:
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸用量'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].sum()
                        df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].sum()
                    else:
                        if Product_two_ptype != '':
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                             (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==float(mname[2:])) & (df_reel_material_grouped['PN2']==Product_two_ptype)].reset_index(drop=True).set_index('料號')['KG']                                              / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].sum()
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].sum()
                        else:                        
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量'] =                                             (df_reel_material_grouped[(df_reel_material_grouped['分類別']==Product_Category) & (df_reel_material_grouped['RM_Kind']=='CH') & (df_reel_material_grouped['PD']==float(mname[2:]))].reset_index(drop=True).set_index('料號')['KG']                                              / df_Product_cost_schedule.loc[0,'生產量(噸)']).sum() - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸用量'].sum()
                            df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] =                                             df_Product_cost_schedule_Items.loc[index_CH,'每噸成本'] - df_Product_cost_schedule_Items.loc[index_CT+1:index_CH-2,'每噸成本'].sum()
                    df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'材料單價'] =                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸成本'] /                                     df_Product_cost_schedule_Items.loc[(df_Product_cost_schedule_Items['代碼']=='CH') & (df_Product_cost_schedule_Items['名稱']=='其他'),'每噸用量']
            
#             cost_df = df_Product_cost_schedule_Items.loc[:df_Product_cost_schedule_Items[df_Product_cost_schedule_Items['名稱'] == '直接原料合計'].index[0], :]
            cost_df = df_Product_cost_schedule_Items.copy()
    
            elapsed = time.time() - start_time
            logging.info(f"df_Product_cost_schedule time is: {elapsed:.2f} seconds")

            return df_Product_cost_schedule,cost_df
        
        
        dt = datetime.datetime.strptime(stime, "%Y%m")

        stime_1 = (dt - relativedelta(months=1)).strftime("%Y%m")
        stime_2 = (dt - relativedelta(months=2)).strftime("%Y%m")

        etime_1 = stime
        etime_2 = stime_1  

        if mname == 'NCR':
            df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname='PM19',
                                                        Product_Category='NCR原紙',Product_two_ptype='QC')
            df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
            if etime == '202502':
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,'PM19','NCR原紙','QC',
                                                                                      df_Product_cost_schedule_Items_schema)
                cost_df_temp_NCR_Base_Paper = pd.concat([cost_df_temp_1,cost_df_temp_2])       

                df_Product_cost_schedule_Items_schema = None
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)
                df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)                  
            elif etime == '202501':
                cost_df_temp_NCR_Base_Paper = cost_df_temp_1.copy()
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)                
            else:
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,'PM19','NCR原紙','QC',
                                                                                      df_Product_cost_schedule_Items_schema)
                df_Product_cost_schedule_temp_3,cost_df_temp_3 = Product_Cost_Details(stime_2,etime_2,'PM19','NCR原紙','QC',
                                                                                      df_Product_cost_schedule_Items_schema)

                cost_df_temp_NCR_Base_Paper = pd.concat([cost_df_temp_1,cost_df_temp_2,cost_df_temp_3])       

                df_Product_cost_schedule_Items_schema = None
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)
                df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)
                df_Product_cost_schedule_temp_3,cost_df_temp_3 = Product_Cost_Details(stime_2,etime_2,mname,Product_Category,
                                    Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)     
        elif mname == '含浸':
            df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname='PM18',
                                                        Product_Category='含浸原紙',Product_two_ptype='QE')
            df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
            if etime == '202502':
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,'PM18','含浸原紙','QE',
                                                                                      df_Product_cost_schedule_Items_schema)
                cost_df_temp_NCR_Base_Paper = pd.concat([cost_df_temp_1,cost_df_temp_2])       

                df_Product_cost_schedule_Items_schema = None
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)
                df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)                  
            elif etime == '202501':
                cost_df_temp_NCR_Base_Paper = cost_df_temp_1.copy()
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)                
            else:
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,'PM18','含浸原紙','QE',
                                                                                      df_Product_cost_schedule_Items_schema)
                df_Product_cost_schedule_temp_3,cost_df_temp_3 = Product_Cost_Details(stime_2,etime_2,'PM18','含浸原紙','QE',
                                                                                      df_Product_cost_schedule_Items_schema)

                cost_df_temp_NCR_Base_Paper = pd.concat([cost_df_temp_1,cost_df_temp_2,cost_df_temp_3])       

                df_Product_cost_schedule_Items_schema = None
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)
                df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,mname,Product_Category,
                                     Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)
                df_Product_cost_schedule_temp_3,cost_df_temp_3 = Product_Cost_Details(stime_2,etime_2,mname,Product_Category,
                                    Product_two_ptype,df_Product_cost_schedule_Items_schema,cost_df_temp_NCR_Base_Paper)                  
        else:
            if etime == '202502':
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                                                                                      Product_two_ptype)
                df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,mname,Product_Category,
                                                                    Product_two_ptype,df_Product_cost_schedule_Items_schema)           
            elif etime == '202501':
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                                                                                      Product_two_ptype)                
            else:
                df_Product_cost_schedule_temp_1,cost_df_temp_1 = Product_Cost_Details(stime,etime,mname,Product_Category,
                                                                                                      Product_two_ptype)
                df_Product_cost_schedule_Items_schema = cost_df_temp_1.loc[:,['代碼','料號','名稱']].copy()
                df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Details(stime_1,etime_1,mname,Product_Category,
                                                                    Product_two_ptype,df_Product_cost_schedule_Items_schema)
                df_Product_cost_schedule_temp_3,cost_df_temp_3 = Product_Cost_Details(stime_2,etime_2,mname,Product_Category,
                                                                    Product_two_ptype,df_Product_cost_schedule_Items_schema)

        if two_month=='1':
            if etime == '202501':              
                df_Product_cost_schedule = df_Product_cost_schedule_temp_1.copy()
                cost_df = cost_df_temp_1.copy()               
            else:
                df_Product_cost_schedule = pd.concat([df_Product_cost_schedule_temp_1,df_Product_cost_schedule_temp_2])        

                cost_df = pd.concat([cost_df_temp_1,cost_df_temp_2])
        else:
            if etime == '202502':
                df_Product_cost_schedule = pd.concat([df_Product_cost_schedule_temp_1,df_Product_cost_schedule_temp_2])        

                cost_df = pd.concat([cost_df_temp_1,cost_df_temp_2])                
            elif etime == '202501':
                df_Product_cost_schedule = df_Product_cost_schedule_temp_1.copy()
                cost_df = cost_df_temp_1.copy()                
            else:
                df_Product_cost_schedule = pd.concat([df_Product_cost_schedule_temp_1,df_Product_cost_schedule_temp_2,df_Product_cost_schedule_temp_3])        

                cost_df = pd.concat([cost_df_temp_1,cost_df_temp_2,cost_df_temp_3])
        
        if not cost_df.empty:
            
            # === 設定 metadata 結構 ===
            result = {
                "metadata": {
                    "Production": {
                        "label": "生產量",
                        "unit": "噸"
                    },
                    "Cost": {
                        "Code": {
                            "label": "代碼",
                            "unit": ""
                        },
                        "Mat_id_erp": {
                            "label": "料號",
                            "unit": ""
                        },
                        "Schsnm": {
                            "label": "名稱",
                            "unit": ""
                        },                        
                        "UP": {
                            "label": "材料單價",
                            "unit": "%"
                        },
                        "ConsPT": {
                            "label": "每噸用量",
                            "unit": "KG"
                        },
                        "CostPT": {
                            "label": "每噸成本",
                            "unit": "NTD"
                        }
                    },
                    "Rate": {
                        "Yield": {
                            "label": "得率",
                            "unit": "%",
                            "description": "Good Units / Total Input Units"
                        },
                        "Matching": {
                            "label": "配合率",
                            "unit": "%",
                            "description": "Actual Quantity / Planned Quantity"
                        }
                    }
                },
                "data": defaultdict(dict)
            }

            for _, row in cost_df.iterrows():
                ym = str(row["月份"])
                code = str(row["代碼"])
                name = str(row["名稱"]).strip()
                prefix = ''.join([c for c in code if not c.isdigit()]) or "Total" 

                if "Cost" not in result["data"][ym]:
                    result["data"][ym]["Cost"] = {}

                if prefix not in result["data"][ym]["Cost"]:
                    result["data"][ym]["Cost"][prefix] = {}

                key_name = "Subtotal" if prefix in ["FB", "CY", "CT", "CH"] else code
                
                def safe_value(val):
                    return val if pd.notna(val) and np.isfinite(val) else None        

                if (code in ["FB", "CY", "CT", "CH"]) & ("小計" in name):
                    result["data"][ym]["Cost"][prefix]["Subtotal"] = {
                        "Id": "",
                        "Code": row["代碼"] if pd.notna(row["代碼"]) else None,
                        "Mat_id_erp": row["料號"] if pd.notna(row["料號"]) else None,
                        "Schsnm": row["名稱"] if pd.notna(row["名稱"]) else None,
                        "UP": safe_value(row["材料單價"]),
                        "ConsPT": safe_value(row["每噸用量"]),
                        "CostPT": safe_value(row["每噸成本"])
                    }
                elif (code in ["FB", "CY", "CT", "CH"]) & ("其他" in name):
                    result["data"][ym]["Cost"][prefix]["other"] = {
                        "Id": "",
                        "Code": row["代碼"] if pd.notna(row["代碼"]) else None,
                        "Mat_id_erp": row["料號"] if pd.notna(row["料號"]) else None,
                        "Schsnm": row["名稱"] if pd.notna(row["名稱"]) else None,
                        "UP": safe_value(row["材料單價"]),
                        "ConsPT": safe_value(row["每噸用量"]),
                        "CostPT": safe_value(row["每噸成本"])
                    }
                else:
                    if prefix == 'COST':
                        result["data"][ym]["Cost"][prefix][code] = {
                            "Id": row["代碼"] if pd.notna(row["代碼"]) else None,
                            "Code": "",
                            "Mat_id_erp": row["料號"] if pd.notna(row["料號"]) else None,
                            "Schsnm": row["名稱"] if pd.notna(row["名稱"]) else None,
                            "UP": safe_value(row["材料單價"]),
                            "ConsPT": safe_value(row["每噸用量"]),
                            "CostPT": safe_value(row["每噸成本"])
                            }                        
                    else:
                        result["data"][ym]["Cost"][prefix][code] = {
                            "Id": "",
                            "Code": row["代碼"] if pd.notna(row["代碼"]) else None,
                            "Mat_id_erp": row["料號"] if pd.notna(row["料號"]) else None,
                            "Schsnm": row["名稱"] if pd.notna(row["名稱"]) else None,
                            "UP": safe_value(row["材料單價"]),
                            "ConsPT": safe_value(row["每噸用量"]),
                            "CostPT": safe_value(row["每噸成本"])
                            }

            # === 建構 Production + Rate 區段 ===
            rate_mapping = {
                "纖維得率": ("Purp", "Yield"),
                "纖維配合率": ("Purp", "Matching"),
                "填料得率": ("Chemicals", "Yield"),
                "填料配合率": ("Chemicals", "Matching"),
                "塗料得率": ("Coatings", "Yield"),
                "塗料配合率": ("Coatings", "Matching")
            }

            for _, row in df_Product_cost_schedule.iterrows():
                ym = str(row["月份"])
                mname = str(row["機台"])

                if "Production" not in result["data"][ym]:
                    result["data"][ym]["Production"] = {}

                if "Rate" not in result["data"][ym]:
                    result["data"][ym]["Rate"] = {}

                # 生產量
                result["data"][ym]["Production"] = row["生產量(噸)"] if pd.notna(row["生產量(噸)"]) else None

                # 比例資料
                for col in rate_mapping:
                    if col in row:
                        group, metric = rate_mapping[col]
                        if group not in result["data"][ym]["Rate"]:
                            result["data"][ym]["Rate"][group] = {}
                        result["data"][ym]["Rate"][group][metric] = row[col] if pd.notna(row[col]) else None

            # === 將 defaultdict 轉回一般 dict（避免 JSON 轉換錯誤） ===
            result["data"] = {ym: dict(detail) for ym, detail in result["data"].items()}
            
            result_json = result.copy()

        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


# 約當量


# In[ ]:


class product_cost_equivalent:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, mname: str, Product_Category: str, Product_two_ptype: str, two_month: str):
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        if not Product_Category:
            return {'success': False, 'message': 'Missing category parameter'}   
        if not Product_two_ptype:
            Product_two_ptype = ''
        if not two_month:
            two_month = 0               
        
        if mname == "18":
            mname = 'PM18'
            mname_t = "'18'"
            sub_r = "'R'"
        elif mname == "19":
            mname = 'PM19'
            mname_t = "'19','C2'"
            sub_r = "'S'"
        elif mname == "20":
            mname = 'PM20'
            mname_t = "'20','C7','C8','C9'"
            sub_r = "'T'"
        elif mname == "21":
            mname = 'PM21'
            mname_t = "'21','C1','C6'"
            sub_r = "'W'"
        else:
            pass               

        def Product_Cost_Equivalent(stime,etime,mname,Product_Category,Product_two_ptype):
            def Work_In_Process(df):
                df = df.dropna(how='all')
                df = df[df['年'].notna()].reset_index(drop=True)
                df['年'] = df['年'].astype(int)
                df['月'] = df['月'].astype(int)
                df['日'] = df['日'].astype(int)

                # 選取欄位

                df = df.loc[:,['年月','年', '月', '日', '號機', '紙別', '基重(原紙)','基重(成品)', '塗佈前', 
                                       '壓光前','複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']]
                # 計算欄位

                df['總計(噸數)'] = df[['塗佈前', '壓光前', '複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']].sum(axis=1, skipna=True).round(3)

                df['基重(原紙)'] = df['基重(原紙)'].apply(
                    lambda x: str(int(x)) if pd.notna(x) and float(x) == int(float(x))
                    else (str(x) if pd.notna(x) else None)
                )

                df['基重(成品)'] = df['基重(成品)'].apply(
                    lambda x: str(int(x)) if pd.notna(x) and float(x) == int(float(x))
                    else (str(x) if pd.notna(x) else None)
                )                    

                df['紙別基重(塗前)'] = df['號機'].astype(str) + df['紙別'].astype(str) + df['基重(原紙)'].astype(str)

                df['塗前'] = df[['塗佈前']].sum(axis=1, skipna=True)
                df['塗後'] = df[['壓光前', '複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']].sum(axis=1, skipna=True).round(3)

                df = df.replace({pd.NA: None, np.nan: None})

                return df.copy()  


            def classify_pn4(value):
                if pd.isna(value):
                    return None

                value_str = str(value)

                # 若中間為 NCR 或開頭為 UCR
                if value_str[1:4] == 'NCR' or value_str.startswith('UCR'):
                    return 'QC'
                elif value_str.startswith('M'):
                    return 'QE'
                elif value_str.isdigit():
                    return value_str[:2]  # 數字，取前兩位字串
                else:
                    return value_str[:2]  # 其他，一樣取前兩碼     

            # 讀取期末在產品(MES)
            def search_InProcess_MES(etime):

                dt = datetime.datetime.strptime(etime, "%Y%m")
                etime_t = (dt + relativedelta(months=1) - timedelta(days=1))
                etime_t = etime_t.strftime('%Y-%m-%d')

                srv_SRVAD1 = self.servers['SRVAD1'] 
                with srv_SRVAD1['create_engine'][0].connect() as conn:                
                    sql =   """
                        ;with raw_data as
                        (
                            select 
                                a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                            from openquery([10.10.1.27],'select * from [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] where Creation_date >= dateadd(m,-6,getdate())') a
                            inner join adpack b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass <> 'A') and substring(batch_no,10,2) = 'SH'
                            where 1=1
                            and bdate between '"""+ str(etime_t) +"""' and '"""+ str(etime_t) +"""' 
                            and re <> 0 and a.status_code = 'S'

                            union

                            select a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                            from openquery([10.10.1.27],'select * from [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] where Creation_date >= dateadd(m,-6,getdate())') a
                            inner join adsel b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass IN ('B','P') or b.pclass is null) and substring(batch_no,10,2) = 'SH'
                            where 1=1
                            and bdate between '"""+ str(etime_t) +"""' and '"""+ str(etime_t) +"""' 
                            and nstation not in('SP','WP','WH') 
                            and re <> 0 and a.status_code = 'S'
                            --order by runno, batch_no, ptype, psize1, psize2, x_yn, bhno
                        )
                        SELECT mname_2 AS mname,ptype,pgramg,SUM(T) AS T
                        FROM
                        (
                            SELECT runno,mname_2,bdate,batch_no,ptype,pgramg,psize1,psize2,store,ExportSales,pclass,rewt,SUM(re) AS re,SUM(T) AS T,
                            count(*) as amount
                            FROM
                            (
                                SELECT *,rewt*re*0.0004535924 AS T,
                                CASE WHEN x_yn = 'Y' Then '外銷' ELSE '內銷' END AS ExportSales,
                                CASE WHEN x_yn = 'Y' Then 'A4FG'
                                WHEN x_yn = 'N' AND substring(runno,1,1) = 'R' THEN 'A3FG'
                                WHEN x_yn = 'N' AND substring(runno,1,1) = 'S' THEN 'A2FG'
                                WHEN x_yn = 'N' AND substring(runno,1,1) = 'W' THEN 'A1FG'
                                END AS store,
                                CASE WHEN ptype like 'H%' THEN 'NCR'
                                     WHEN left(runno,1) = 'R' THEN 'PM18'
                                     WHEN left(runno,1) = 'S' THEN 'PM19'
                                     WHEN left(runno,1) = 'T' THEN 'PM20'
                                     WHEN left(runno,1) = 'W' THEN 'PM21'
                                END AS mname_2
                                FROM raw_data
                            ) t
                            GROUP BY runno,mname_2,bdate,batch_no,ptype,pgramg,psize1,psize2,store,ExportSales,pclass,rewt
                        ) m
                        GROUP BY mname_2,ptype,pgramg          
                    """       
                    query = conn.execute(text(sql))  
                    df_ERP_SH = pd.DataFrame([dict(i) for i in query]) 

                    sql =   """
                        SELECT 
                            mname_2 AS mname,
                            ptype,
                            pgramg,
                            sum(weigh) as T 

                        FROM
                        (
                            SELECT *,CASE 
                                WHEN x_yn = 'Y' AND pstatus = '成品' THEN 'A4FG'
                                WHEN pstatus = '成品' THEN 
                                    CASE 
                                        WHEN left(relno,1) = 'R' AND prodn <> 'R' THEN 'A3FG'
                                        WHEN left(relno,1) = 'S' AND prodn <> 'R' THEN 'A2FG'
                                        WHEN (left(relno,1) = 'T' AND prodn <> 'R') 
                                             OR (left(relno,1) = 'R' AND prodn <> 'R') 
                                             OR (left(relno,1) = 'S' AND prodn <> 'R') THEN 'A6FG'
                                        WHEN left(relno,1) = 'W' AND prodn <> 'R' THEN 'A7FG'   
                                        ELSE NULL  -- 如果沒有符合條件，不設值
                                    END
                                ELSE 'FTA.SFG.SR.PM' + CAST(left(relno,1) AS VARCHAR)  -- 非 "成品" 情況，store 依 mname 設定
                            END AS store,
                            CASE WHEN left(relno,1) = 'R' THEN 'PM18'
                                 WHEN left(relno,1) = 'S' THEN 'PM19'
                                 WHEN left(relno,1) = 'T' THEN 'PM20'
                                 WHEN left(relno,1) = 'W' THEN 'PM21'
                            END AS mname_2
                            FROM
                            (
                                select *,
                                CASE 
                                    WHEN prod = '1' THEN 
                                        CASE 
                                            WHEN LEFT(ptype, 1) = 'H' AND CAST(width AS FLOAT) >= 100 
                                                THEN RIGHT('00' + CAST(width AS VARCHAR), 4) + 'RL00'
                                            WHEN LEFT(ptype, 1) = 'H' OR CAST(width AS FLOAT) < 100 
                                                THEN 
                                                    CASE 
                                                        WHEN RIGHT(CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) AS VARCHAR), 1) = '5' 
                                                            THEN RIGHT('00' + CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) - 1 AS VARCHAR), 3) + 'KRL00'
                                                        WHEN RIGHT(CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) AS VARCHAR), 1) = '8' 
                                                            THEN RIGHT('00' + CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) - 2 AS VARCHAR), 3) + 'KRL00'
                                                        ELSE RIGHT('00' + CAST(CAST(width AS FLOAT) * 10 AS VARCHAR), 3) + 'KRL00'
                                                    END
                                            ELSE 
                                                RIGHT('00' + CAST(width AS VARCHAR), 4) + 'RL00'
                                        END
                                    WHEN prod IN ('2', '4', '7', '8') THEN 'R'
                                    ELSE NULL 
                                END AS prodn,
                                CASE WHEN prod = 1 THEN '成品'
                                WHEN prod = 2 Then '裁切'
                                WHEN prod = 4 Then '中倉'
                                WHEN prod = 7 Then '分條'
                                WHEN prod = 8 Then '含浸' END AS pstatus

                                from adwind 
                                where 1=1
                                and bdate between '"""+ str(etime_t) +"""' and '"""+ str(etime_t) +"""'  
                                and prod not in('3','5','6','9') 
                                --order by runno, prod, ptype, pclass, width, pgramg, x_yn, relno, swinno
                            ) m
                        ) t
                        WHERE store NOT LIKE '%SR%'
                        GROUP BY mname_2,ptype,pgramg
                    """
                    query = conn.execute(text(sql))  
                    df_ERP_SR = pd.DataFrame([dict(i) for i in query])   

                srv_SRVAD2 = self.servers['SRVAD2'] 
                with srv_SRVAD2['create_engine'][0].connect() as conn:                    
                    sql =   """
                        --ACAA040I3.ASP
                        DECLARE @sdate varchar(10) = '"""+ str(etime_t) +"""'
                        DECLARE @edate varchar(10) = '"""+ str(etime_t) +"""'

                        ;With raw_data as
                        (
                            SELECT *
                            FROM
                            (
                                --SRVAD2
                                select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation,sptype,
                                CASE WHEN pm='W' AND nstation = 'WR' Then '再捲機'
                                WHEN pm='W' AND nstation = 'WC' Then '塗佈機'
                                WHEN pm='W' AND nstation = 'WE' Then '壓光機'
                                WHEN pm='W' AND nstation = 'WW' Then '複捲機'

                                WHEN pm='T' AND nstation = 'TR' Then '再捲機'
                                WHEN pm='T' AND nstation = 'TC' Then '塗佈機'
                                WHEN pm='T' AND nstation = 'TE' Then '壓光機'
                                WHEN pm='T' AND nstation = 'TW' Then '複捲機'

                                WHEN pm='S' AND nstation = 'SW' Then '複捲機'
                                WHEN pm='R' AND nstation = 'RW' Then '複捲機'

                                END AS 機台
                                from [pm21].[dbo].[adbuff_prod] where cbdate between @sdate and @edate

                                UNION ALL

                                select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation,sptype,
                                CASE WHEN pm='W' AND nstation = 'WC' Then '塗佈機'
                                WHEN pm='W' AND nstation = 'WS' Then '裁切機'
                                WHEN pm='W' AND nstation = 'WW' Then '分條機'
                                WHEN pm='W' AND nstation = 'WE' Then '壓光機'

                                WHEN pm='T' AND nstation = 'TR' Then '再捲機'
                                WHEN pm='T' AND nstation = 'TC' Then '塗佈機'
                                WHEN pm='T' AND nstation = 'TE' Then '壓光機'
                                WHEN pm='T' AND nstation = 'TS' Then '裁切機'

                                WHEN pm='S' AND nstation = 'SE' Then '壓光機'
                                WHEN pm='S' AND nstation = 'SC' Then '塗佈機'
                                WHEN pm='S' AND nstation = 'SS' Then '裁切機'
                                WHEN pm='S' AND nstation = 'SW' Then '分條機'

                                WHEN pm='R' AND nstation = 'RS' Then '裁切機'

                                END AS 機台

                                from [SRVAD2].[pm21].[dbo].[adwind_prod] where cbdate between @sdate and @edate
                                UNION ALL
                                select cbdate,pm,mname,ptype,gramg,pgramg,(rewt*re/2204.62),nstation as weigh,sptype,
                                CASE WHEN pm='W' AND nstation = 'WH' Then '選紙班'
                                WHEN pm='W' AND nstation = 'WP' Then '包裝機'

                                WHEN pm='T' AND nstation = 'TH' Then '選紙班'
                                WHEN pm='T' AND nstation = 'TP' Then '包裝機'

                                WHEN pm='S' AND nstation = 'SH' Then '選紙班'
                                WHEN pm='S' AND nstation = 'SP' Then '包裝機'

                                WHEN pm='R' AND nstation = 'RH' Then '選紙班'
                                END AS 機台

                                from [SRVAD2].[pm21].[dbo].[adstock_prod] where cbdate between @sdate and @edate
                            ) t
                            WHERE 1=1
                            AND 機台 is not null --AND gramg is not null 
                            AND len(ptype) > 0
                            --AND ptype = 'KL00' AND pgramg = '58'
                        )
                        SELECT 
                        YEAR(cbdate) AS 年,
                        MONTH(cbdate) AS 月,
                        DAY(cbdate) AS 日,
                        CASE WHEN pm='R' THEN 'PM18' WHEN pm='S' THEN 'PM19' WHEN pm='T' THEN 'PM20' WHEN pm='W' THEN 'PM21' ELSE '' END AS 號機,
                        ptype AS 紙別,
                        pgramg AS '基重(原紙)',
                        pgramg AS '基重(成品)',
                        ISNULL(SUM([塗佈前]),0) AS [塗佈前],
                        ISNULL(SUM([壓光前]),0) AS [壓光前],
                        ISNULL(SUM([複捲前(含中間倉)]),0) AS [複捲前(含中間倉)],
                        ISNULL(SUM([截切前]),0) AS [截切前],
                        ISNULL(SUM([包裝前]),0) AS [包裝前],
                        ISNULL(SUM([已包未入庫]),0) AS [已包未入庫]
                        FROM (
                            SELECT 
                                cbdate,pm,ptype,gramg,pgramg,sptype,
                                CASE WHEN ptype like '%NCR' Then ''
                                WHEN ptype like '%MM' Then ''
                                WHEN 機台 IN ('再捲機','塗佈機') THEN '塗佈前'
                                WHEN 機台 = '壓光機' THEN '壓光前'
                                WHEN 機台 IN ('複捲機','分條機') THEN '複捲前(含中間倉)'
                                WHEN 機台 = '裁切機' THEN '截切前'
                                WHEN 機台 IN ('選紙班','包裝機') THEN '包裝前'
                                END AS 機台,
                                weigh
                            FROM raw_data
                        ) AS source
                        PIVOT (
                            SUM(weigh)
                            FOR 機台 IN ([塗佈前],[壓光前],[複捲前(含中間倉)],[截切前],[包裝前],[已包未入庫])
                        ) AS pivot_table
                        --WHERE pm = 'W'
                        GROUP BY cbdate,pm,ptype,pgramg
                        ORDER BY cbdate,pm desc,ptype,pgramg
                    """       
                    query = conn.execute(text(sql))  
                    df_InProcess = pd.DataFrame([dict(i) for i in query])

                df_ERP_SR_SH = pd.concat([df_ERP_SR,df_ERP_SH],ignore_index=True)
                df_ERP_SR_SH['年'] = df_InProcess.loc[0,'年']
                df_ERP_SR_SH['月'] = df_InProcess.loc[0,'月']
                df_ERP_SR_SH['日'] = df_InProcess.loc[0,'日']
                df_ERP_SR_SH.rename(columns={'mname':'號機','ptype':'紙別','pgramg':'基重(成品)','T':'已包未入庫'},inplace=True)
                df_ERP_SR_SH['基重(原紙)'] = df_ERP_SR_SH['基重(成品)'].copy()
                df_ERP_SR_SH['塗佈前'] = 0.0
                df_ERP_SR_SH['壓光前'] = 0.0
                df_ERP_SR_SH['複捲前(含中間倉)'] = 0.0
                df_ERP_SR_SH['截切前'] = 0.0
                df_ERP_SR_SH['包裝前'] = 0.0
                df_ERP_SR_SH['已包未入庫'] = df_ERP_SR_SH['已包未入庫'].astype(float)
                
                df_result = pd.concat([df_InProcess,df_ERP_SR_SH],ignore_index=True)
                
                df_result['號機'] = np.where(
                    df_result['紙別'].str.endswith('NCR'),
                    df_result['號機'],
                    np.where(
                        df_result['紙別'].str.startswith('H'), 
                        'NCR',
                        np.where(
                            df_result['紙別'].str.startswith('TR'),
                            '含浸',
                            df_result['號機']
                        )
                    )
                )                    

                df_result = df_result.groupby(['年','月','日','號機','紙別','基重(原紙)','基重(成品)'])                    .agg(a=('塗佈前','sum'), 
                         b=('壓光前','sum'),
                         c=('複捲前(含中間倉)','sum'), 
                         d=('截切前','sum'),
                         e=('包裝前','sum'),
                         f=('已包未入庫','sum'),
                        ).reset_index()  

                df_result = df_result.rename(columns={
                    'a': '塗佈前',
                    'b': '壓光前',
                    'c': '複捲前(含中間倉)',
                    'd': '截切前',
                    'e': ' 包裝前',
                    'f': '已包未入庫',
                })
                
                df_result['年月'] = etime

                return df_result         
            
            
            # 讀取入庫量(MES)
            def search_Inventory_MES(etime):

                yearmonth = etime

                dt = datetime.datetime.strptime(etime, "%Y%m")
                stime = dt.strftime('%Y-%m-%d')
                etime = (dt + relativedelta(months=1) - timedelta(days=1)).strftime('%Y-%m-%d')  

                df_RE_transRate = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\FTA平版料號轉換率\FTA 平版料號轉換率.xlsx',
                                          sheet_name='工作表1',skiprows=0)
                df_RE_transRate = df_RE_transRate[df_RE_transRate['TO 單位類別'] != 'Length']
                df_RE_transRate['料號_2'] = df_RE_transRate['料號'].str[-13:]
                df_RE_transRate_reduce = df_RE_transRate.groupby(['料號_2','轉換率']).size().reset_index().groupby(['料號_2'])['轉換率'].min().reset_index()

                srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
                with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:                
                    sql =   """
                        SELECT [PROCESS_CODE]
                              ,[SERVER_CODE]
                              ,[BATCH_ID]
                              ,[BATCH_LINE_ID]
                              ,[STATUS_CODE]
                              ,[ORGCODE]
                              ,[RXID]
                              ,[PREVIOUS_RXID]
                              ,[BATCH_NO]
                              ,[MACHINE_NO]
                              ,[ITEM_NO]
                              ,SUBSTRING([ITEM_NO],2,4) as ptype
                              ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                              ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                              ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                              ,[SUBINVENTORY_CODE]
                              ,[LOCATOR]
                              ,[TRANSACTION_QUANTITY]
                              ,[TRANSACTION_UOM]
                              ,[SECONDARY_TRANSACTION_QUANTITY]
                              ,[SECONDARY_UOM_CODE]
                              ,[TRANSACTION_DATE]
                              ,convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) as bdate
                              ,[LOT_NUMBER]
                              ,[STATUS]
                          FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST]
                          WHERE 1=1
                          AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                          AND MACHINE_NO IN ('18','19','20','21')
                          AND SUBINVENTORY_CODE != 'SFG'
                          AND STATUS_CODE = 'S'

                          UNION ALL

                        SELECT [PROCESS_CODE]
                              ,[SERVER_CODE]
                              ,[BATCH_ID]
                              ,[BATCH_LINE_ID]
                              ,[STATUS_CODE]
                              ,[ORGCODE]
                              ,[RXID]
                              ,[PREVIOUS_RXID]
                              ,[BATCH_NO]
                              ,[MACHINE_NO]
                              ,[ITEM_NO]
                              ,SUBSTRING([ITEM_NO],2,4) as ptype
                              ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                              ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                              ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                              ,[SUBINVENTORY_CODE]
                              ,[LOCATOR]
                              ,[TRANSACTION_QUANTITY]
                              ,[TRANSACTION_UOM]
                              ,[SECONDARY_TRANSACTION_QUANTITY]
                              ,[SECONDARY_UOM_CODE]
                              ,[TRANSACTION_DATE]
                              ,convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) as bdate
                              ,[LOT_NUMBER]
                              ,[STATUS]
                          FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P211_IN_MMT_PROD_ST]
                          where 1=1
                          AND (
                            (SUBSTRING([ITEM_NO],2,4) like 'MM%' AND [ITEM_NO] like '%R') 
                            OR 
                            (RIGHT(SUBSTRING([ITEM_NO],2,4),3) = 'NCR' AND [ITEM_NO] like '%R')
                          )
                          AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                          AND [STATUS_CODE] = 'S'          
                    """       
                    query = conn.execute(text(sql))
                    df_inventory_250 = pd.DataFrame([dict(i) for i in query])

                df_inventory_250['料號_2'] = df_inventory_250['ITEM_NO'].str[-13:]   

                df_inventory_250_C = df_inventory_250[df_inventory_250['STATUS'] == 'C']
                df_inventory_250_M = df_inventory_250[df_inventory_250['STATUS'] == 'M']
                df_inventory_250_C = df_inventory_250_C[~df_inventory_250_C['RXID'].isin(list(df_inventory_250[df_inventory_250['STATUS'] == 'M']['PREVIOUS_RXID']))]
                df_inventory_250_M = df_inventory_250_M.loc[df_inventory_250_M.groupby('PREVIOUS_RXID')['TRANSACTION_DATE'].idxmax()]

                df_inventory_250_latest = pd.concat([df_inventory_250_C,df_inventory_250_M],ignore_index=True)
                df_inventory_250_latest = df_inventory_250_latest.loc[:,['bdate','MACHINE_NO','ptype', 'gramg','ITEM_NO','TRANSACTION_QUANTITY','TRANSACTION_UOM',
                                              'SECONDARY_TRANSACTION_QUANTITY','SECONDARY_UOM_CODE','料號_2']]
                df_inventory_250_latest = df_inventory_250_latest.merge(df_RE_transRate_reduce,on='料號_2',how='left')
                df_inventory_250_latest['weigh'] = np.where(
                    df_inventory_250_latest['SECONDARY_UOM_CODE'].isna(),
                    df_inventory_250_latest['TRANSACTION_QUANTITY'] * 1000,
                    df_inventory_250_latest['SECONDARY_TRANSACTION_QUANTITY'].astype(float) * df_inventory_250_latest['轉換率'] / 1000.0
                )
                df_inventory_250_latest['gramg'] = df_inventory_250_latest['gramg'].astype(float) / 10.0
                df_inventory_250_latest['MACHINE_NO'] = np.where(
                    df_inventory_250_latest['ptype'].str.endswith('NCR'),
                    'PM' + df_inventory_250_latest['MACHINE_NO'],
                    np.where(
                        df_inventory_250_latest['ptype'].str.startswith('H'),
                        'NCR',
                        np.where(
                            df_inventory_250_latest['ptype'].str.startswith('T'),
                            '含浸',
                            'PM' + df_inventory_250_latest['MACHINE_NO']
                        )        
                    )
                )
                df_inventory_250_result = df_inventory_250_latest.groupby(['MACHINE_NO','ptype','gramg'])['weigh'].sum().reset_index()

                df_inventory_250_result.rename(columns={'MACHINE_NO':'機台','ptype':'PN4','gramg':'基重','weigh':'合計(kg)'},inplace=True)

                df_inventory_250_result['基重'] = df_inventory_250_result['基重'].round(1).astype(str)

                df_inventory_250_result['合計(kg)'] = df_inventory_250_result['合計(kg)'].astype(float).round(1)
                df_inventory_250_result['紙別基重'] = df_inventory_250_result['機台'] + df_inventory_250_result['PN4'] + df_inventory_250_result['基重']
                df_inventory_250_result['紙別基重'] = df_inventory_250_result['紙別基重'].str.replace(r'\.0$', '', regex=True)
                df_inventory_250_result['年月'] = yearmonth

                return df_inventory_250_result
            
            def material_data(etime,df_Equivalent_Output_Before_Apportionment):

                df_RMData = None

                # 讀取原物料名稱_成本
                etime_sheet_name = str(int(etime[:4])-1911)

                base_path = r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\會計提供'

                # 先試主檔
                try:
                    df_RMData = pd.read_excel(
                        fr'{base_path}\RMData_料號成本.xlsx',
                        sheet_name=etime_sheet_name,
                        header=0
                    )
                except Exception:
                    pass    

                # 如果主檔沒有，再找歷史檔
                if df_RMData is None:
                    for year in range(int(etime[:4]), 2015, -1):
                        try:
                            file_path = fr'{base_path}\RMData_料號成本_{year}.xlsx'

                            df_RMData = pd.read_excel(
                                file_path,
                                sheet_name=etime_sheet_name,
                                header=0
                            )
                            print(f'使用檔案: {file_path}')
                            break

                        except Exception:
                            continue    

                # 防呆檢查
                if df_RMData is None:
                    raise RuntimeError(f'找不到含 sheet {etime_sheet_name} 的 RMData Excel')                  

                month_map = {
                    '01': '1月','02': '2月','03': '3月','04': '4月','05': '5月','06': '6月','07': '7月',
                    '08': '8月','09': '9月','10': '10月','11': '11月','12': '12月'
                }

                etime_cost_col = month_map.get(etime[4:], '未知月份')
                df_RMData.rename(columns={etime_cost_col:'COST_2'},inplace=True)    

                # 讀取 原物料 用量 Data_

                stime_d = (datetime.datetime.strptime(etime, "%Y%m")).strftime('%Y-%m-%d')
                etime_d = (datetime.datetime.strptime(etime, "%Y%m") + relativedelta(months=1)).strftime('%Y-%m-%d')

                srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
                with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:
                    sql =   """
                    SELECT CASE WHEN P210.[TRANSACTION_UOM] = 'KG' THEN [TRANSACTION_QUANTITY]
                                ELSE [TRANSACTION_QUANTITY] * 1000.0 END AS KG
                          ,CASE WHEN len(P210.[BATCH_NO]) = 17 THEN 'JB'
                                WHEN P210.[BATCH_NO] like '%SR%' THEN 'SR'
                                ELSE 'SH' END AS BATCH_Sort
                          ,'' AS RM_Kind
                          ,'' AS RMN
                          ,CASE WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'R' THEN '18'
                                WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'S' THEN '19'
                                WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'T' THEN '20'
                                WHEN len(P210.[BATCH_NO]) = 17 AND SUBSTRING(P210.[BATCH_NO],10,1) = 'W' THEN '21' 
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'R' THEN '18' 
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'S' THEN '19' 
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'T' THEN '20'
                                WHEN SUBSTRING(P210.[BATCH_NO],12,1) = 'W' THEN '21'
                                ELSE '' END AS 號機
                          ,'' AS PD
                          ,SUBSTRING(P208.[RECIPE_NO],3,2) AS PN2
                          ,SUBSTRING(P208.[RECIPE_NO],3,4) AS PN4
                          ,'' AS COST
                          ,P210.[ITEM_NO] AS '料號'
                          ,P210.[TRANSACTION_DATE] AS '異動日期'
                          ,P210.[TRANSACTION_QUANTITY] * -1 AS '主要數量'
                          ,P210.[TRANSACTION_UOM] AS '主要單位'
                          ,P210.[BATCH_NO] AS '工單'
                          --,P210.[SUBINVENTORY_CODE]
                          --,P210.[LOCATOR]
                          --,[SECONDARY_TRANSACTION_QUANTITY]
                          --,[SECONDARY_UOM_CODE]
                          --,[LOT_NUMBER]
                          --,P210.[STATUS]
                          ,CASE WHEN len(P210.[BATCH_NO]) = 17 THEN CAST(RIGHT(P208.[ITEM_NO],5) AS float) / 10.0
                                ELSE CAST(LEFT(RIGHT(P208.[ITEM_NO],6),5) AS float) / 10.0 END AS BW
                      FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P210_IN_MMT_INGR_ST] P210
                      LEFT JOIN (
                        SELECT distinct [BATCH_NO],[ITEM_NO],[RECIPE_NO] FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST]
                        WHERE [XXIF_CHP_P208_IN_CRE_BATCH_ST].[STATUS_CODE] = 'S'
                      ) P208 ON P208.BATCH_NO = P210.BATCH_NO
                      where 1=1
                      --AND P210.[ITEM_NO] ='903412200046'
                      AND P210.[TRANSACTION_DATE]>='"""+ str(stime_d) +""" 08:00:00' AND P210.TRANSACTION_DATE<'"""+ str(etime_d) +""" 08:00:00'
                      AND P210.[STATUS_CODE] = 'S'
                      AND P210.[SUBINVENTORY_CODE] = 'RM'
                      order by TRANSACTION_DATE
                    """       
                    query = conn.execute(text(sql))
                    df_reel_material = pd.DataFrame([dict(i) for i in query])  

                    df_reel_material = df_reel_material.sort_values(by=['異動日期','KG']).reset_index(drop=True)

                    # 條件一：號機為 '21' 且 BATCH_NO 結尾為 '199'
                    condition_21 = (df_reel_material['號機'] == '21') & (df_reel_material['工單'].astype(str).str.endswith('199'))

                    # 條件二：號機為 '19' 且 BATCH_NO 結尾為 '199'
                    condition_19 = (df_reel_material['號機'] == '19') & (df_reel_material['工單'].astype(str).str.endswith('199'))

                    # 設定 PN4
                    df_reel_material['PN4'] = np.where(condition_21, '2000',
                                               np.where(condition_19, '1000', df_reel_material['PN4']))

                    # 設定 PN2
                    df_reel_material['PN2'] = np.where(condition_21, '20',
                                               np.where(condition_19, '10', df_reel_material['PN2']))

                    df_reel_material['BW'] = np.where(condition_21, 0,
                                               np.where(condition_19, 0, df_reel_material['BW']))

                    df_reel_material['PN2'] = np.where(df_reel_material['PN4'].astype(str).str.startswith('MM'), 'QE', df_reel_material['PN2'])
                    df_reel_material['PN2'] = np.where(df_reel_material['PN4'].astype(str).str.endswith('NCR'), 'QC', df_reel_material['PN2'])

                    def RM_Kind_mapping(k_value):
                        if k_value.startswith('2') or k_value.startswith('3') or k_value.startswith('90'):
                            mid_result = '纖維'
                        else:
                            # 從 RMP 表找對應
                            mid_result = df_RMData.loc[df_RMData['料號'] == k_value, '類別']
                            mid_result = mid_result.iloc[0] if not mid_result.empty else None  

                        if mid_result == '化工':
                            mid_result = 'CH'
                        elif mid_result == '塗料':
                            mid_result = 'CT'
                        elif mid_result == '填料':
                            mid_result = 'CY'
                        elif mid_result == '纖維':
                            mid_result = 'FB'

                        return mid_result

                    df_reel_material['RM_Kind'] = df_reel_material['料號'].apply(RM_Kind_mapping)

                    df_reel_material = df_reel_material.merge(df_RMData.loc[:,['料號','中文名稱','COST_2','塗料淨量率']],on='料號',how='left')
                    df_reel_material['RMN'] = df_reel_material['中文名稱'].copy()
                    df_reel_material['COST'] = df_reel_material['COST_2'].copy()
                    df_reel_material['COST'] = df_reel_material['COST'] * df_reel_material['主要數量'] * (-1.0)

                    df_reel_material = df_reel_material.merge(df_ptype_category.loc[:,['兩碼紙別','類別']].rename(columns={'兩碼紙別':'PN2','類別':'分類別'}),
                                                              on='PN2',how='left')

                    df_reel_material['PD'] = np.where(
                            df_reel_material['PN2'].isin(['K8','HI','HK','HL','HP','HQ','HR','HS','HU','HV','UQ','UR','US']),
                            '78',
                            np.where(
                                df_reel_material['PN2'].isin(['TD','TF','TR','TS','A017','A020']),
                                '95',
                                df_reel_material['號機']
                            )
                        )

                    mapping = {'CT': '塗料','CH': '化工','FB': '纖維','CY': '填料'}

                    df_reel_material['類別'] = df_reel_material['RM_Kind'].map(mapping)

                    df_reel_material['Nqty'] = np.where(
                        df_reel_material['RM_Kind'] == 'CT',
                        df_reel_material['KG'] * df_reel_material['塗料淨量率'] / 100.0,
                        df_reel_material['KG']
                    )

                    df_reel_material = df_reel_material.loc[:,['分類別', 'KG', 'BATCH_Sort', 'RM_Kind', 'RMN', '號機', 'PD', 'PN2', 'PN4', 'COST',
                           '料號', '異動日期', '主要數量', '主要單位', '工單', 'Nqty', 'BW', '類別']]        

                    # 創建日結_表格
                    df_material = df_reel_material.groupby(['PD','PN4','BW','類別'])['KG','Nqty'].sum().reset_index().pivot_table(
                        index=['PD', 'PN4', 'BW'],
                        columns='類別',
                        values=['Nqty', 'KG'],
                        aggfunc='sum',
                        fill_value=0
                    ).reset_index()

                    df_material.columns = [f'{val}_{col}' for val, col in df_material.columns]
                    df_material = df_material.reset_index(drop=True)
                    df_material = df_material.loc[:,['PD_', 'PN4_', 'BW_','Nqty_纖維','Nqty_塗料','Nqty_填料','Nqty_化工',
                                               'KG_纖維', 'KG_塗料','KG_填料','KG_化工']]

                    df_material.columns = ['PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', '纖維.1','塗料.1', '填料.1', '化工.1',]

                    mapping = {'18': 'PM18','19': 'PM19','20': 'PM20','21': 'PM21','78': 'NCR','95': '含浸'}

                    df_material['機台'] = df_material['PD'].map(mapping)

                    df_material['紙別成品基重'] = df_material['機台'] + df_material['PN4'] + df_material['BW'].astype(str)
                    df_material['紙別成品基重'] = df_material['紙別成品基重'].str.replace(r'\.0$', '', regex=True)

                    df_material = df_material.loc[:,['機台', '紙別成品基重', 'PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', 
                                                     '纖維.1','塗料.1', '填料.1', '化工.1']]        

                    # 計算初出紙用漿量
                    df_reel_material_first = df_reel_material[(df_reel_material['PN4'].isin(['1000','2000'])) &                                      (df_reel_material['RM_Kind'].isin(['FB']))]                                    .groupby(['號機','PN2','RM_Kind','料號','RMN'])['KG','Nqty','COST'].sum().reset_index()
                    df_reel_material_first['機台'] = 'PM' + df_reel_material_first['號機']        

                    # 讀取計算約當量(分攤前)
                    df_Equivalent_Output_Before_Apportionment['PN2'] = df_Equivalent_Output_Before_Apportionment['PN4'].apply(classify_pn4)
                    df_Equivalent_Output_Before_Apportionment['類別'] = df_Equivalent_Output_Before_Apportionment['PN2'].map(df_ptype_category.set_index('兩碼紙別')['類別'])

                    df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['機台'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['PN4'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['基重'].astype(str)

                    df_Equivalent_Output_Before_Apportionment['塗前期初在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗後期初在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗前期末在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                       df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗後期末在產品(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                       df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['入庫量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_Inventory[df_Inventory['年月'] == etime].reset_index(drop=True).set_index('紙別基重')['合計(kg)']/1000.0
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment.loc[
                        df_Equivalent_Output_Before_Apportionment['PN2'].isin(['QE', 'QC']),
                        ['塗前期初在產品(噸)', '塗後期初在產品(噸)','塗前期末在產品(噸)','塗後期末在產品(噸)']
                    ] = None

                    df_Equivalent_Output_Before_Apportionment['塗前約當量(噸)'] = (df_Equivalent_Output_Before_Apportionment['塗前期末在產品(噸)'] -                                                                    df_Equivalent_Output_Before_Apportionment['塗前期初在產品(噸)']).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗後約當量(噸)'] = (df_Equivalent_Output_Before_Apportionment['入庫量(噸)'] +                                                                    df_Equivalent_Output_Before_Apportionment['塗後期末在產品(噸)'].fillna(0) -                                                                    df_Equivalent_Output_Before_Apportionment['塗後期初在產品(噸)'].fillna(0)).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['塗前塗佈克數(g)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_coatingweight.drop_duplicates(subset='紙別原紙基重').reset_index(drop=True).set_index('紙別原紙基重')['機上\n塗佈(g)'].rename_axis('紙別成品基重')
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment.loc[df_Equivalent_Output_Before_Apportionment['塗前約當量(噸)']==0,'塗前塗佈克數(g)'] = 0

                    df_Equivalent_Output_Before_Apportionment['塗後塗佈克數(g)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_coatingweight.drop_duplicates(subset='紙別成品基重').reset_index(drop=True).set_index('紙別成品基重')['塗佈合計(g)']
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['理論塗佈產量(噸)'] = df_Equivalent_Output_Before_Apportionment.apply(
                        lambda row: (
                            (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                            (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                        ) if row['基重'] not in [0, None, np.nan] else 0,
                        axis=1
                    )

                    df_Equivalent_Output_Before_Apportionment['理論填料產量(噸)'] = df_Equivalent_Output_Before_Apportionment.apply(
                        lambda row: (
                            (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                            (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                        ) if row['基重'] not in [0, None, np.nan] else 0,
                        axis=1
                    )

                    df_Equivalent_Output_Before_Apportionment['理論填料產量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['填料']*0.75/1000
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['理論纖維產量(噸)'] = df_Equivalent_Output_Before_Apportionment['塗前約當量(噸)'] +                                                                    df_Equivalent_Output_Before_Apportionment['塗後約當量(噸)'] -                                                                    df_Equivalent_Output_Before_Apportionment['理論塗佈產量(噸)'] -                                                                    df_Equivalent_Output_Before_Apportionment['理論填料產量(噸)']

                    df_Equivalent_Output_Before_Apportionment['塗料領用量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['塗料']/1000
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['填料領用量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['填料']/1000
                    ).fillna(0)

                    df_Equivalent_Output_Before_Apportionment['纖維領用量(噸)'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].map(
                        df_material.set_index('紙別成品基重')['纖維']/1000
                    ).fillna(0)  

                    # 讀取損紙攤提比重
                    df_Broken_paper_amortization_ratio_table = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\紙機損紙_初出紙用漿.xlsx',
                                              sheet_name='損紙攤提比重',skiprows=0)
                    df_Broken_paper_amortization_ratio_table = df_Broken_paper_amortization_ratio_table.iloc[:,1:4]

                    # 開始計算攤提
                    df_Broken_paper_amortization_ratio = df_Equivalent_Output_Before_Apportionment                                                        [~df_Equivalent_Output_Before_Apportionment['機台'].isin(['NCR','含浸'])]
                    df_Broken_paper_amortization_ratio =                             df_Broken_paper_amortization_ratio.merge(df_Broken_paper_amortization_ratio_table,on=['機台','PN2'],how='left')                            .loc[:,['機台','PN4','基重','損紙攤提比重','塗前約當量(噸)','塗後約當量(噸)','纖維領用量(噸)']]

                    df_Broken_paper_amortization_ratio['攤提基準(纖維用量)'] = df_Broken_paper_amortization_ratio['損紙攤提比重'] *                                                                               df_Broken_paper_amortization_ratio['纖維領用量(噸)']

                    df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)'] = np.where(
                        df_Broken_paper_amortization_ratio['攤提基準(纖維用量)']<0,
                        0,
                        df_Broken_paper_amortization_ratio['攤提基準(纖維用量)']
                    )

                    df_Broken_paper_amortization_ratio_sum = df_Broken_paper_amortization_ratio.groupby(['機台'])['攤提基準(約當量)(排除負纖維產量)'].sum().reset_index()
                    df_Broken_paper_amortization_ratio_sum.columns = ['機台','攤提基準(約當量)(排除負纖維產量)加總']

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_Broken_paper_amortization_ratio_sum,on='機台')

                    df_Broken_paper_amortization_ratio['佔比(纖維產量)'] = np.where(
                        df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)加總']==0,
                        0,
                        df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)'] / df_Broken_paper_amortization_ratio['攤提基準(約當量)(排除負纖維產量)加總']
                    )

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio[df_Broken_paper_amortization_ratio['佔比(纖維產量)']>0].reset_index(drop=True)


                    df_reel_material_first_pivot = df_reel_material_first.loc[:,['機台','料號','KG']].pivot_table(
                        index=['機台'],
                        columns='料號',
                        values=['KG'],
                        aggfunc='sum',
                        fill_value=0
                    ).reset_index()

                    df_reel_material_first_pivot.columns = [f'{val}_{col}' for val, col in df_reel_material_first_pivot.columns]

                    df_reel_material_first_pivot.rename(columns={'機台_':'機台'},inplace=True)
                    df_reel_material_first_pivot.columns = df_reel_material_first_pivot.columns.str.replace('^KG_', '', regex=True)

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_reel_material_first_pivot,on='機台',how='left')

                    for col in df_reel_material_first_pivot.columns[1:]:
                        df_Broken_paper_amortization_ratio[col] = df_Broken_paper_amortization_ratio[col] *                                                                  df_Broken_paper_amortization_ratio['佔比(纖維產量)'] * -1

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.groupby(['機台','PN4','基重'])[list(df_reel_material_first_pivot.columns[1:])].sum().reset_index()

                    df_Broken_paper_amortization_ratio[[col for col in df_reel_material_first_pivot.columns if col.endswith('P')]] =                     df_Broken_paper_amortization_ratio[[col for col in df_reel_material_first_pivot.columns if col.endswith('P')]] / 1000.0

                    df_Broken_paper_amortization_ratio = pd.melt(df_Broken_paper_amortization_ratio,
                            id_vars=['機台','PN4','基重'],
                            var_name = '料號',
                            value_name = '主要數量'
                    )

                    df_Broken_paper_amortization_ratio['號機'] = df_Broken_paper_amortization_ratio['機台'].str[2:]
                    df_Broken_paper_amortization_ratio['PN2'] = df_Broken_paper_amortization_ratio['PN4'].str[:2]
                    df_Broken_paper_amortization_ratio.rename(columns={'基重':'BW'},inplace=True)
                    df_Broken_paper_amortization_ratio['RM_Kind'] = df_Broken_paper_amortization_ratio['料號'].apply(RM_Kind_mapping)
                    df_Broken_paper_amortization_ratio['主要單位'] = np.where(
                        df_Broken_paper_amortization_ratio['料號'].str.endswith('P'),
                        'ADT',
                        'KG'
                    )
                    df_Broken_paper_amortization_ratio['BATCH_Sort'] = 'JB'

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_RMData.loc[:,['料號','中文名稱','COST_2','塗料淨量率']],on='料號',how='left')
                    df_Broken_paper_amortization_ratio['RMN'] = df_Broken_paper_amortization_ratio['中文名稱'].copy()
                    df_Broken_paper_amortization_ratio['COST'] = df_Broken_paper_amortization_ratio['COST_2'].copy()
                    df_Broken_paper_amortization_ratio['COST'] = df_Broken_paper_amortization_ratio['COST'] * df_Broken_paper_amortization_ratio['主要數量'] * (-1.0)

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.merge(df_ptype_category.loc[:,['兩碼紙別','類別']].rename(columns={'兩碼紙別':'PN2','類別':'分類別'}),
                                                              on='PN2',how='left')

                    df_Broken_paper_amortization_ratio['PD'] = df_Broken_paper_amortization_ratio['號機']

                    mapping = {'CT': '塗料','CH': '化工','FB': '纖維','CY': '填料'}

                    df_Broken_paper_amortization_ratio['類別'] = df_Broken_paper_amortization_ratio['RM_Kind'].map(mapping)

                    df_Broken_paper_amortization_ratio['KG'] = np.where(
                        df_Broken_paper_amortization_ratio['主要單位'] == 'KG',
                        df_Broken_paper_amortization_ratio['主要數量'] * (-1),
                        df_Broken_paper_amortization_ratio['主要數量'] * (-1) * 1000
                    )

                    df_Broken_paper_amortization_ratio['Nqty'] = np.where(
                        df_Broken_paper_amortization_ratio['RM_Kind'] == 'CT',
                        df_Broken_paper_amortization_ratio['KG'] * df_Broken_paper_amortization_ratio['塗料淨量率'] / 100.0,
                        df_Broken_paper_amortization_ratio['KG']
                    )

                    df_Broken_paper_amortization_ratio['異動日期'] = np.nan
                    df_Broken_paper_amortization_ratio['工單'] = np.nan

                    df_Broken_paper_amortization_ratio = df_Broken_paper_amortization_ratio.loc[:,['分類別', 'KG', 'BATCH_Sort', 'RM_Kind', 'RMN', '號機', 'PD', 'PN2', 'PN4', 'COST',
                           '料號', '異動日期', '主要數量', '主要單位', '工單', 'Nqty', 'BW', '類別']]        

                    # 更新 原物料 用量 Data_
                    df_reel_material = pd.concat([df_reel_material,df_Broken_paper_amortization_ratio],ignore_index=True)     

                    return df_reel_material                   
                

            # 讀取期末在產品
            
            start_time = time.time() 

            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                   
                    sql =   """
                        SELECT * FROM [CostSheet].[dbo].[End_work_in_process] WHERE [年月] = '"""+ str(etime) +"""'
                    """       
                    query = conn.execute(text(sql))  
                    df_End_work_in_process_current_period = pd.DataFrame([dict(i) for i in query])
                if df_End_work_in_process_current_period.empty:
                    df_End_work_in_process_current_period = search_InProcess_MES(etime)
                    df_End_work_in_process_current_period = Work_In_Process(df_End_work_in_process_current_period)
            except:
                df_End_work_in_process_current_period = search_InProcess_MES(etime)
                df_End_work_in_process_current_period = Work_In_Process(df_End_work_in_process_current_period)

            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                  
                    sql =   """
                        SELECT * FROM [CostSheet].[dbo].[End_work_in_process] WHERE [年月] = '"""+ str(stime) +"""'
                    """       
                    query = conn.execute(text(sql))  
                    df_End_work_in_process_Last_period = pd.DataFrame([dict(i) for i in query])
                if df_End_work_in_process_Last_period.empty:
                    df_End_work_in_process_Last_period = search_InProcess_MES(stime)
                    df_End_work_in_process_Last_period = Work_In_Process(df_End_work_in_process_Last_period)
            except:
                df_End_work_in_process_Last_period = search_InProcess_MES(stime)
                df_End_work_in_process_Last_period = Work_In_Process(df_End_work_in_process_Last_period)   
        
            elapsed = time.time() - start_time
            logging.info(f"Work_In_Process time is: {elapsed:.2f} seconds")  

            # 讀取紙別分類
            start_time = time.time()
        
            try:
                df_ptype_category = pd.read_excel(r'E:\AP\Api\dist\計算約當量_2025_分類別.xlsx',
                                          sheet_name='紙別分類',skiprows=0)                
            except:
                df_ptype_category = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
                                          sheet_name='紙別分類',skiprows=0)

            df_ptype_category = df_ptype_category.iloc[1:115,[14,15,16,18]].reset_index(drop=True)
            df_ptype_category.iloc[0,3] = '類別'            
            df_ptype_category.columns = df_ptype_category.iloc[0]
            df_ptype_category = df_ptype_category[1:].reset_index(drop=True)

            # 讀取入庫量
            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                  
                    sql =   """
                        SELECT * FROM [CostSheet].[dbo].[ERP_Inventory] WHERE [年月] = '"""+ str(etime) +"""'
                    """       
                    query = conn.execute(text(sql))  
                    df_Inventory = pd.DataFrame([dict(i) for i in query])
                if df_Inventory.empty:
                    df_Inventory = search_Inventory_MES(etime)
            except:
                df_Inventory = search_Inventory_MES(etime)
                
            elapsed = time.time() - start_time
            logging.info(f"Inventory time is: {elapsed:.2f} seconds")
            
            start_time = time.time()
            # 讀取塗佈克數
            # 讀取塗佈克數
            try:
                df_coatingweight = pd.read_excel(r'E:\AP\Api\dist\計算約當量_2025_分類別.xlsx',
                                          sheet_name='塗佈克數_data',skiprows=0)                
            except:            
                df_coatingweight = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
                                          sheet_name='塗佈克數_data',skiprows=0)
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_1 time is: {elapsed:.2f} seconds")             
            
            # 讀取範例schema檔案
            start_time = time.time()
            try:
                df_mname_ptype_gramg_schema = pd.read_excel(r'E:\AP\Api\dist\計算約當量_2025_分類別.xlsx',
                                      sheet_name='計算約當量_202504',skiprows=0)                
            except:                 
                df_mname_ptype_gramg_schema = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\計算約當量_2025_分類別.xlsx',
                                      sheet_name='計算約當量_202504',skiprows=0)
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_2 time is: {elapsed:.2f} seconds")
            
            start_time = time.time()

            dt = datetime.datetime.strptime(etime, "%Y%m")
            etime_t = (dt + relativedelta(months=1) - timedelta(days=1))

            df_mname_ptype_gramg_schema = df_mname_ptype_gramg_schema.loc[:df_mname_ptype_gramg_schema[df_mname_ptype_gramg_schema['類別'].isna()].head(1).index[0]-1,:]            
            df_mname_ptype_gramg_schema['年'] = etime_t.year
            df_mname_ptype_gramg_schema['月'] = etime_t.month
            df_mname_ptype_gramg_schema['日'] = etime_t.day
            df_mname_ptype_gramg_schema = df_mname_ptype_gramg_schema.loc[:,['年', '月', '日', '機台', 'PN4', '基重']]
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_3 time is: {elapsed:.2f} seconds")
            
            start_time = time.time()

            # 找出不在舊資料的四碼紙別基重
            df_mname_ptype_gramg_schema_new = pd.concat([
                df_End_work_in_process_Last_period.loc[:,['號機','紙別', '基重(成品)']],
                df_End_work_in_process_current_period.loc[:,['號機','紙別', '基重(成品)']],
                df_Inventory.rename(columns={'PN4':'紙別','基重':'基重(成品)','機台':'號機'}).loc[:,['號機','紙別', '基重(成品)']]
            ],ignore_index=True
            ).drop_duplicates()

            df_mname_ptype_gramg_schema_new = df_mname_ptype_gramg_schema_new.merge(df_mname_ptype_gramg_schema,left_on=['號機','紙別', '基重(成品)'],
                                                  right_on=['機台','PN4', '基重'],how='left')
            df_mname_ptype_gramg_schema_new = df_mname_ptype_gramg_schema_new[df_mname_ptype_gramg_schema_new['年'].isna()].reset_index(drop=True)
            df_mname_ptype_gramg_schema_new = df_mname_ptype_gramg_schema_new.loc[:,['號機','紙別', '基重(成品)']]
            df_mname_ptype_gramg_schema_new['年'] = etime_t.year
            df_mname_ptype_gramg_schema_new['月'] = etime_t.month
            df_mname_ptype_gramg_schema_new['日'] = etime_t.day
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_4 time is: {elapsed:.2f} seconds")
            
            start_time = time.time()
            
            def convert_weight(x):
                try:
                    x_float = float(x)
                    if x_float.is_integer():
                        return int(x_float)  # 轉成 int
                    else:
                        return round(x_float, 1)  # 精確到小數一位
                except Exception as e:
                    return x  # 如果轉換失敗就原值保留

            converted = [convert_weight(x) for x in df_mname_ptype_gramg_schema_new['基重(成品)']]
            df_mname_ptype_gramg_schema_new['基重(成品)'] = pd.Series(converted, dtype='object')            

            df_Equivalent_Output_Before_Apportionment = pd.concat([df_mname_ptype_gramg_schema,
                       df_mname_ptype_gramg_schema_new.rename(columns={'紙別':'PN4','基重(成品)':'基重','號機':'機台'})],ignore_index=True).drop_duplicates().reset_index(drop=True)               

            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_5 time is: {elapsed:.2f} seconds") 
            
            start_time = time.time()             
            
            try:
                srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
                with srv_SRVMESDBA1['create_engine'][0].connect() as conn:                
                    sql =   """
                        SELECT [分類別],[KG],[BATCH_Sort],[RM_Kind],[RMN],[號機],[PD],[PN2],[PN4],[COST],[料號],
                                [異動日期],[主要數量],[主要單位],[工單],[Nqty],[BW],[類別]
                          FROM [CostSheet].[dbo].[ERP_Inventory_Material]
                          WHERE [年月] = '"""+ str(etime) +"""'
                    """       
                    query = conn.execute(text(sql))
                    df_reel_material = pd.DataFrame([dict(i) for i in query])

                    df_Equivalent_Output_Before_Apportionment['PN2'] = df_Equivalent_Output_Before_Apportionment['PN4'].apply(classify_pn4)
                    df_Equivalent_Output_Before_Apportionment['類別'] = df_Equivalent_Output_Before_Apportionment['PN2'].map(df_ptype_category.set_index('兩碼紙別')['類別'])        

                    df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['機台'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['PN4'].astype(str) +                                                                   df_Equivalent_Output_Before_Apportionment['基重'].astype(str)        
                if df_reel_material.empty:
                    df_reel_material = material_data(etime,df_Equivalent_Output_Before_Apportionment)
            except:
                df_reel_material = material_data(etime,df_Equivalent_Output_Before_Apportionment)
                
            
            elapsed = time.time() - start_time
            logging.info(f"df_Equivalent_Output_Before_Apportionment_1 time is: {elapsed:.2f} seconds") 

            # 讀取原物料日結
            # 讀取原物料日結
            df_material = df_reel_material.groupby(['PD','PN4','BW','類別'])['KG','Nqty'].sum().reset_index().pivot_table(
                index=['PD', 'PN4', 'BW'],
                columns='類別',
                values=['Nqty', 'KG'],
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            df_material.columns = [f'{val}_{col}' for val, col in df_material.columns]
            df_material = df_material.reset_index(drop=True)
            df_material = df_material.loc[:,['PD_', 'PN4_', 'BW_','Nqty_纖維','Nqty_塗料','Nqty_填料','Nqty_化工',
                                       'KG_纖維', 'KG_塗料','KG_填料','KG_化工']]

            df_material.columns = ['PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', '纖維.1','塗料.1', '填料.1', '化工.1',]

            mapping = {'18': 'PM18','19': 'PM19','20': 'PM20','21': 'PM21','78': 'NCR','95': '含浸'}

            df_material['機台'] = df_material['PD'].map(mapping)

            df_material['紙別成品基重'] = df_material['機台'] + df_material['PN4'] + df_material['BW'].astype(str)
            df_material['紙別成品基重'] = df_material['紙別成品基重'].str.replace(r'\.0$', '', regex=True)

            df_material = df_material.loc[:,['機台', '紙別成品基重', 'PD', 'PN4', 'BW', '纖維', '塗料', '填料', '化工', 
                                             '纖維.1','塗料.1', '填料.1', '化工.1']]
            
            elapsed = time.time() - start_time
            logging.info(f"df_material time is: {elapsed:.2f} seconds")            

            # 讀取原物料 原紙耗用
            # 讀取原物料 原紙耗用
            start_time = time.time() 
            
            stime_d = (datetime.datetime.strptime(etime, "%Y%m")).strftime('%Y-%m-%d')
            etime_d = (datetime.datetime.strptime(etime, "%Y%m") + relativedelta(months=1)  - timedelta(days=1)).strftime('%Y-%m-%d')
            
            srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
            with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:                            
                sql =   """
                ;With raw_data as
                (
                    SELECT *
                    FROM
                    (
                    SELECT [RXID]
                            ,[PREVIOUS_RXID]
                            ,[BATCH_NO]
                            ,[ITEM_NO]
                        ,SUBSTRING([ITEM_NO],2,4) as ptype
                        ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                        ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                        ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                            ,[SUBINVENTORY_CODE]
                            ,[LOCATOR]
                            ,[TRANSACTION_QUANTITY]
                            ,[TRANSACTION_UOM]
                            ,[SECONDARY_TRANSACTION_QUANTITY]
                            ,[SECONDARY_UOM_CODE]
                            ,[TRANSACTION_DATE]
                            ,[STATUS]
                        FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P210_IN_MMT_INGR_ST]
                        WHERE 1=1
                        AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime_d) +"""' and '"""+ str(etime_d) +"""'
                        AND [STATUS_CODE] = 'S'
                    ) s
                    WHERE 1=1
                    AND (ptype like '%NCR' or ptype like 'MM%') AND length  = 'R'
                )
                SELECT PN4,BW,[原紙紙別],SUM([紙用量(kg)]) AS 合計 FROM
                (
                    SELECT t.BATCH_NO,SUBSTRING(MAX(P250.[ITEM_NO]),2,4) as PN4,CAST(SUBSTRING(MAX(P250.[ITEM_NO]),7,5) AS INT) / 10.0 as BW,
                    MAX(t.ptype) 原紙紙別, MAX(t.gramg) / 10.0 原紙基重, MAX(t.[TRANSACTION_QUANTITY]) AS [紙用量(kg)]
                    FROM
                    (
                        SELECT BATCH_NO,ptype,gramg,sum([TRANSACTION_QUANTITY]) AS [TRANSACTION_QUANTITY]
                        FROM
                        (
                            SELECT * FROM raw_data
                            WHERE RXID NOT IN (SELECT DISTINCT PREVIOUS_RXID FROM raw_data WHERE PREVIOUS_RXID is not null)
                        ) s
                        WHERE 1=1
                        GROUP BY BATCH_NO,ptype,gramg
                    ) t
                    LEFT JOIN [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST] P250 ON t.BATCH_NO = P250.BATCH_NO 
                    GROUP BY t.BATCH_NO
                ) n
                WHERE PN4 IS NOT NULL AND BW IS NOT NULL
                GROUP BY PN4,BW,[原紙紙別]
                """       
                query = conn.execute(text(sql))
                df_reel_consume = pd.DataFrame([dict(i) for i in query])

            df_reel_consume['BW'] = df_reel_consume['BW'].astype(int)

            df_reel_consume['紙別成品基重'] = np.where(
                df_reel_consume['原紙紙別'].str.startswith('MM'),
                '含浸' + df_reel_consume['PN4']+ df_reel_consume['BW'].astype(str),
                np.where(
                    df_reel_consume['原紙紙別'].str.endswith('NCR'),
                    'NCR' + df_reel_consume['PN4']+ df_reel_consume['BW'].astype(str),
                    ''
                )
            )
            
            df_reel_consume = df_reel_consume.drop_duplicates(
                subset='紙別成品基重', keep='first'
            ).reset_index(drop=True)
            
            elapsed = time.time() - start_time
            logging.info(f"df_reel_consume time is: {elapsed:.2f} seconds") 
            
            
            start_time = time.time()
            
            # 讀取計算約當量
            # 讀取計算約當量
            df_Equivalent_Output_Before_Apportionment['紙別成品基重'] = df_Equivalent_Output_Before_Apportionment['紙別成品基重'].astype(str).str.replace(r'\.0$', '', regex=True)
            
            df_Equivalent_Output_current_period = df_Equivalent_Output_Before_Apportionment.loc[:,['年', '月', '日', '機台', 'PN4', '基重','PN2','類別','紙別成品基重']]

            df_Equivalent_Output_current_period['塗前期初在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
            ).fillna(0)

            df_Equivalent_Output_current_period['塗後期初在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_End_work_in_process_Last_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
            ).fillna(0)

            df_Equivalent_Output_current_period['塗前期末在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
               df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗前']
            ).fillna(0)

            df_Equivalent_Output_current_period['塗後期末在產品(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
               df_End_work_in_process_current_period.loc[:,['紙別基重(塗前)','塗前','塗後']].set_index('紙別基重(塗前)')['塗後']
            ).fillna(0)

            df_Equivalent_Output_current_period['入庫量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_Inventory[df_Inventory['年月'] == etime].reset_index(drop=True).set_index('紙別基重')['合計(kg)']/1000.0
            ).fillna(0)

            df_Equivalent_Output_current_period.loc[
                df_Equivalent_Output_current_period['PN2'].isin(['QE', 'QC']),
                ['塗前期初在產品(噸)', '塗後期初在產品(噸)','塗前期末在產品(噸)','塗後期末在產品(噸)']
            ] = None

            df_Equivalent_Output_current_period['塗前約當量(噸)'] = (df_Equivalent_Output_current_period['塗前期末在產品(噸)'] -                                                            df_Equivalent_Output_current_period['塗前期初在產品(噸)']).fillna(0)

            df_Equivalent_Output_current_period['塗後約當量(噸)'] = (df_Equivalent_Output_current_period['入庫量(噸)'] +                                                            df_Equivalent_Output_current_period['塗後期末在產品(噸)'].fillna(0) -                                                            df_Equivalent_Output_current_period['塗後期初在產品(噸)'].fillna(0)).fillna(0)

            df_Equivalent_Output_current_period['塗前塗佈克數(g)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_coatingweight.drop_duplicates(subset='紙別原紙基重').reset_index(drop=True).set_index('紙別原紙基重')['機上\n塗佈(g)'].rename_axis('紙別成品基重')
            ).fillna(0)

            df_Equivalent_Output_current_period.loc[df_Equivalent_Output_current_period['塗前約當量(噸)']==0,'塗前塗佈克數(g)'] = 0

            df_Equivalent_Output_current_period['塗後塗佈克數(g)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_coatingweight.drop_duplicates(subset='紙別成品基重').reset_index(drop=True).set_index('紙別成品基重')['塗佈合計(g)']
            ).fillna(0)

            df_Equivalent_Output_current_period['理論塗佈產量(噸)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                    (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                ) if row['基重'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_Equivalent_Output_current_period['理論填料產量(噸)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['塗前塗佈克數(g)'] / row['基重'] * row['塗前約當量(噸)']) +
                    (row['塗後塗佈克數(g)'] / row['基重'] * row['塗後約當量(噸)'])
                ) if row['基重'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_Equivalent_Output_current_period['理論填料產量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['填料']*0.75/1000
            ).fillna(0)

            df_Equivalent_Output_current_period['理論纖維產量(噸)'] = df_Equivalent_Output_current_period['塗前約當量(噸)'] +                                                            df_Equivalent_Output_current_period['塗後約當量(噸)'] -                                                            df_Equivalent_Output_current_period['理論塗佈產量(噸)'] -                                                            df_Equivalent_Output_current_period['理論填料產量(噸)']

            df_Equivalent_Output_current_period['塗料領用量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['塗料']/1000
            ).fillna(0)

            df_Equivalent_Output_current_period['填料領用量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['填料']/1000
            ).fillna(0)

            df_Equivalent_Output_current_period['纖維領用量(噸)'] = df_Equivalent_Output_current_period['紙別成品基重'].map(
                df_material.set_index('紙別成品基重')['纖維']/1000
            ).fillna(0)

            df_Equivalent_Output_current_period.loc[df_Equivalent_Output_current_period['機台'].isin(['NCR','含浸']),'纖維領用量(噸)'] =                 df_Equivalent_Output_current_period.loc[df_Equivalent_Output_current_period['機台'].isin(['NCR','含浸']),'紙別成品基重'].map(
                    df_reel_consume.set_index('紙別成品基重')['合計']/1000
                ).fillna(0)


            df_Equivalent_Output_current_period['纖維得率(%)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_Equivalent_Output_current_period['塗料得率(%)'] = df_Equivalent_Output_current_period.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped = df_Equivalent_Output_current_period.groupby(['機台','PN2'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            # 對「機台」套用排序規則
            df_grouped['機台'] = pd.Categorical(df_grouped['機台'], categories=custom_order, ordered=True)

            # 再排序
            df_grouped = df_grouped.sort_values(['機台', 'PN2']).reset_index(drop=True)

            # df_grouped[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']] = df_grouped[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']].round(2)

            df_grouped = df_grouped.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped_2 = df_Equivalent_Output_current_period.groupby(['機台','類別'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            # 對「機台」套用排序規則
            df_grouped_2['機台'] = pd.Categorical(df_grouped_2['機台'], categories=custom_order, ordered=True)

            # 再排序
            df_grouped_2 = df_grouped_2.sort_values(['機台', '類別']).reset_index(drop=True)

#             df_grouped_2[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']] = df_grouped_2[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']].round(2)

            df_grouped_2 = df_grouped_2.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            df_grouped_2['纖維得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped_2['塗料得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped_2['填料得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論填料產量(噸)'] / row['填料領用量(噸)'])
                ) if row['填料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )


            df_grouped['纖維得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped['塗料得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped['填料得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論填料產量(噸)'] / row['填料領用量(噸)'])
                ) if row['填料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )
            
            elapsed = time.time() - start_time
            logging.info(f"df_grouped_2 time is: {elapsed:.2f} seconds")


            return df_grouped_2.copy()
        
        
        dt = datetime.datetime.strptime(stime, "%Y%m")

        stime_1 = (dt - relativedelta(months=1)).strftime("%Y%m")
        stime_2 = (dt - relativedelta(months=2)).strftime("%Y%m")

        etime_1 = stime
        etime_2 = stime_1  

        df_result = Product_Cost_Equivalent(stime,etime,mname,Product_Category,Product_two_ptype)
#         df_Product_cost_schedule_temp_2,cost_df_temp_2 = Product_Cost_Equivalent(stime_1,etime_1,mname,Product_Category,Product_two_ptype)
#         df_Product_cost_schedule_temp_3,cost_df_temp_3 = Product_Cost_Equivalent(stime_2,etime_2,mname,Product_Category,Product_two_ptype)            
            
            
        if not df_result.empty:
            
            for k in list(df_result.columns):
                df_result[k] = df_result[k].astype(str)           

            result_json = [{"mname": m,"category":c,"equivalent_before":eb,"equivalent_after":ea,"weight_fiber":wf,"weight_adcoat":wa,
                "weight_cy":wc,"use_fiber":uf,"use_adcoat":ua,"use_cy":uc,"yield_fiber":yf,"yield_adcoat":ya,"yield_cy": yc} 
                           for m,c,eb,ea,wf,wa,wc,uf,ua,uc,yf,ya,yc in zip(df_result["機台"], df_result["類別"],
                                  df_result["塗前約當量(噸)"],df_result["塗後約當量(噸)"], 
                                  df_result["理論纖維產量(噸)"], df_result["理論塗佈產量(噸)"],df_result["理論填料產量(噸)"],
                                  df_result["纖維領用量(噸)"],df_result["塗料領用量(噸)"],df_result["填料領用量(噸)"],
                                  df_result["纖維得率(%)"],df_result["塗料得率(%)"],df_result["填料得率(%)"],)]

        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json           


# In[ ]:


# monthly_equivalent_production


# In[ ]:


class monthly_equivalent_production:
    def __init__(self, servers):
        self.servers = servers    
    
    def fetch(self, year: str):
        startTime = time.time()
        
        if not year:
            return {'success': False, 'message': 'Missing year parameter'}        

        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:        
            sql =   """
                  SELECT *  FROM [CostSheet].[dbo].[Equivalent_production]
                  WHERE 年 = """ + str(year) + """
            """
            query = conn.execute(text(sql))  
            df_Equivalent_Output_current_period = pd.DataFrame([dict(i) for i in query]) 
            
        if not df_Equivalent_Output_current_period.empty:

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped = df_Equivalent_Output_current_period.groupby(['年','月','類別','機台','PN2'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            df_grouped['機台'] = pd.Categorical(df_grouped['機台'], categories=custom_order, ordered=True)
            df_grouped = df_grouped.sort_values(['機台', 'PN2']).reset_index(drop=True)
            df_grouped = df_grouped.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            df_grouped_2 = df_Equivalent_Output_current_period.groupby(['年','月','機台','類別'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            df_grouped_2['機台'] = pd.Categorical(df_grouped_2['機台'], categories=custom_order, ordered=True)
            df_grouped_2 = df_grouped_2.sort_values(['機台', '類別']).reset_index(drop=True)
            df_grouped_2 = df_grouped_2.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            df_grouped['年月'] = df_grouped['年'].astype(str).str.zfill(4) + df_grouped['月'].astype(str).str.zfill(2)
            df_grouped['約當量'] = df_grouped['塗前約當量(噸)'] + df_grouped['塗後約當量(噸)']

            df_grouped_result = (
                df_grouped
                .groupby(['機台','PN2','類別','年月'], observed=True)
                .agg(約當量=('約當量','sum'))
                .unstack('年月')            # 年月變成欄
            )

            # 補約當量的缺值
            if '約當量' in df_grouped_result.columns.get_level_values(0):
                df_grouped_result['約當量'] = df_grouped_result['約當量'].fillna(0)


            # 如果要讓欄位扁平化
            df_grouped_result.columns = [f"{col[1]}" for col in df_grouped_result.columns]
            df_grouped_result = df_grouped_result.reset_index()


            df_grouped_2['年月'] = df_grouped_2['年'].astype(str).str.zfill(4) + df_grouped_2['月'].astype(str).str.zfill(2)
            df_grouped_2['約當量'] = df_grouped_2['塗前約當量(噸)'] + df_grouped_2['塗後約當量(噸)']

            df_grouped_2_result = (
                df_grouped_2
                .groupby(['機台','類別','年月'], observed=True)
                .agg(約當量=('約當量','sum'))
                .unstack('年月')            # 年月變成欄
            )

            # 補約當量的缺值
            if '約當量' in df_grouped_2_result.columns.get_level_values(0):
                df_grouped_2_result['約當量'] = df_grouped_2_result['約當量'].fillna(0)


            # 如果要讓欄位扁平化
            df_grouped_2_result.columns = [f"{col[1]}" for col in df_grouped_2_result.columns]
            df_grouped_2_result = df_grouped_2_result.reset_index()               
            
            # 轉長表
            df_grouped_result_long = df_grouped_result.melt(
                id_vars=['機台', 'PN2', '類別'],
                var_name='yearmonth',
                value_name='value'
            ).to_dict(orient='records')

            df_grouped_2_result_long = df_grouped_2_result.melt(
                id_vars=['機台', '類別'],
                var_name='yearmonth',
                value_name='value'
            ).to_dict(orient='records')


            # 包成最終 JSON
            result_json = {
                "metadata": {
                    "name": "monthly_equivalent_production",
                    "source": "monthly_equivalent_production",
                    "description": "monthly_equivalent_production"
                },
                "data": {
                    "Content": {
                         "PN2":df_grouped_result_long,
                         "Category":df_grouped_2_result_long

                    }
                }
            }            
            
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


# monthly_ERP_inventory


# In[ ]:


class monthly_ERP_inventory:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, year: str):
        startTime = time.time()
        
        if not year:
            return {'success': False, 'message': 'Missing year parameter'}        

        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:   
            sql =   """
                  SELECT *  FROM [CostSheet].[dbo].[Equivalent_production]
                  WHERE 年 = """ + str(year) + """
            """
            query = conn.execute(text(sql))  
            df_Equivalent_Output_current_period = pd.DataFrame([dict(i) for i in query]) 
            
        if not df_Equivalent_Output_current_period.empty:

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped = df_Equivalent_Output_current_period.groupby(['年','月','類別','機台','PN2'])                .agg(a=('入庫量(噸)','sum')).reset_index()

            df_grouped['機台'] = pd.Categorical(df_grouped['機台'], categories=custom_order, ordered=True)
            df_grouped = df_grouped.sort_values(['機台', 'PN2']).reset_index(drop=True)
            df_grouped = df_grouped.rename(columns={'a': '入庫量(噸)'})

            df_grouped_2 = df_Equivalent_Output_current_period.groupby(['年','月','機台','類別'])                .agg(a=('入庫量(噸)','sum')).reset_index()

            df_grouped_2['機台'] = pd.Categorical(df_grouped_2['機台'], categories=custom_order, ordered=True)
            df_grouped_2 = df_grouped_2.sort_values(['機台', '類別']).reset_index(drop=True)
            df_grouped_2 = df_grouped_2.rename(columns={'a': '入庫量(噸)'})

            df_grouped['年月'] = df_grouped['年'].astype(str).str.zfill(4) + df_grouped['月'].astype(str).str.zfill(2)

            df_grouped_result = (
                df_grouped
                .groupby(['機台','PN2','類別','年月'], observed=True)
                .agg(入庫量=('入庫量(噸)','sum'))
                .unstack('年月')            # 年月變成欄
            )

            # 補約當量的缺值
            if '入庫量' in df_grouped_result.columns.get_level_values(0):
                df_grouped_result['入庫量'] = df_grouped_result['入庫量'].fillna(0)


            # 如果要讓欄位扁平化
            df_grouped_result.columns = [f"{col[1]}" for col in df_grouped_result.columns]
            df_grouped_result = df_grouped_result.reset_index()


            df_grouped_2['年月'] = df_grouped_2['年'].astype(str).str.zfill(4) + df_grouped_2['月'].astype(str).str.zfill(2)

            df_grouped_2_result = (
                df_grouped_2
                .groupby(['機台','類別','年月'], observed=True)
                .agg(入庫量=('入庫量(噸)','sum'))
                .unstack('年月')            # 年月變成欄
            )

            # 補約當量的缺值
            if '入庫量' in df_grouped_2_result.columns.get_level_values(0):
                df_grouped_2_result['入庫量'] = df_grouped_2_result['入庫量'].fillna(0)


            # 如果要讓欄位扁平化
            df_grouped_2_result.columns = [f"{col[1]}" for col in df_grouped_2_result.columns]
            df_grouped_2_result = df_grouped_2_result.reset_index()               
            
            # 轉長表
            df_grouped_result_long = df_grouped_result.melt(
                id_vars=['機台', 'PN2', '類別'],
                var_name='yearmonth',
                value_name='value'
            ).to_dict(orient='records')

            df_grouped_2_result_long = df_grouped_2_result.melt(
                id_vars=['機台', '類別'],
                var_name='yearmonth',
                value_name='value'
            ).to_dict(orient='records')


            # 包成最終 JSON
            result_json = {
                "metadata": {
                    "name": "monthly_ERP_inventory",
                    "source": "monthly_ERP_inventory",
                    "description": "monthly_ERP_inventory"
                },
                "data": {
                    "Content": {
                         "PN2":df_grouped_result_long,
                         "Category":df_grouped_2_result_long

                    }
                }
            }            
            
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


# monthly_yield_rate


# In[ ]:


class monthly_yield_rate:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, year: str):
        startTime = time.time()
        
        if not year:
            return {'success': False, 'message': 'Missing year parameter'}        

        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:   
            sql =   """
                  SELECT *  FROM [CostSheet].[dbo].[Equivalent_production]
                  WHERE 年 = """ + str(year) + """
            """
            query = conn.execute(text(sql))  
            df_Equivalent_Output_current_period = pd.DataFrame([dict(i) for i in query]) 
            
        if not df_Equivalent_Output_current_period.empty:

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped = df_Equivalent_Output_current_period.groupby(['年','月','類別','機台','PN2'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            # 對「機台」套用排序規則
            df_grouped['機台'] = pd.Categorical(df_grouped['機台'], categories=custom_order, ordered=True)

            # 再排序
            df_grouped = df_grouped.sort_values(['機台', 'PN2']).reset_index(drop=True)

            df_grouped = df_grouped.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            custom_order = ['PM18', 'PM19', 'PM20', 'PM21','NCR','含浸']  # 根據你要的順序設定

            df_grouped_2 = df_Equivalent_Output_current_period.groupby(['年','月','機台','類別'])                .agg(a=('塗前約當量(噸)','sum'), 
                     b=('塗後約當量(噸)','sum'),
                     c=('理論纖維產量(噸)','sum'), 
                     d=('理論塗佈產量(噸)','sum'),
                     e=('理論填料產量(噸)','sum'),
                     f=('纖維領用量(噸)','sum'),
                     g=('塗料領用量(噸)','sum'),
                     h=('填料領用量(噸)','sum'),
                    )\
                .reset_index()

            # 對「機台」套用排序規則
            df_grouped_2['機台'] = pd.Categorical(df_grouped_2['機台'], categories=custom_order, ordered=True)

            # 再排序
            df_grouped_2 = df_grouped_2.sort_values(['機台', '類別']).reset_index(drop=True)

            df_grouped_2 = df_grouped_2.rename(columns={
                'a': '塗前約當量(噸)',
                'b': '塗後約當量(噸)',
                'c': '理論纖維產量(噸)',
                'd': '理論塗佈產量(噸)',
                'e': '理論填料產量(噸)',
                'f': '纖維領用量(噸)',
                'g': '塗料領用量(噸)',
                'h': '填料領用量(噸)',
            })

            df_grouped_2['纖維得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped_2['塗料得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped_2['填料得率(%)'] = df_grouped_2.apply(
                lambda row: (
                    (row['理論填料產量(噸)'] / row['填料領用量(噸)'])
                ) if row['填料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )


            df_grouped['纖維得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論纖維產量(噸)'] / row['纖維領用量(噸)'])
                ) if row['纖維領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped['塗料得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論塗佈產量(噸)'] / row['塗料領用量(噸)'])
                ) if row['塗料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped['填料得率(%)'] = df_grouped.apply(
                lambda row: (
                    (row['理論填料產量(噸)'] / row['填料領用量(噸)'])
                ) if row['填料領用量(噸)'] not in [0, None, np.nan] else 0,
                axis=1
            )

            df_grouped['年月'] = df_grouped['年'].astype(str).str.zfill(4) + df_grouped['月'].astype(str).str.zfill(2)
            df_grouped['約當量'] = df_grouped['塗前約當量(噸)'] + df_grouped['塗後約當量(噸)']

            df_grouped_result = (
                df_grouped
                .groupby(['機台','PN2','類別','年月'], observed=True)
                .agg(纖維得率=('纖維得率(%)','sum'),塗料得率=('塗料得率(%)','sum'),約當量=('約當量','sum'))
                .unstack('年月')            # 年月變成欄
            )

            # 補缺值
            if '纖維得率' in df_grouped_result.columns.get_level_values(0):
                df_grouped_result['纖維得率'] = df_grouped_result['纖維得率'].fillna(0)
                df_grouped_result['纖維得率'] = np.where(df_grouped_result['纖維得率'] < 0, 0, df_grouped_result['纖維得率'])
            if '塗料得率' in df_grouped_result.columns.get_level_values(0):
                df_grouped_result['塗料得率'] = df_grouped_result['塗料得率'].fillna(0) 
                df_grouped_result['塗料得率'] = np.where(df_grouped_result['塗料得率'] < 0, 0, df_grouped_result['塗料得率'])
            if '約當量' in df_grouped_result.columns.get_level_values(0):
                df_grouped_result['約當量'] = df_grouped_result['約當量'].fillna(0)                


            # 如果要讓欄位扁平化
            df_grouped_result.columns = [f"{col[0]}_{col[1]}" for col in df_grouped_result.columns]
            df_grouped_result = df_grouped_result.reset_index()


            df_grouped_2['年月'] = df_grouped_2['年'].astype(str).str.zfill(4) + df_grouped_2['月'].astype(str).str.zfill(2)
            df_grouped_2['約當量'] = df_grouped_2['塗前約當量(噸)'] + df_grouped_2['塗後約當量(噸)']            

            df_grouped_2_result = (
                df_grouped_2
                .groupby(['機台','類別','年月'], observed=True)
                .agg(纖維得率=('纖維得率(%)','sum'),塗料得率=('塗料得率(%)','sum'),約當量=('約當量','sum'))
                .unstack('年月')            # 年月變成欄
            )

            # 補約當量的缺值
            if '纖維得率' in df_grouped_2_result.columns.get_level_values(0):
                df_grouped_2_result['纖維得率'] = df_grouped_2_result['纖維得率'].fillna(0)
                df_grouped_2_result['纖維得率'] = np.where(df_grouped_2_result['纖維得率'] < 0, 0, df_grouped_2_result['纖維得率'])
            if '塗料得率' in df_grouped_2_result.columns.get_level_values(0):
                df_grouped_2_result['塗料得率'] = df_grouped_2_result['塗料得率'].fillna(0)
                df_grouped_2_result['塗料得率'] = np.where(df_grouped_2_result['塗料得率'] < 0, 0, df_grouped_2_result['塗料得率'])
            if '約當量' in df_grouped_2_result.columns.get_level_values(0):
                df_grouped_2_result['約當量'] = df_grouped_2_result['約當量'].fillna(0)                


            # 如果要讓欄位扁平化
            df_grouped_2_result.columns = [f"{col[0]}_{col[1]}" for col in df_grouped_2_result.columns]
            df_grouped_2_result = df_grouped_2_result.reset_index()
            
            def add_weighted_yield(df, year: int):
                # 動態組欄位名稱 (01 ~ 12)
                months = [str(i).zfill(2) for i in range(1, 13)]

                fiber_cols = [f"纖維得率_{year}{m}" for m in months if f"纖維得率_{year}{m}" in df.columns]
                paint_cols = [f"塗料得率_{year}{m}" for m in months if f"塗料得率_{year}{m}" in df.columns]
                weight_cols = [f"約當量_{year}{m}" for m in months if f"約當量_{year}{m}" in df.columns]

                if not weight_cols:
                    raise ValueError(f"DataFrame 中找不到 約當量_{year}xx 欄位")

                # 計算加權平均的內部函式
                def weighted_avg(value_cols, weight_cols, name):
                    if value_cols:
                        numerator = (df[value_cols].values * df[weight_cols].values).sum(axis=1)
                        denominator = df[weight_cols].sum(axis=1)
                        result = np.where(
                            denominator == 0,
                            0,  # 避免 0/0 變 NaN
                            numerator / denominator
                        )
                        result = np.where((result < 0) | (abs(result) < 1e-8), 0, result)
                        df[name] = result

                # 纖維得率
                weighted_avg(fiber_cols, weight_cols, f"纖維得率_{year}")

                # 塗料得率
                weighted_avg(paint_cols, weight_cols, f"塗料得率_{year}")
                
                df = df.applymap(lambda x: 0 if isinstance(x, (int, float)) and abs(x) < 1e-8 else x)

                return df

            df_grouped_result = add_weighted_yield(df_grouped_result, year)
            df_grouped_2_result = add_weighted_yield(df_grouped_2_result, year)
            
            # 轉長表
            df_grouped_result_long = df_grouped_result.melt(
                id_vars=['機台', 'PN2', '類別'],
                var_name='yearmonth',
                value_name='value'
            ).to_dict(orient='records')

            df_grouped_2_result_long = df_grouped_2_result.melt(
                id_vars=['機台', '類別'],
                var_name='yearmonth',
                value_name='value'
            ).to_dict(orient='records')


            # 包成最終 JSON
            result_json = {
                "metadata": {
                    "name": "monthly_yield_rate",
                    "source": "monthly_yield_rate",
                    "description": "monthly_yield_rate"
                },
                "data": {
                    "Content": {
                         "PN2":df_grouped_result_long,
                         "Category":df_grouped_2_result_long

                    }
                }
            }            
            
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


# ERP_inventory


# In[ ]:


class ERP_inventory:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, mname: str, month: str):
        startTime = time.time()
        
        if not mname:
            return {'success': False, 'message': 'Missing machine_name parameter'}
        if not month:
            if not stime:
                return {'success': False, 'message': 'Missing date_from parameter'}   
            if not etime:
                return {'success': False, 'message': 'Missing date_to parameter'} 

            try:
                dt = datetime.datetime.strptime(stime, '%Y-%m-%d')
                start_year, start_month, start_day = dt.year, dt.month, dt.day
            except (ValueError, TypeError):
                return {'success': False, 'message': 'Incorrect date format year_month_from, please use YYYY-MM-DD'}

            try:
                dt = datetime.datetime.strptime(etime, '%Y-%m-%d')
                end_year, end_month, end_day = dt.year, dt.month, dt.day
            except (ValueError, TypeError):
                return {'success': False, 'message': 'Incorrect date format date_to, please use YYYY-MM-DD'}  
        
        # 讀取入庫量(MES)
        def search_Inventory_MES(stime,etime,mname):

            df_RE_transRate = pd.read_excel(r'\\Srvafp1\Public\Document\日結相關資訊\實際成本單\FTA平版料號轉換率\FTA 平版料號轉換率.xlsx',
                                      sheet_name='工作表1',skiprows=0)
            df_RE_transRate = df_RE_transRate[df_RE_transRate['TO 單位類別'] != 'Length']
            df_RE_transRate['料號_2'] = df_RE_transRate['料號'].str[-13:]
            df_RE_transRate_reduce = df_RE_transRate.groupby(['料號_2','轉換率']).size().reset_index().groupby(['料號_2'])['轉換率'].min().reset_index()

            srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
            with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:               
                sql =   """
                    SELECT [PROCESS_CODE]
                          ,[SERVER_CODE]
                          ,[BATCH_ID]
                          ,[BATCH_LINE_ID]
                          ,[STATUS_CODE]
                          ,[ORGCODE]
                          ,[RXID]
                          ,[PREVIOUS_RXID]
                          ,[BATCH_NO]
                          ,[MACHINE_NO]
                          ,[ITEM_NO]
                          ,SUBSTRING([ITEM_NO],2,4) as ptype
                          ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                          ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                          ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                          ,[SUBINVENTORY_CODE]
                          ,[LOCATOR]
                          ,[TRANSACTION_QUANTITY]
                          ,[TRANSACTION_UOM]
                          ,[SECONDARY_TRANSACTION_QUANTITY]
                          ,[SECONDARY_UOM_CODE]
                          ,[TRANSACTION_DATE]
                          ,convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) as bdate
                          ,[LOT_NUMBER]
                          ,[STATUS]
                      FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST]
                      WHERE 1=1
                      AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                      --AND MACHINE_NO IN ('18','19','20','21')
                      AND MACHINE_NO = '"""+ str(mname) +"""'
                      AND SUBINVENTORY_CODE != 'SFG'
                      AND STATUS_CODE = 'S'

                      UNION ALL

                    SELECT [PROCESS_CODE]
                          ,[SERVER_CODE]
                          ,[BATCH_ID]
                          ,[BATCH_LINE_ID]
                          ,[STATUS_CODE]
                          ,[ORGCODE]
                          ,[RXID]
                          ,[PREVIOUS_RXID]
                          ,[BATCH_NO]
                          ,[MACHINE_NO]
                          ,[ITEM_NO]
                          ,SUBSTRING([ITEM_NO],2,4) as ptype
                          ,CAST(SUBSTRING([ITEM_NO],7,5) AS INT) as gramg
                          ,REPLACE(SUBSTRING([ITEM_NO],12,4),'K','') as length
                          ,REPLACE(SUBSTRING([ITEM_NO],16,4),'K','') as width
                          ,[SUBINVENTORY_CODE]
                          ,[LOCATOR]
                          ,[TRANSACTION_QUANTITY]
                          ,[TRANSACTION_UOM]
                          ,[SECONDARY_TRANSACTION_QUANTITY]
                          ,[SECONDARY_UOM_CODE]
                          ,[TRANSACTION_DATE]
                          ,convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) as bdate
                          ,[LOT_NUMBER]
                          ,[STATUS]
                      FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P211_IN_MMT_PROD_ST]
                      where 1=1
                      AND (
                        (SUBSTRING([ITEM_NO],2,4) like 'MM%' AND [ITEM_NO] like '%R') 
                        OR 
                        (RIGHT(SUBSTRING([ITEM_NO],2,4),3) = 'NCR' AND [ITEM_NO] like '%R')
                      )
                      AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                      AND [STATUS_CODE] = 'S' 
                      AND MACHINE_NO = '"""+ str(mname) +"""'
                """       
                query = conn.execute(text(sql))
                df_inventory_250 = pd.DataFrame([dict(i) for i in query])
                
            if not df_inventory_250.empty:

                df_inventory_250['料號_2'] = df_inventory_250['ITEM_NO'].str[-13:]   

                df_inventory_250_C = df_inventory_250[df_inventory_250['STATUS'] == 'C']
                df_inventory_250_M = df_inventory_250[df_inventory_250['STATUS'] == 'M']
                df_inventory_250_C = df_inventory_250_C[~df_inventory_250_C['RXID'].isin(list(df_inventory_250[df_inventory_250['STATUS'] == 'M']['PREVIOUS_RXID']))]
                df_inventory_250_M = df_inventory_250_M.loc[df_inventory_250_M.groupby('PREVIOUS_RXID')['TRANSACTION_DATE'].idxmax()]

                df_inventory_250_latest = pd.concat([df_inventory_250_C,df_inventory_250_M],ignore_index=True)
                df_inventory_250_latest = df_inventory_250_latest.loc[:,['bdate','MACHINE_NO','ptype', 'gramg','ITEM_NO','TRANSACTION_QUANTITY','TRANSACTION_UOM',
                                              'SECONDARY_TRANSACTION_QUANTITY','SECONDARY_UOM_CODE','料號_2']]
                df_inventory_250_latest = df_inventory_250_latest.merge(df_RE_transRate_reduce,on='料號_2',how='left')
                df_inventory_250_latest['weigh'] = np.where(
                    df_inventory_250_latest['SECONDARY_UOM_CODE'].isna(),
                    df_inventory_250_latest['TRANSACTION_QUANTITY'] * 1000,
                    df_inventory_250_latest['SECONDARY_TRANSACTION_QUANTITY'].astype(float) * df_inventory_250_latest['轉換率'] / 1000.0
                )
                df_inventory_250_latest['gramg'] = df_inventory_250_latest['gramg'].astype(float) / 10.0
                df_inventory_250_latest['MACHINE_NO'] = np.where(
                    df_inventory_250_latest['ptype'].str.endswith('NCR'),
                    'PM' + df_inventory_250_latest['MACHINE_NO'],
                    np.where(
                        df_inventory_250_latest['ptype'].str.startswith('H'),
                        'NCR',
                        np.where(
                            df_inventory_250_latest['ptype'].str.startswith('T'),
                            '含浸',
                            'PM' + df_inventory_250_latest['MACHINE_NO']
                        )        
                    )
                )
                df_inventory_250_result = df_inventory_250_latest.groupby(['bdate','MACHINE_NO','ptype','gramg'])['weigh'].sum().reset_index()

                df_inventory_250_result.rename(columns={'MACHINE_NO':'機台','ptype':'PN4','gramg':'基重','weigh':'合計(kg)'},inplace=True)

                df_inventory_250_result['基重'] = df_inventory_250_result['基重'].round(1).astype(str)

                df_inventory_250_result['合計(kg)'] = df_inventory_250_result['合計(kg)'].astype(float).round(1)
                df_inventory_250_result['紙別基重'] = df_inventory_250_result['機台'] + df_inventory_250_result['PN4'] + df_inventory_250_result['基重']
                df_inventory_250_result['紙別基重'] = df_inventory_250_result['紙別基重'].str.replace(r'\.0$', '', regex=True)

                df_inventory_250_result['合計'] = df_inventory_250_result['合計(kg)'] / 1000.0
                
            else:
                df_inventory_250_result = pd.DataFrame(columns=['bdate', '機台', 'PN4', '基重', '合計(kg)', '紙別基重', '合計'])                  

            return df_inventory_250_result
        
        # 讀取期末在產品(MES)
        def search_InProcess_MES(stime,etime):

            srv_SRVAD1 = self.servers['SRVAD1'] 
            with srv_SRVAD1['create_engine'][0].connect() as conn:            
                sql =   """
                    ;with raw_data as
                    (
                        select 
                            a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                        from openquery([10.10.1.27],'select * from [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] where Creation_date >= dateadd(m,-6,getdate())') a
                        inner join adpack b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass <> 'A') and substring(batch_no,10,2) = 'SH'
                        where 1=1
                        and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                        and re <> 0 and a.status_code = 'S'

                        union

                        select a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                        from openquery([10.10.1.27],'select * from [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] where Creation_date >= dateadd(m,-6,getdate())') a
                        inner join adsel b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass IN ('B','P') or b.pclass is null) and substring(batch_no,10,2) = 'SH'
                        where 1=1
                        and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                        and nstation not in('SP','WP','WH') 
                        and re <> 0 and a.status_code = 'S'
                        --order by runno, batch_no, ptype, psize1, psize2, x_yn, bhno
                    )
                    SELECT YEAR(bdate) AS [年],MONTH(bdate) AS [月],DAY(bdate) AS [日],
                                bdate,mname_2 AS mname,ptype,pgramg,SUM(T) AS T
                    FROM
                    (
                        SELECT runno,mname_2,bdate,batch_no,ptype,pgramg,psize1,psize2,store,ExportSales,pclass,rewt,SUM(re) AS re,SUM(T) AS T,
                        count(*) as amount
                        FROM
                        (
                            SELECT *,rewt*re*0.0004535924 AS T,
                            CASE WHEN x_yn = 'Y' Then '外銷' ELSE '內銷' END AS ExportSales,
                            CASE WHEN x_yn = 'Y' Then 'A4FG'
                            WHEN x_yn = 'N' AND substring(runno,1,1) = 'R' THEN 'A3FG'
                            WHEN x_yn = 'N' AND substring(runno,1,1) = 'S' THEN 'A2FG'
                            WHEN x_yn = 'N' AND substring(runno,1,1) = 'W' THEN 'A1FG'
                            END AS store,
                            CASE WHEN ptype like 'H%' THEN 'NCR'
                                 WHEN left(runno,1) = 'R' THEN 'PM18'
                                 WHEN left(runno,1) = 'S' THEN 'PM19'
                                 WHEN left(runno,1) = 'T' THEN 'PM20'
                                 WHEN left(runno,1) = 'W' THEN 'PM21'
                            END AS mname_2
                            FROM raw_data
                        ) t
                        GROUP BY runno,mname_2,bdate,batch_no,ptype,pgramg,psize1,psize2,store,ExportSales,pclass,rewt
                    ) m
                    GROUP BY bdate,mname_2,ptype,pgramg          
                """       
                query = conn.execute(text(sql))  
                df_ERP_SH = pd.DataFrame([dict(i) for i in query]) 

                sql =   """
                    SELECT 
                        YEAR(bdate) AS [年],
                        MONTH(bdate) AS [月],
                        DAY(bdate) AS [日],                    
                        bdate,                    
                        mname_2 AS mname,
                        ptype,
                        pgramg,
                        sum(weigh) as T 

                    FROM
                    (
                        SELECT *,CASE 
                            WHEN x_yn = 'Y' AND pstatus = '成品' THEN 'A4FG'
                            WHEN pstatus = '成品' THEN 
                                CASE 
                                    WHEN left(relno,1) = 'R' AND prodn <> 'R' THEN 'A3FG'
                                    WHEN left(relno,1) = 'S' AND prodn <> 'R' THEN 'A2FG'
                                    WHEN (left(relno,1) = 'T' AND prodn <> 'R') 
                                         OR (left(relno,1) = 'R' AND prodn <> 'R') 
                                         OR (left(relno,1) = 'S' AND prodn <> 'R') THEN 'A6FG'
                                    WHEN left(relno,1) = 'W' AND prodn <> 'R' THEN 'A7FG'   
                                    ELSE NULL  -- 如果沒有符合條件，不設值
                                END
                            ELSE 'FTA.SFG.SR.PM' + CAST(left(relno,1) AS VARCHAR)  -- 非 "成品" 情況，store 依 mname 設定
                        END AS store,
                        CASE WHEN left(relno,1) = 'R' THEN 'PM18'
                             WHEN left(relno,1) = 'S' THEN 'PM19'
                             WHEN left(relno,1) = 'T' THEN 'PM20'
                             WHEN left(relno,1) = 'W' THEN 'PM21'
                        END AS mname_2
                        FROM
                        (
                            select *,
                            CASE 
                                WHEN prod = '1' THEN 
                                    CASE 
                                        WHEN LEFT(ptype, 1) = 'H' AND CAST(width AS FLOAT) >= 100 
                                            THEN RIGHT('00' + CAST(width AS VARCHAR), 4) + 'RL00'
                                        WHEN LEFT(ptype, 1) = 'H' OR CAST(width AS FLOAT) < 100 
                                            THEN 
                                                CASE 
                                                    WHEN RIGHT(CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) AS VARCHAR), 1) = '5' 
                                                        THEN RIGHT('00' + CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) - 1 AS VARCHAR), 3) + 'KRL00'
                                                    WHEN RIGHT(CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) AS VARCHAR), 1) = '8' 
                                                        THEN RIGHT('00' + CAST(CAST(CAST(width AS FLOAT) * 10 AS INT) - 2 AS VARCHAR), 3) + 'KRL00'
                                                    ELSE RIGHT('00' + CAST(CAST(width AS FLOAT) * 10 AS VARCHAR), 3) + 'KRL00'
                                                END
                                        ELSE 
                                            RIGHT('00' + CAST(width AS VARCHAR), 4) + 'RL00'
                                    END
                                WHEN prod IN ('2', '4', '7', '8') THEN 'R'
                                ELSE NULL 
                            END AS prodn,
                            CASE WHEN prod = 1 THEN '成品'
                            WHEN prod = 2 Then '裁切'
                            WHEN prod = 4 Then '中倉'
                            WHEN prod = 7 Then '分條'
                            WHEN prod = 8 Then '含浸' END AS pstatus

                            from adwind 
                            where 1=1
                            and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'  
                            and prod not in('3','5','6','9') 
                            --order by runno, prod, ptype, pclass, width, pgramg, x_yn, relno, swinno           
                        ) m 
                    ) t
                    WHERE store NOT LIKE '%SR%'
                    GROUP BY bdate,mname_2,ptype,pgramg     
                """       
                query = conn.execute(text(sql))  
                df_ERP_SR = pd.DataFrame([dict(i) for i in query])   

            srv_SRVAD2 = self.servers['SRVAD2'] 
            with srv_SRVAD2['create_engine'][0].connect() as conn:                
                sql =   """
                    --ACAA040I3.ASP
                    DECLARE @sdate varchar(10) = '"""+ str(stime) +"""'
                    DECLARE @edate varchar(10) = '"""+ str(etime) +"""'

                    ;With raw_data as
                    (
                        SELECT *
                        FROM
                        (
                            --SRVAD2
                            select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation,sptype,
                            CASE WHEN pm='W' AND nstation = 'WR' Then '再捲機'
                            WHEN pm='W' AND nstation = 'WC' Then '塗佈機'
                            WHEN pm='W' AND nstation = 'WE' Then '壓光機'
                            WHEN pm='W' AND nstation = 'WW' Then '複捲機'

                            WHEN pm='T' AND nstation = 'TR' Then '再捲機'
                            WHEN pm='T' AND nstation = 'TC' Then '塗佈機'
                            WHEN pm='T' AND nstation = 'TE' Then '壓光機'
                            WHEN pm='T' AND nstation = 'TW' Then '複捲機'

                            WHEN pm='S' AND nstation = 'SW' Then '複捲機'
                            WHEN pm='R' AND nstation = 'RW' Then '複捲機'

                            END AS 機台
                            from [pm21].[dbo].[adbuff_prod] where cbdate between @sdate and @edate

                            UNION ALL

                            select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation,sptype,
                            CASE WHEN pm='W' AND nstation = 'WC' Then '塗佈機'
                            WHEN pm='W' AND nstation = 'WS' Then '裁切機'
                            WHEN pm='W' AND nstation = 'WW' Then '分條機'
                            WHEN pm='W' AND nstation = 'WE' Then '壓光機'

                            WHEN pm='T' AND nstation = 'TR' Then '再捲機'
                            WHEN pm='T' AND nstation = 'TC' Then '塗佈機'
                            WHEN pm='T' AND nstation = 'TE' Then '壓光機'
                            WHEN pm='T' AND nstation = 'TS' Then '裁切機'

                            WHEN pm='S' AND nstation = 'SE' Then '壓光機'
                            WHEN pm='S' AND nstation = 'SC' Then '塗佈機'
                            WHEN pm='S' AND nstation = 'SS' Then '裁切機'
                            WHEN pm='S' AND nstation = 'SW' Then '分條機'

                            WHEN pm='R' AND nstation = 'RS' Then '裁切機'

                            END AS 機台

                            from [SRVAD2].[pm21].[dbo].[adwind_prod] where cbdate between @sdate and @edate
                            UNION ALL
                            select cbdate,pm,mname,ptype,gramg,pgramg,(rewt*re/2204.62),nstation as weigh,sptype,
                            CASE WHEN pm='W' AND nstation = 'WH' Then '選紙班'
                            WHEN pm='W' AND nstation = 'WP' Then '包裝機'

                            WHEN pm='T' AND nstation = 'TH' Then '選紙班'
                            WHEN pm='T' AND nstation = 'TP' Then '包裝機'

                            WHEN pm='S' AND nstation = 'SH' Then '選紙班'
                            WHEN pm='S' AND nstation = 'SP' Then '包裝機'

                            WHEN pm='R' AND nstation = 'RH' Then '選紙班'
                            END AS 機台

                            from [SRVAD2].[pm21].[dbo].[adstock_prod] where cbdate between @sdate and @edate
                        ) t
                        WHERE 1=1
                        AND 機台 is not null --AND gramg is not null 
                        AND len(ptype) > 0
                        --AND ptype = 'KL00' AND pgramg = '58'
                    )
                    SELECT 
                    YEAR(cbdate) AS 年,
                    MONTH(cbdate) AS 月,
                    DAY(cbdate) AS 日,
                    CASE WHEN pm='R' THEN 'PM18' WHEN pm='S' THEN 'PM19' WHEN pm='T' THEN 'PM20' WHEN pm='W' THEN 'PM21' ELSE '' END AS 號機,
                    ptype AS 紙別,
                    pgramg AS '基重(原紙)',
                    pgramg AS '基重(成品)',
                    ISNULL(SUM([塗佈前]),0) AS [塗佈前],
                    ISNULL(SUM([壓光前]),0) AS [壓光前],
                    ISNULL(SUM([複捲前(含中間倉)]),0) AS [複捲前(含中間倉)],
                    ISNULL(SUM([截切前]),0) AS [截切前],
                    ISNULL(SUM([包裝前]),0) AS [包裝前],
                    ISNULL(SUM([已包未入庫]),0) AS [已包未入庫]
                    FROM (
                        SELECT 
                            cbdate,pm,ptype,gramg,pgramg,sptype,
                            CASE WHEN ptype like '%NCR' Then ''
                            WHEN ptype like '%MM' Then ''
                            WHEN 機台 IN ('再捲機','塗佈機') THEN '塗佈前'
                            WHEN 機台 = '壓光機' THEN '壓光前'
                            WHEN 機台 IN ('複捲機','分條機') THEN '複捲前(含中間倉)'
                            WHEN 機台 = '裁切機' THEN '截切前'
                            WHEN 機台 IN ('選紙班','包裝機') THEN '包裝前'
                            END AS 機台,
                            weigh
                        FROM raw_data
                    ) AS source
                    PIVOT (
                        SUM(weigh)
                        FOR 機台 IN ([塗佈前],[壓光前],[複捲前(含中間倉)],[截切前],[包裝前],[已包未入庫])
                    ) AS pivot_table
                    --WHERE pm = 'W'
                    GROUP BY cbdate,pm,ptype,pgramg
                    ORDER BY cbdate,pm desc,ptype,pgramg
                """       
                query = conn.execute(text(sql))  
                df_InProcess = pd.DataFrame([dict(i) for i in query])

            df_ERP_SR_SH = pd.concat([df_ERP_SR,df_ERP_SH],ignore_index=True)
            df_ERP_SR_SH.rename(columns={'mname':'號機','ptype':'紙別','pgramg':'基重(成品)','T':'已包未入庫'},inplace=True)
            df_ERP_SR_SH['基重(原紙)'] = df_ERP_SR_SH['基重(成品)'].copy()
            df_ERP_SR_SH['塗佈前'] = 0.0
            df_ERP_SR_SH['壓光前'] = 0.0
            df_ERP_SR_SH['複捲前(含中間倉)'] = 0.0
            df_ERP_SR_SH['截切前'] = 0.0
            df_ERP_SR_SH['包裝前'] = 0.0
            df_ERP_SR_SH['已包未入庫'] = df_ERP_SR_SH['已包未入庫'].astype(float)

            df_result = pd.concat([df_InProcess,df_ERP_SR_SH],ignore_index=True)
            
            df_result = df_result[df_result['號機'] == ('PM'+str(mname))]
            
            df_result = df_result[df_result['號機'] == ('PM'+str(mname))]

            df_result['號機'] = np.where(
                df_result['紙別'].str.endswith('NCR'),
                df_result['號機'],
                np.where(
                    df_result['紙別'].str.startswith('H'), 
                    'NCR',
                    np.where(
                        df_result['紙別'].str.startswith('TR'),
                        '含浸',
                        df_result['號機']
                    )
                )
            )

            df_result = df_result.groupby(['年','月','日','號機','紙別','基重(原紙)','基重(成品)'])                .agg(a=('塗佈前','sum'), 
                     b=('壓光前','sum'),
                     c=('複捲前(含中間倉)','sum'), 
                     d=('截切前','sum'),
                     e=('包裝前','sum'),
                     f=('已包未入庫','sum'),
                    ).reset_index()  

            df_result = df_result.rename(columns={
                'a': '塗佈前',
                'b': '壓光前',
                'c': '複捲前(含中間倉)',
                'd': '截切前',
                'e': ' 包裝前',
                'f': '已包未入庫',
            })

            return df_result
        
        def Work_In_Process(df):
            df = df.dropna(how='all')
            df = df[df['年'].notna()].reset_index(drop=True)
            df['年'] = df['年'].astype(int)
            df['月'] = df['月'].astype(int)
            df['日'] = df['日'].astype(int)

            # 選取欄位

            df = df.loc[:,['年', '月', '日', '號機', '紙別', '基重(原紙)','基重(成品)', '塗佈前', 
                                   '壓光前','複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']]
            # 計算欄位

            df['總計(噸數)'] = df[['塗佈前', '壓光前', '複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']].sum(axis=1, skipna=True).round(3)

            df['基重(原紙)'] = df['基重(原紙)'].apply(
                lambda x: str(int(x)) if pd.notna(x) and float(x) == int(float(x))
                else (str(x) if pd.notna(x) else None)
            )

            df['紙別基重(塗前)'] = df['號機'].astype(str) + df['紙別'].astype(str) + df['基重(成品)'].astype(float).astype(str).replace(r'\.0$', '', regex=True)

            df['塗前'] = df[['塗佈前']].sum(axis=1, skipna=True)
            df['塗後'] = df[['壓光前', '複捲前(含中間倉)', '截切前', ' 包裝前', '已包未入庫']].sum(axis=1, skipna=True).round(3)

            df = df.replace({pd.NA: None, np.nan: None})

            return df.copy()  
        
        if not month:
        
            stime_1 = str((datetime.datetime.strptime(stime, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d'))

            df_result_Inprocess = search_InProcess_MES(stime_1,etime)
            df_result_Inprocess = Work_In_Process(df_result_Inprocess)

            df_result_Inprocess['bdate'] = pd.to_datetime(
                df_result_Inprocess.rename(columns={'年': 'year', '月': 'month', '日': 'day'})[['year', 'month', 'day']]
            )

            df_result = search_Inventory_MES(stime_1,etime,mname)

            df_result_Inprocess_Inventory = df_result_Inprocess.merge(df_result,left_on=['bdate','紙別基重(塗前)'],right_on=['bdate','紙別基重'],how='outer')
            df_result_Inprocess_Inventory[['塗後', '合計', '塗前']] = df_result_Inprocess_Inventory[['塗後', '合計', '塗前']].fillna(0)

            df_result_Inprocess_Inventory['機台'] = df_result_Inprocess_Inventory['機台'].fillna(df_result_Inprocess_Inventory['號機'])
            df_result_Inprocess_Inventory['PN4'] = df_result_Inprocess_Inventory['PN4'].fillna(df_result_Inprocess_Inventory['紙別'])
            df_result_Inprocess_Inventory['基重'] = df_result_Inprocess_Inventory['基重'].fillna(df_result_Inprocess_Inventory['基重(成品)'])        

            df_result_Inprocess_Inventory['bdate'] = pd.to_datetime(df_result_Inprocess_Inventory['bdate'])

            # 建立「前一天資料」的 DataFrame
            df_result_Inprocess_Inventory_prev = df_result_Inprocess_Inventory.copy()
            df_result_Inprocess_Inventory_prev['bdate'] = df_result_Inprocess_Inventory_prev['bdate'] + pd.Timedelta(days=1)

            # 為避免欄位名稱衝突，重新命名三個欄位
            df_result_Inprocess_Inventory_prev = df_result_Inprocess_Inventory_prev.rename(columns={
                '塗前': '前日_塗前',
                '塗後': '前日_塗後',
                '已包未入庫': '前日_已包未入庫'
            })

            # merge 時，用 bdate、機台、PN4、基重 當 key
            df_result_Inprocess_Inventory_merge = df_result_Inprocess_Inventory.merge(
                df_result_Inprocess_Inventory_prev[['bdate', '機台', 'PN4', '基重', '前日_塗前', '前日_塗後','前日_已包未入庫']],
                on=['bdate', '機台', 'PN4', '基重'],
                how='left'
            )

            df_result_Inprocess_Inventory_merge['約當量'] = (
                df_result_Inprocess_Inventory_merge['塗前'].fillna(0) - df_result_Inprocess_Inventory_merge['前日_塗前'].fillna(0) + \
                df_result_Inprocess_Inventory_merge['塗後'].fillna(0) - df_result_Inprocess_Inventory_merge['前日_塗後'].fillna(0) + \
                df_result_Inprocess_Inventory_merge['合計'].fillna(0)
            ).round(3)

            df_result_Inprocess_Inventory_merge = df_result_Inprocess_Inventory_merge[~df_result_Inprocess_Inventory_merge['前日_塗前'].isna()]
            df_result_Inprocess_Inventory_merge = df_result_Inprocess_Inventory_merge[~df_result_Inprocess_Inventory_merge['前日_塗後'].isna()]
            df_result_Inprocess_Inventory_merge = df_result_Inprocess_Inventory_merge.reset_index(drop=True)        

            df_result_Inprocess_Inventory_merge["bdate"] = df_result_Inprocess_Inventory_merge["bdate"].astype(str)

            df_result_Inprocess_Inventory_merge["基重"] = df_result_Inprocess_Inventory_merge["基重"].astype(str)
            df_result_Inprocess_Inventory_merge["合計"] = df_result_Inprocess_Inventory_merge["合計"].round(3).astype(str)
            df_result_Inprocess_Inventory_merge["約當量"] = df_result_Inprocess_Inventory_merge["約當量"].astype(str)

            # 建立 JSON 結構
            result_json = {
                "data": [
                    {
                        "日期": row['bdate'],
                        "機台": row["機台"],
                        "PN4": row["PN4"],
                        "基重": row["基重"],
                        "入庫量": row["合計"],
                        "約當量": row["約當量"],
                        "期初在產品量": str(row['前日_塗前'] + row['前日_塗後']),
                        "期末在產品量": str(row['塗前'] + row['塗後']),
                        "期初已包未入庫量": str(row['前日_已包未入庫']),
                        "期末已包未入庫量": str(row['已包未入庫'])

                    }
                    for _, row in df_result_Inprocess_Inventory_merge.iterrows()
                ]
            }   
            
        else:
            dt = datetime.datetime.strptime(month, "%Y-%m")
            if dt == datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m"), "%Y-%m"):
                return {'success': False, 'message': 'No data available because this month has not yet ended'}, 400            
            etime_t = (dt + relativedelta(months=1) - timedelta(days=1))
            etime_t = etime_t.strftime('%Y-%m-%d')

            stime_t = (dt- timedelta(days=1)).strftime('%Y-%m-%d')                

            df_result_Inprocess_before = search_InProcess_MES(stime_t,stime_t)
            df_result_Inprocess_before = Work_In_Process(df_result_Inprocess_before)
            df_result_Inprocess_before['bdate'] = pd.to_datetime(
                df_result_Inprocess_before.rename(columns={'年': 'year', '月': 'month', '日': 'day'})[['year', 'month', 'day']]
            )
            
            df_result_Inprocess_after = search_InProcess_MES(etime_t,etime_t)
            df_result_Inprocess_after = Work_In_Process(df_result_Inprocess_after)
            df_result_Inprocess_after['bdate'] = pd.to_datetime(
                df_result_Inprocess_after.rename(columns={'年': 'year', '月': 'month', '日': 'day'})[['year', 'month', 'day']]
            )

            df_result = search_Inventory_MES(etime_t,etime_t,mname)

            df_result_Inprocess_Inventory = df_result_Inprocess_after.merge(df_result,left_on=['bdate','紙別基重(塗前)'],right_on=['bdate','紙別基重'],how='outer')
            df_result_Inprocess_Inventory[['塗後', '合計', '塗前']] = df_result_Inprocess_Inventory[['塗後', '合計', '塗前']].fillna(0)

            df_result_Inprocess_Inventory['機台'] = df_result_Inprocess_Inventory['機台'].fillna(df_result_Inprocess_Inventory['號機'])
            df_result_Inprocess_Inventory['PN4'] = df_result_Inprocess_Inventory['PN4'].fillna(df_result_Inprocess_Inventory['紙別'])
            df_result_Inprocess_Inventory['基重'] = df_result_Inprocess_Inventory['基重'].fillna(df_result_Inprocess_Inventory['基重(成品)'])        

            df_result_Inprocess_Inventory['bdate'] = pd.to_datetime(df_result_Inprocess_Inventory['bdate'])

            # 建立「前一天資料」的 DataFrame
            df_result_Inprocess_Inventory_prev = df_result_Inprocess_before.copy()
            df_result_Inprocess_Inventory_prev['bdate'] = (dt + relativedelta(months=1) - timedelta(days=1))

            # 為避免欄位名稱衝突，重新命名三個欄位
            df_result_Inprocess_Inventory_prev = df_result_Inprocess_Inventory_prev.rename(columns={
                '塗前': '前日_塗前',
                '塗後': '前日_塗後',
                '已包未入庫': '前日_已包未入庫'
            })
            
            df_result_Inprocess_Inventory_prev['機台'] = df_result_Inprocess_Inventory_prev['號機'].fillna(df_result_Inprocess_Inventory_prev['號機'])
            df_result_Inprocess_Inventory_prev['PN4'] = df_result_Inprocess_Inventory_prev['紙別'].fillna(df_result_Inprocess_Inventory_prev['紙別'])
            df_result_Inprocess_Inventory_prev['基重'] = df_result_Inprocess_Inventory_prev['基重(成品)'].fillna(df_result_Inprocess_Inventory_prev['基重(成品)'])        

            df_result_Inprocess_Inventory_prev['bdate'] = pd.to_datetime(df_result_Inprocess_Inventory_prev['bdate'])             

            # merge 時，用 bdate、機台、PN4、基重 當 key
            df_result_Inprocess_Inventory_merge = df_result_Inprocess_Inventory.merge(
                df_result_Inprocess_Inventory_prev[['bdate', '機台', 'PN4', '基重', '前日_塗前', '前日_塗後','前日_已包未入庫']],
                on=['bdate', '機台', 'PN4', '基重'],
                how='left'
            )

            df_result_Inprocess_Inventory_merge['約當量'] = (
                df_result_Inprocess_Inventory_merge['塗前'].fillna(0) - df_result_Inprocess_Inventory_merge['前日_塗前'].fillna(0) + \
                df_result_Inprocess_Inventory_merge['塗後'].fillna(0) - df_result_Inprocess_Inventory_merge['前日_塗後'].fillna(0) + \
                df_result_Inprocess_Inventory_merge['合計'].fillna(0)
            ).round(3)

            df_result_Inprocess_Inventory_merge['前日_塗前'] = df_result_Inprocess_Inventory_merge['前日_塗前'].fillna(0)
            df_result_Inprocess_Inventory_merge['前日_塗後'] = df_result_Inprocess_Inventory_merge['前日_塗後'].fillna(0)
            df_result_Inprocess_Inventory_merge['前日_已包未入庫'] = df_result_Inprocess_Inventory_merge['前日_已包未入庫'].fillna(0)

            df_result_Inprocess_Inventory_merge["bdate"] = df_result_Inprocess_Inventory_merge["bdate"].astype(str)

            df_result_Inprocess_Inventory_merge["基重"] = df_result_Inprocess_Inventory_merge["基重"].astype(str)
            df_result_Inprocess_Inventory_merge["合計"] = df_result_Inprocess_Inventory_merge["合計"].astype(str)
            df_result_Inprocess_Inventory_merge["約當量"] = df_result_Inprocess_Inventory_merge["約當量"].astype(str)
            
            df_result_Inprocess_Inventory_merge = df_result_Inprocess_Inventory_merge.replace({pd.NA: None, np.nan: None})

            # 建立 JSON 結構
            result_json = {
                "data": [
                    {
                        "日期": row['bdate'],
                        "機台": row["機台"],
                        "PN4": row["PN4"],
                        "基重": row["基重"],
                        "入庫量": row["合計"],
                        "約當量": row["約當量"],
                        "期初在產品量": str(row['前日_塗前'] + row['前日_塗後']),
                        "期末在產品量": str(row['塗前'] + row['塗後']),
                        "期初已包未入庫量": str(row['前日_已包未入庫']),
                        "期末已包未入庫量": str(row['已包未入庫'])

                    }
                    for _, row in df_result_Inprocess_Inventory_merge.iterrows()
                ]
            }               

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


# End_work_in_process


# In[ ]:


class End_work_in_process:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, year_month_from: str):
        startTime = time.time()
        
        if not year_month_from:
            return {'success': False, 'message': 'Missing year_month_from parameter'}        

        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:   
            sql =   """
                  SELECT *  FROM [CostSheet].[dbo].[End_work_in_process]
                  WHERE 年月 = """ + str(year_month_from) + """
            """
            query = conn.execute(text(sql))  
            df_End_work_in_process = pd.DataFrame([dict(i) for i in query]) 
            
        if not df_End_work_in_process.empty:
            result_json = {
                "data": [
                    {
                        "年月": row["年月"],
                        "年": row["年"],
                        "月": row["月"],
                        "日": row["日"],
                        "號機": row["號機"],
                        "紙別": row["紙別"],
                        "基重(原紙)": row["基重(原紙)"],
                        "基重(成品)": row["基重(成品)"],
                        "塗佈前": row["塗佈前"],
                        "壓光前": row["壓光前"],
                        "複捲前(含中間倉)": row["複捲前(含中間倉)"],
                        "截切前": row["截切前"],
                        "包裝前": row["包裝前"],
                        "已包未入庫": row["已包未入庫"],
                        "總計(噸數)": row["總計(噸數)"],
                        "紙別基重(塗前)": row["紙別基重(塗前)"],
                        "塗前": row["塗前"],
                        "塗後": row["塗後"]
                    }
                    for _, row in df_End_work_in_process.iterrows()
                ]
            }   
            
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


class monthly_fixed_fee:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, year: str):
        startTime = time.time()
        
        if not year:
            return {'success': False, 'message': 'Missing year parameter'}        

        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:   
            sql =   """
                  SELECT *  FROM [CostSheet].[dbo].[Cost_sheet_details]
                  WHERE left(年月,4) = """ + str(year) + """
            """
            query = conn.execute(text(sql))  
            df_Cost_sheet_details = pd.DataFrame([dict(i) for i in query])
            
        if not df_Cost_sheet_details.empty:
            df_Cost_sheet_details_ptype = df_Cost_sheet_details.loc[df_Cost_sheet_details['Schsnm'] == '固定製造成本',['CostPT','年月','機台','兩碼紙別']]            .pivot_table(index=['機台', '兩碼紙別'],
                                    columns='年月',
                                    values='CostPT',
                                    aggfunc='sum',
                                    fill_value=0
                                ).reset_index()
            df_Cost_sheet_details_catrgory = df_Cost_sheet_details.loc[(df_Cost_sheet_details['Schsnm'] == '固定製造成本') & (df_Cost_sheet_details['兩碼紙別'].isna())
                                      ,['CostPT','年月','機台','大類別']]\
                                .pivot_table(index=['機台', '大類別'],
                                    columns='年月',
                                    values='CostPT',
                                    aggfunc='sum',
                                    fill_value=0
                                ).reset_index()                  
            
            result_json = {
                "data": {
                    'df_Cost_sheet_details_ptype':df_Cost_sheet_details_ptype.to_dict(orient='records'),
                    'df_Cost_sheet_details_catrgory':df_Cost_sheet_details_catrgory.to_dict(orient='records')
                }
            }   
            
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


class monthly_energy_usage:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, year: str):
        startTime = time.time()
        
        if not year:
            return {'success': False, 'message': 'Missing year parameter'}        

        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:   
            sql =   """
                  SELECT *  FROM [CostSheet].[dbo].[Cost_sheet_details]
                  WHERE left(年月,4) = """ + str(year) + """
            """
            query = conn.execute(text(sql))  
            df_Cost_sheet_details = pd.DataFrame([dict(i) for i in query])
            
        if not df_Cost_sheet_details.empty:
            df_Cost_sheet_details_fuel_ptype = df_Cost_sheet_details.loc[df_Cost_sheet_details['Schsnm'] == '燃料費',['ConsPT','年月','機台','兩碼紙別']]                                .pivot_table(index=['機台', '兩碼紙別'],
                                    columns='年月',
                                    values='ConsPT',
                                    aggfunc='sum',
                                    fill_value=0
                                ).reset_index()

            df_Cost_sheet_details_fuel_catrgory = df_Cost_sheet_details.loc[(df_Cost_sheet_details['Schsnm'] == '燃料費') & (df_Cost_sheet_details['兩碼紙別'].isna())
                                      ,['ConsPT','年月','機台','大類別']]\
                                .pivot_table(index=['機台', '大類別'],
                                    columns='年月',
                                    values='ConsPT',
                                    aggfunc='sum',
                                    fill_value=0
                                ).reset_index()    

            df_Cost_sheet_details_elec_ptype = df_Cost_sheet_details.loc[df_Cost_sheet_details['Schsnm'] == '電力費',['ConsPT','年月','機台','兩碼紙別']]                                .pivot_table(index=['機台', '兩碼紙別'],
                                    columns='年月',
                                    values='ConsPT',
                                    aggfunc='sum',
                                    fill_value=0
                                ).reset_index()

            df_Cost_sheet_details_elec_catrgory = df_Cost_sheet_details.loc[(df_Cost_sheet_details['Schsnm'] == '電力費') & (df_Cost_sheet_details['兩碼紙別'].isna())
                                      ,['ConsPT','年月','機台','大類別']]\
                                .pivot_table(index=['機台', '大類別'],
                                    columns='年月',
                                    values='ConsPT',
                                    aggfunc='sum',
                                    fill_value=0
                                ).reset_index()                     
            
            result_json = {
                "data": {
                    'df_Cost_sheet_details_fuel_ptype':df_Cost_sheet_details_fuel_ptype.to_dict(orient='records'),
                    'df_Cost_sheet_details_fuel_catrgory':df_Cost_sheet_details_fuel_catrgory.to_dict(orient='records'),
                    'df_Cost_sheet_details_elec_ptype':df_Cost_sheet_details_elec_ptype.to_dict(orient='records'),
                    'df_Cost_sheet_details_elec_catrgory':df_Cost_sheet_details_elec_catrgory.to_dict(orient='records')                    
                }
            }   
            
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:


class monthly_Cost_sheet:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, year_month_From: str,mname: str,year: str,ptype2: str):
        startTime = time.time()
        
#         if not year_month_From:
#             return {'success': False, 'message': 'Missing year_month_From parameter'}   
#         if not mname:
#             return {'success': False, 'message': 'Missing mname parameter'}   

        if year and ptype2:
            model = 'year'
        elif not year and ptype2:
            return {'success': False, 'message': 'Missing year parameter'} 
        elif year and not ptype2:
            return {'success': False, 'message': 'Missing ptype2 parameter'} 
        elif year_month_From and mname:
            model = 'month'
        elif not year_month_From and mname:
            return {'success': False, 'message': 'Missing year_month_From parameter'} 
        elif year_month_From and not mname:
            return {'success': False, 'message': 'Missing mname parameter'}
        else:
            return {'success': False, 'message': 'Missing (year,ptype2) or (year_month_From,mname) parameter'}
        
        if model == 'month':
            srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
            with srv_SRVMESDBA1['create_engine'][0].connect() as conn:   
                sql =   """
                      SELECT *  FROM [CostSheet].[dbo].[Cost_sheet_details]
                      WHERE 年月 = """ + str(year_month_From) + """
                """
                query = conn.execute(text(sql))  
                df_Cost_sheet_details = pd.DataFrame([dict(i) for i in query])

                sql =   """
                      SELECT *  FROM [CostSheet].[dbo].[Cost_sheet_details_prod]
                      WHERE 年月 = """ + str(year_month_From) + """
                """
                query = conn.execute(text(sql))  
                df_Cost_sheet_details_prod = pd.DataFrame([dict(i) for i in query])    

            if (not df_Cost_sheet_details.empty) & (not df_Cost_sheet_details_prod.empty):
                df_Cost_sheet_simple_table_ptype = df_Cost_sheet_details.loc[(df_Cost_sheet_details['年月']==year_month_From) &                                                                             (df_Cost_sheet_details['機台']==mname) &                                          (
                                            (df_Cost_sheet_details['Code'].str.contains('COST')) | \
                                            (df_Cost_sheet_details['Schsnm'].isin(['纖維原料小計','填料小計','塗料小計','化工原料小計','直接原料合計']))
                                          )]\
                                                .pivot_table(index=['Code','Schsnm'],
                                                    columns='兩碼紙別',
                                                    values='CostPT',
                                                    aggfunc='sum',
                                                    fill_value=0
                                                ).reset_index()

                df_Cost_sheet_simple_table_category = df_Cost_sheet_details.loc[(df_Cost_sheet_details['年月']==year_month_From) &                                                                             (df_Cost_sheet_details['機台']==mname) &                                                                             (df_Cost_sheet_details['兩碼紙別'].isna()) &                                          (
                                            (df_Cost_sheet_details['Code'].str.contains('COST')) | \
                                            (df_Cost_sheet_details['Schsnm'].isin(['纖維原料小計','填料小計','塗料小計','化工原料小計','直接原料合計']))
                                          )]\
                                                .pivot_table(index=['Code','Schsnm'],
                                                    columns='大類別',
                                                    values='CostPT',
                                                    aggfunc='sum',
                                                    fill_value=0
                                                ).reset_index()
                
        elif model == 'year':
            srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
            with srv_SRVMESDBA1['create_engine'][0].connect() as conn: 
                sql =   """
                      SELECT *  FROM [CostSheet].[dbo].[Cost_sheet_details]
                      WHERE left(年月,4) = """ + str(year) + """ and 兩碼紙別 = '""" + str(ptype2) + """'
                """
                query = conn.execute(text(sql))  
                df_Cost_sheet_details = pd.DataFrame([dict(i) for i in query])


                sql =   """
                      SELECT *  FROM [CostSheet].[dbo].[Cost_sheet_details_prod]
                      WHERE left(年月,4) = """ + str(year) + """ and 兩碼紙別 = '""" + str(ptype2) + """'
                """
                query = conn.execute(text(sql))  
                df_Cost_sheet_details_prod = pd.DataFrame([dict(i) for i in query])

            if (not df_Cost_sheet_details.empty):
                if (ptype2 == 'KL') | (ptype2 == 'SL'):
                    df_Cost_sheet_details = df_Cost_sheet_details[df_Cost_sheet_details['機台']=='PM21'].copy()
                    df_Cost_sheet_details_prod = df_Cost_sheet_details_prod[df_Cost_sheet_details_prod['機台']=='PM21'].copy()
                elif str(ptype2)[0] == 'B':
                    df_Cost_sheet_details = df_Cost_sheet_details[df_Cost_sheet_details['機台']=='PM19'].copy()
                    df_Cost_sheet_details_prod = df_Cost_sheet_details_prod[df_Cost_sheet_details_prod['機台']=='PM19'].copy()                    
                
                df_Cost_sheet_simple_table_ptype = df_Cost_sheet_details.loc[(
                                            (df_Cost_sheet_details['Code'].str.contains('COST')) | \
                                            (df_Cost_sheet_details['Schsnm'].isin(['纖維原料小計','填料小計','塗料小計','化工原料小計','直接原料合計']))
                                          )]\
                                                .pivot_table(index=['Code','Schsnm'],
                                                    columns='年月',
                                                    values='CostPT',
                                                    aggfunc='sum',
                                                    fill_value=0
                                                ).reset_index()            

        # 自訂排序順序
        order = ["FB", "CY", "CT",'CH','','COST1','COST2','COST3','COST4','COST5','COST6','COST7','COST8','COST9','COST10',
                                          'COST11','COST12','COST13','COST14','COST15','COST16','COST17','COST18','COST19','COST20',
                                          'COST21','COST22','COST23','COST24']

        # 將欄位轉成 Categorical 並指定順序
        df_Cost_sheet_simple_table_ptype["Code"] = pd.Categorical(df_Cost_sheet_simple_table_ptype["Code"], categories=order, 
                                                                  ordered=True)
        df_Cost_sheet_simple_table_ptype = df_Cost_sheet_simple_table_ptype.sort_values("Code").reset_index(drop=True)

        divisor = 2204.62
        cols_to_divide = [col for col in df_Cost_sheet_simple_table_ptype.columns if col not in ['Code', 'Schsnm']]
        df_Cost_sheet_simple_table_ptype[cols_to_divide] = df_Cost_sheet_simple_table_ptype[cols_to_divide] / divisor
        
        if model == 'month':
            # 將欄位轉成 Categorical 並指定順序
            df_Cost_sheet_simple_table_category["Code"] = pd.Categorical(df_Cost_sheet_simple_table_category["Code"], categories=order, 
                                                                      ordered=True)
            df_Cost_sheet_simple_table_category = df_Cost_sheet_simple_table_category.sort_values("Code").reset_index(drop=True)

            divisor = 2204.62
            cols_to_divide = [col for col in df_Cost_sheet_simple_table_category.columns if col not in ['Code', 'Schsnm']]
            df_Cost_sheet_simple_table_category[cols_to_divide] = df_Cost_sheet_simple_table_category[cols_to_divide] / divisor   


            df_Cost_sheet_details_prod_ptype = df_Cost_sheet_details_prod.loc[((df_Cost_sheet_details_prod['年月']==year_month_From) &                                           (df_Cost_sheet_details_prod['機台']==mname)),
                                           ['大類別','兩碼紙別','生產量(噸)','纖維得率(%)','填料得率(%)','塗料得率(%)']]\
                                            .melt(
                                                id_vars=['大類別', '兩碼紙別'],  # 保留這些欄位不動
                                                value_vars=['生產量(噸)', '纖維得率(%)', '填料得率(%)', '塗料得率(%)'],  # 要展開的欄位
                                                var_name='指標',   # 新欄位名稱 (原來的欄位名)
                                                value_name='Schsnm'  # 新欄位名稱 (欄位的值)
                                            )\
                                            .pivot_table(index=['指標'],
                                                columns='兩碼紙別',
                                                values='Schsnm',
                                                aggfunc='sum',
                                                fill_value=0
                                            ).reset_index()


            df_Cost_sheet_details_prod_category = df_Cost_sheet_details_prod.loc[((df_Cost_sheet_details_prod['年月']==year_month_From) &                                           (df_Cost_sheet_details_prod['機台']==mname) & (df_Cost_sheet_details_prod['兩碼紙別'].isna())),
                                           ['大類別','兩碼紙別','生產量(噸)','纖維得率(%)','填料得率(%)','塗料得率(%)']]\
                                            .melt(
                                                id_vars=['大類別', '兩碼紙別'],  # 保留這些欄位不動
                                                value_vars=['生產量(噸)', '纖維得率(%)', '填料得率(%)', '塗料得率(%)'],  # 要展開的欄位
                                                var_name='指標',   # 新欄位名稱 (原來的欄位名)
                                                value_name='Schsnm'  # 新欄位名稱 (欄位的值)
                                            )\
                                            .pivot_table(index=['指標'],
                                                columns='大類別',
                                                values='Schsnm',
                                                aggfunc='sum',
                                                fill_value=0
                                            ).reset_index()         
            
        elif model =='year':
            df_Cost_sheet_details_prod_ptype = df_Cost_sheet_details_prod.loc[:,
                                                       ['年月','大類別','兩碼紙別','生產量(噸)','纖維得率(%)','填料得率(%)','塗料得率(%)']]\
                                                        .melt(
                                                            id_vars=['年月','大類別', '兩碼紙別'],  # 保留這些欄位不動
                                                            value_vars=['生產量(噸)', '纖維得率(%)', '填料得率(%)', '塗料得率(%)'],  # 要展開的欄位
                                                            var_name='指標',   # 新欄位名稱 (原來的欄位名)
                                                            value_name='Schsnm'  # 新欄位名稱 (欄位的值)
                                                        )\
                                                        .pivot_table(index=['指標'],
                                                            columns='年月',
                                                            values='Schsnm',
                                                            aggfunc='sum',
                                                            fill_value=0
                                                        ).reset_index()            
            


        # 自訂排序順序
        order = ["生產量(噸)", "纖維得率(%)", "填料得率(%)",'塗料得率(%)']

        # 將欄位轉成 Categorical 並指定順序
        df_Cost_sheet_details_prod_ptype["指標"] = pd.Categorical(df_Cost_sheet_details_prod_ptype["指標"], categories=order, 
                                                                  ordered=True)
        df_Cost_sheet_details_prod_ptype = df_Cost_sheet_details_prod_ptype.sort_values("指標").reset_index(drop=True)

        df_Cost_sheet_details_prod_ptype.rename(columns={'指標': 'Schsnm'},inplace = True)
        df_Cost_sheet_details_prod_ptype['Code'] = None
        
        if model == 'month':
            # 將欄位轉成 Categorical 並指定順序
            df_Cost_sheet_details_prod_category["指標"] = pd.Categorical(df_Cost_sheet_details_prod_category["指標"], categories=order, 
                                                                      ordered=True)
            df_Cost_sheet_details_prod_category = df_Cost_sheet_details_prod_category.sort_values("指標").reset_index(drop=True)

            df_Cost_sheet_details_prod_category.rename(columns={'指標': 'Schsnm'},inplace = True)
            df_Cost_sheet_details_prod_category['Code'] = None

        
            df_Cost_sheet_category = pd.concat([df_Cost_sheet_details_prod_category,df_Cost_sheet_simple_table_category],ignore_index=True)
            df_Cost_sheet_category = df_Cost_sheet_category.replace({pd.NA: None, np.nan: None})
            
        df_Cost_sheet_ptype = pd.concat([df_Cost_sheet_details_prod_ptype,df_Cost_sheet_simple_table_ptype],ignore_index=True)   
        df_Cost_sheet_ptype = df_Cost_sheet_ptype.replace({pd.NA: None, np.nan: None})

        def insert_row_before(df, target_code, schsnm_value):
            # 建立一筆新 row，除了 Schsnm / Code 之外都空字串
            new_row = {col: '' for col in df.columns}
            new_row['Schsnm'] = schsnm_value
            new_row['Code'] = ''

            # 找到 target_code 的位置
            idx = df.index[df['Code'] == target_code].tolist()
            if not idx:
                raise ValueError(f"Code {target_code} 不存在")
            insert_idx = idx[0]

            # 插入新 row
            df = pd.concat(
                [df.iloc[:insert_idx], pd.DataFrame([new_row]), df.iloc[insert_idx:]],
                ignore_index=True
            )
            return df

        # 在 COST9 前插入 Schsnm = 內銷
        df_Cost_sheet_ptype = insert_row_before(df_Cost_sheet_ptype, "COST9", "內銷")
        # 在 COST17 前插入 Schsnm = 外銷
        df_Cost_sheet_ptype = insert_row_before(df_Cost_sheet_ptype, "COST17", "外銷")
        
        if model == 'month':
            # 在 COST9 前插入 Schsnm = 內銷
            df_Cost_sheet_category = insert_row_before(df_Cost_sheet_category, "COST9", "內銷")
            # 在 COST17 前插入 Schsnm = 外銷
            df_Cost_sheet_category = insert_row_before(df_Cost_sheet_category, "COST17", "外銷")              

            result_json = {
                "data": {
                    'df_Cost_sheet_ptype': df_Cost_sheet_ptype.to_dict(orient='records'),
                    'df_Cost_sheet_category': df_Cost_sheet_category.to_dict(orient='records')
                }
            }
            
        elif model == 'year':
            result_json = {
                "data": {
                    'df_Cost_sheet_ptype': df_Cost_sheet_ptype.to_dict(orient='records')
                }
            }            
            
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json

