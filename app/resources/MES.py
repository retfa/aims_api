#!/usr/bin/env python
# coding: utf-8

# In[3]:


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


# In[2]:


import logging
logger = logging.getLogger(__name__)  # 取得和主程式共用的 logger


# In[2]:


import sqlalchemy

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


# In[4]:


class amreel_groupby_ptime:
    def __init__(self, servers):
        self.servers = servers    
    
    def fetch(self, stime: str, etime: str, mname: str, MachineCode: str):  
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'}
        
        if pd.isna(MachineCode):
            MachineCode = -1
            
        if MachineCode == -1:
            
            srv_SRVMSDBA2 = self.servers['SRVMSDBA2'] 
            with srv_SRVMSDBA2['create_engine'][0].connect() as conn:            
                sql =   """
                SELECT *
                FROM
                (
                      SELECT 
                        bdate,
                        REPLACE(REPLACE(MachineName, '_Unit_Power_Consumption', ''),'PM','') AS mname,
                        Unit_Power_Consumption
                    FROM 
                    (
                        SELECT 
                            dateadd(HOUR,-8,[fta_dtm]) as bdate,
                            PM21_Unit_Power_Consumption,
                            PM20_Unit_Power_Consumption,
                            PM19_Unit_Power_Consumption,
                            PM18_Unit_Power_Consumption
                        FROM [FTA_EN_Summary].[dbo].[FTA_APower_Unit_Consumption_DAY]
                        where dateadd(HOUR,-8,[fta_dtm]) >='"""+ str(stime) +"""' 
                        AND dateadd(HOUR,-8,[fta_dtm]) <= '"""+ str(etime) +"""'
                    ) AS source_table
                    UNPIVOT 
                    (
                        Unit_Power_Consumption FOR MachineName IN 
                        (
                            PM21_Unit_Power_Consumption,
                            PM20_Unit_Power_Consumption,
                            PM19_Unit_Power_Consumption,
                            PM18_Unit_Power_Consumption
                        )
                    ) AS unpivoted
                ) t
                where 1=1
                AND mname = '"""+ str(mname) +"""'
                """       
                query = conn.execute(text(sql))
                df_Unit_Power = pd.DataFrame([dict(i) for i in query])
                
                sql =   """
                SELECT *
                FROM
                (
                      SELECT 
                        bdate,
                        REPLACE(REPLACE(MachineName, '_Unit_Steam_Consumption', ''),'PM','') AS mname,
                        Unit_Steam_Consumption
                    FROM 
                    (
                        SELECT 
                            dateadd(HOUR,-8,[fta_dtm]) as bdate
                          ,[PM21_Unit_Steam_Consumption]
                          ,[PM20_Unit_Steam_Consumption]
                          ,[PM19_Unit_Steam_Consumption]
                          ,[PM18_Unit_Steam_Consumption]
                        FROM [FTA_EN_Summary].[dbo].[FTA_Steam_Unit_Consumption_DAY]
                        where dateadd(HOUR,-8,[fta_dtm]) >='"""+ str(stime) +"""' 
                        AND dateadd(HOUR,-8,[fta_dtm]) <= '"""+ str(etime) +"""'
                    ) AS source_table
                    UNPIVOT 
                    (
                        Unit_Steam_Consumption FOR MachineName IN 
                        (
                            PM21_Unit_Steam_Consumption,
                            PM20_Unit_Steam_Consumption,
                            PM19_Unit_Steam_Consumption,
                            PM18_Unit_Steam_Consumption
                        )
                    ) AS unpivoted
                ) t
                where 1=1
                AND mname = '"""+ str(mname) +"""'
                """       
                query = conn.execute(text(sql))
                df_Unit_Steam = pd.DataFrame([dict(i) for i in query])                            
    
            srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
            with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:    
                sql =   """
                
            SELECT bdate,MACHINE_NO,ptype,gramg,
            ISNULL(SUM([TRANSACTION_QUANTITY]),0) + ISNULL(SUM([SECONDARY_TRANSACTION_QUANTITY]),0) AS [TRANSACTION_QUANTITY] FROM
            (
                SELECT bdate,MACHINE_NO,ptype,gramg / 10.0 AS gramg,[TRANSACTION_QUANTITY],[TRANSACTION_UOM],
                CASE WHEN [ITEM_NO] LIKE '%K' AND [SECONDARY_UOM_CODE] = 'RE' 
                    THEN ROUND([gramg] * CAST([length] AS BIGINT) * (CAST([width] AS BIGINT)) * 0.00071117 / 1000 ,2) * [SECONDARY_TRANSACTION_QUANTITY] * 0.0004535924
                    WHEN [SECONDARY_UOM_CODE] = 'RE' 
                    THEN ROUND([gramg] * CAST([length] AS BIGINT) * CAST([width] AS BIGINT) * 0.000110231 / 1000  ,2) * [SECONDARY_TRANSACTION_QUANTITY] * 0.0004535924
                    ELSE [SECONDARY_TRANSACTION_QUANTITY] END as [SECONDARY_TRANSACTION_QUANTITY],
                    [SECONDARY_UOM_CODE]
                FROM
                (
                    SELECT [PROCESS_CODE]
                          ,[SERVER_CODE]
                          ,[BATCH_ID]
                          ,[BATCH_LINE_ID]
                          ,[STATUS_CODE]
                          ,[ORGCODE]
                          ,[RXID]
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
                      FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST]
                      WHERE 1=1
                      AND convert(datetime,convert(varchar(10), Dateadd(HOUR,-8,[TRANSACTION_DATE]), 120),120) between '"""+ str(stime) +"""' AND '"""+ str(etime) +"""'
                      AND MACHINE_NO = '"""+ str(mname) +"""'
                      AND SUBINVENTORY_CODE <> 'SFG'
                ) t
                where 1=1
                --AND ptype = 'B300'
                --GROUP BY MACHINE_NO,ptype,gramg
                --HAVING SUM([TRANSACTION_QUANTITY]) IS NOT NULL
            ) m
            GROUP BY bdate,MACHINE_NO,ptype,gramg
            ORDER BY bdate,MACHINE_NO,ptype,gramg
                """       
                query = conn.execute(text(sql))
                df_inventory = pd.DataFrame([dict(i) for i in query])
                
            srv_SRVAD2 = self.servers['SRVAD2'] 
            with srv_SRVAD2['create_engine'][0].connect() as conn:            
                sql =   """

                DECLARE @sdate varchar(10) = '"""+ str(stime) +"""'
                DECLARE @edate varchar(10) = '"""+ str(etime) +"""'
                DECLARE @ssdate varchar(10) = convert(varchar(10), dateadd(DAY,-1,@sdate), 121)

                ;With raw_data as
                (
                    SELECT *
                    FROM
                    (
                        SELECT *,
                        CASE WHEN pm='W' AND mname IN('21','R1') Then '0塗佈前'
                        WHEN pm='W' AND mname = 'C1' Then '1壓光前'
                        WHEN pm='W' AND mname IN ('EA','EB','EC') Then '2複捲前(含中間倉)'
                        WHEN pm='W' AND mname IN ('WA','WB') Then '3截切前'
                        WHEN pm='T' AND mname IN('20','RT') Then '0塗佈前'
                        WHEN pm='T' AND mname = 'C7' Then '1壓光前'
                        WHEN pm='T' AND mname IN ('EO','EP','EQ','ER') Then '2複捲前(含中間倉)'
                        WHEN pm='T' AND mname IN ('WE','WW') Then '3截切前'
                        WHEN pm='S' AND mname IN('19') Then '0塗佈前'
                        WHEN pm='S' AND mname = 'C2' Then '1壓光前'
                        WHEN pm='S' AND mname IN ('E3') Then '2複捲前(含中間倉)'
                        WHEN pm='S' AND mname IN ('WS','WJ') Then '3截切前'
                        WHEN pm='R' AND mname IN('18') Then '0塗佈前'
                        WHEN pm='R' AND mname IN ('WR') Then '3截切前'
                        END AS 機台
                        FROM
                        (
                            --SRVAD2
                            select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation from [pm21].[dbo].[adbuff_prod] where cbdate between @ssdate and @edate
                            UNION ALL
                            select cbdate,pm,mname,ptype,gramg,pgramg,weigh,nstation from [pm21].[dbo].[adwind_prod] where cbdate between @ssdate and @edate
                            UNION ALL
                            select cbdate,pm,mname,ptype,gramg,pgramg,(rewt*re/2204.62),nstation as weigh from [pm21].[dbo].[adstock_prod] where cbdate between @ssdate and @edate
                        ) t
                        WHERE 1=1
                        --AND nstation NOT IN ('R','TS') 
                        AND gramg is not null
                        --AND ptype = 'KL00' AND pgramg = '58'
                    ) m
                    where 機台 is not null
                ), equivalent as
                (
                    SELECT TOP 999999 cbdate,pm,ptype,pgramg,(ISNULL([0塗佈前],0)) AS 塗前,(ISNULL([1壓光前],0)+ISNULL([2複捲前(含中間倉)],0)+ISNULL([3截切前],0)) AS 塗後
                    FROM (
                        SELECT cbdate,pm,ptype,pgramg,機台,weigh
                        FROM raw_data
                    ) AS source
                    PIVOT (
                        SUM(weigh)
                        FOR 機台 IN ([0塗佈前],[1壓光前],[2複捲前(含中間倉)],[3截切前])
                    ) AS pivot_table
                    ORDER BY cbdate,pm,ptype,pgramg
                )
                SELECT t.cbdate AS bdate,
                CASE WHEN t.pm = 'W' THEN '21'
                WHEN t.pm = 'T' THEN '20'
                WHEN t.pm = 'S' THEN '19'
                WHEN t.pm = 'R' THEN '18' END AS mname
                ,t.ptype,t.pgramg,
                t.塗前 AS 塗前期末在產品,t.塗後 AS 塗後期末在產品,
                e.塗前 AS 塗前期初在產品,e.塗後 AS 塗後期初在產品
                FROM
                (
                    SELECT *,dateadd(DAY,-1,cbdate) AS ccbdate
                    FROM equivalent
                ) t 
                left join equivalent e ON t.ccbdate = e.cbdate and t.pm = e.pm and t.ptype = e.ptype and t.pgramg = e.pgramg
                WHERE e.cbdate is not null
                """       
                query = conn.execute(text(sql))
                df_equivalent = pd.DataFrame([dict(i) for i in query])
                

            srv_SRVAD1 = self.servers['SRVAD1'] 
            with srv_SRVAD1['create_engine'][0].connect() as conn:                
                sql =   """
                
                    ;With a_m_day_report AS
                    (
                        select a.mname,a.relno, a.ptype,a.gramg,a.rgramg,a.recycle,
                        ((a.gramg - a.ctqty)*(1-(a.asnum/100))*a.lenth*a.width)/1000000 / 1000 AS pulp_qty
                        FROM   [SRVAD1].[AMIS].[dbo].[amreel] a 
                        WHERE   a.bdate  between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                    ),
                    merge_data as
                    (               
                        SELECT 
                            bdate,
                            ptype,
                            mname,
                            relno,                        
                            [mat_id_erp],
                            [cost_id],                    
                            [schsnm],
                            '' AS SourceNo,
                            NULL AS Stage,
                            NULL AS Type,
                            SUM([use_qty]) AS [use_qty],
                            1 AS Unit,
                            1 AS Rate
                        FROM
                        (
                            SELECT [adpulp].[mname]
                                  ,[adpulp].[relno]
                                  ,[amreel].[ptype]
                                  ,[sno]
                                  ,[ftype]
                                  ,[adpulp].[cost_id]
                                  ,[adpulp].[scost_id]
                                  ,[adpulp].[mat_id]
                                  ,[item]
                                  ,[adpulp].[bdate]
                                  ,[PER]
                                  ,[qty]
                                  ,[wqty]
                                  ,a_m_day_report.pulp_qty * [PER] * 1.0 / 100 AS [use_qty]
                                  ,[admatcode_gp].mat_id_erp
                                  ,[admatcode_gp].[schsnm]
                              FROM [SRVAD1].[AMIS].[dbo].[adpulp]
                              LEFT JOIN [SRVAD1].[AMIS].[dbo].[admatcode_gp] ON [adpulp].cost_id = [admatcode_gp].cost_id AND [adpulp].[scost_id] = [admatcode_gp].[scost_id]
                              LEFT JOIN [SRVAD1].[AMIS].[dbo].[amreel] ON [amreel].relno = [adpulp].relno
                              LEFT JOIN a_m_day_report ON a_m_day_report.relno = [adpulp].relno
                              WHERE [adpulp].bdate  between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                        ) t
                        GROUP BY bdate,mname,ptype,relno,scost_id,[mat_id_erp],[cost_id],[schsnm]
                    )                
                    SELECT y_mk,bdate,mname,ptype_two,ptype,gramg,pgramg,SUM(ptime) AS ptime
                    ,ISNULL(sum(case when recycle='N' then weigh end),0) as wei1
                    ,ISNULL(sum(case when recycle='N' then [adchem_tqty_d] end),0) as [weigh_adchem]
                    ,ISNULL(sum(case when recycle='N' then [adcoat_tqty_d] end),0) as [weigh_adcoat]
                    ,ISNULL(sum(case when recycle='N' then [adpulp_tqty_d] end),0) as [weigh_adpulp]
                    ,ISNULL(sum(case when recycle='N' then [amfill_tqty_d] end),0) as [weigh_cy]
                    FROM
                    (
                        SELECT 
                            m.*,
                            [adcoat].[adcoat_tqty_d],
                            [adchem].[adchem_tqty_d],
                            [adpulp].[adpulp_tqty_d],
                            [amfill].[amfill_tqty_d]
                        FROM
                        (
                            SELECT [mname]
                                  ,[y_mk]
                                  ,[relno]
                                  ,[runno]
                                  ,LEFT([ptype],2) AS ptype_two
                                  ,[ptype]
                                  ,[pclass]
                                  ,[gramg]
                                  ,[pgramg]
                                  ,[rgramg]
                                  ,[pdate]
                                  ,[bdate]
                                  ,[btime]
                                  ,[ptime]
                                  ,[weigh]
                                  ,[recycle]
                              FROM [AMIS].[dbo].[amreel]
                              WHERE bdate >='"""+ str(stime) +"""' AND bdate <= '"""+ str(etime) +"""'
                              AND mname = '"""+ str(mname) +"""'
                        ) m
                        LEFT JOIN (
                          SELECT pm,mname,bdate,relno,SUM([tqty_d]) AS [adcoat_tqty_d]
                          FROM [AMIS].[dbo].[adcoat]
                          WHERE bdate >='"""+ str(stime) +"""' AND bdate <= '"""+ str(etime) +"""'
                          AND mname = '"""+ str(mname) +"""'
                          GROUP BY pm,mname,bdate,relno
                        ) [adcoat] ON [adcoat].relno = m.relno
                        LEFT JOIN (
                          SELECT mname,bdate,relno,SUM([tqty_d]) AS [adchem_tqty_d]
                          FROM [AMIS].[dbo].[adchem]
                          WHERE bdate >='"""+ str(stime) +"""' AND bdate <= '"""+ str(etime) +"""'
                          GROUP BY mname,bdate,relno
                        ) [adchem] ON [adchem].relno = m.relno
                        LEFT JOIN (
                            SELECT bdate,ptype,mname,relno,SUM([use_qty]) AS [adpulp_tqty_d] FROM merge_data
                            WHERE mname="""+ str(mname) +"""
                            GROUP BY bdate,ptype,mname,relno
                        ) [adpulp] ON [adpulp].relno = m.relno
                        LEFT JOIN (
                            select pm,mname,bdate,sum(fweigh) AS [amfill_tqty_d] from amfill
                            WHERE bdate >='"""+ str(stime) +"""' AND bdate <= '"""+ str(etime) +"""'
                            AND mname = '"""+ str(mname) +"""'
                            GROUP BY bdate,pm,mname
                        ) [amfill] ON [amfill].bdate = m.bdate                        
                    ) t
                    GROUP BY y_mk,bdate,mname,ptype_two,ptype,gramg,pgramg
                    ORDER BY y_mk,bdate,mname,ptype_two,ptype,gramg,pgramg
                """       
                query = conn.execute(text(sql))
                df_result = pd.DataFrame([dict(i) for i in query])

            if not df_result.empty:
                df_result["weigh_adpulp"] = np.where(
                    df_result["wei1"].notna() & (df_result["wei1"] != 0),
                    (df_result["weigh_adpulp"].astype(float) / df_result["wei1"].astype(float)).round(3),
                    np.nan
                )                
                
                df_result["weigh_adchem"] = np.where(
                    df_result["wei1"].notna() & (df_result["wei1"] != 0),
                    (df_result["weigh_adchem"].astype(float) / df_result["wei1"].astype(float)).round(3),
                    np.nan
                )
                df_result["weigh_adcoat"] = np.where(
                    df_result["wei1"].notna() & (df_result["wei1"] != 0),
                    (df_result["weigh_adcoat"].astype(float) / df_result["wei1"].astype(float)).round(3),
                    np.nan
                )
                
                df_result['weigh_percentage'] = (df_result["wei1"].astype(float) / df_result.groupby('bdate')['wei1'].transform('sum').astype(float) * 100.0).round(3)
                
                
                df_result["product_capacity_daily"] = (df_result["ptime"].astype(float) / 1440.0 * 100).round(3)
                
                df_inventory['bdate'] = df_inventory['bdate'].astype(object)
                df_result['bdate'] = df_result['bdate'].astype(object)

                df_result = df_result.merge(df_inventory,on=['bdate','ptype','gramg'],how='left')
                df_result['inventory'] = df_result['TRANSACTION_QUANTITY']
                df_result['inventory'] = df_result['inventory'].fillna(0)
                df_result.drop(['MACHINE_NO','TRANSACTION_QUANTITY'],axis=1,inplace=True)
                
                df_equivalent['bdate'] = df_equivalent['bdate'].astype(object)
                
                df_result = df_result.merge(df_equivalent,on=['bdate','mname','ptype','pgramg'],how='left')
                df_result['塗前期初在產品'] = df_result['塗前期初在產品'].fillna(0)
                df_result['塗後期初在產品'] = df_result['塗後期初在產品'].fillna(0)                
                df_result['塗前期末在產品'] = df_result['塗前期末在產品'].fillna(0)
                df_result['塗後期末在產品'] = df_result['塗後期末在產品'].fillna(0)
                
                df_result["weigh_equivalent"] = (df_result['塗前期末在產品'] - df_result['塗前期初在產品']) +                 (df_result['塗後期末在產品'] - df_result['塗後期初在產品']) + df_result['inventory'].astype(float)

                df_Unit_Power['bdate'] = df_Unit_Power['bdate'].astype(object)
                df_Unit_Steam['bdate'] = df_Unit_Steam['bdate'].astype(object)

                df_result = df_result.merge(df_Unit_Power,on=['bdate','mname'],how='left').merge(df_Unit_Steam,on=['bdate','mname'],how='left')
                df_result['weigh_electricity'] = df_result['Unit_Power_Consumption'] / df_result['weigh_percentage'] *                                                       df_result['product_capacity_daily']
                df_result['weigh_steam'] = df_result['Unit_Steam_Consumption'] / df_result['weigh_percentage'] *                                                       df_result['product_capacity_daily']                              
                df_result['weigh_electricity'] = df_result['weigh_electricity'].fillna(0)
                df_result['weigh_steam'] = df_result['weigh_steam'].fillna(0)
                
                
                df_result = df_result[df_result['wei1']>0]
                df_result["bdate"] = df_result["bdate"].astype(str)
                df_result["wei1"] = df_result["wei1"].astype(float).round(3).astype(str)
                df_result["gramg"] = df_result["gramg"].astype(str)
                df_result["pgramg"] = df_result["pgramg"].astype(str)
                df_result["weigh_adchem"] = df_result["weigh_adchem"].astype(str)
                df_result["weigh_adcoat"] = df_result["weigh_adcoat"].astype(str)
                df_result["weigh_adpulp"] = df_result["weigh_adpulp"].astype(str)
                df_result["inventory"] = df_result["inventory"].astype(str)
                df_result["weigh_steam"] = df_result["weigh_steam"].astype(str)
                df_result["weigh_electricity"] = df_result["weigh_electricity"].astype(str)
                df_result["weigh_cy"] = df_result["weigh_cy"].astype(str)
                df_result["weigh_equivalent"] = df_result["weigh_equivalent"].astype(str)
             

                result_json = [{"bdate": b, "mname": m, "ptype_two":p_t, "ptype":p, "gramg":g,"pgramg":pg,"ptime": t, "weigh": w,
                               "weigh_adchem": w_adchem,"weigh_adcoat": w_adcoat,"weigh_adpulp": w_adpulp,
                               "weigh_percentage": w_p,"weigh_equivalent": w_eq,"product_capacity_daily": pcd,"inventory": inv,
                                "weigh_steam": w_s,"weigh_electricity": w_el,"weigh_cy": w_cy}
                               for b,m,p_t,p,g,pg,t,w,w_adchem,w_adcoat,w_adpulp,
                               w_p,w_eq,pcd,inv,w_s,w_el,w_cy
                               in zip(df_result["bdate"], 
                                              df_result["mname"],df_result["ptype_two"],
                                              df_result["ptype"], df_result["gramg"], df_result["pgramg"],
                                              df_result["ptime"],df_result["wei1"],
                                              df_result["weigh_adchem"],df_result["weigh_adcoat"],df_result["weigh_adpulp"],
                        df_result["weigh_percentage"], df_result["weigh_equivalent"],df_result["product_capacity_daily"],
                        df_result["inventory"],df_result["weigh_steam"],df_result["weigh_electricity"],df_result["weigh_cy"])]
                
            else:
                result_json = []

        elif MachineCode in ['R1','RT']:
            params = (MachineCode, stime, etime, "N")
            query = "EXEC a_r_day_report_sp @mname=?, @sdate=?, @edate=?, @shft=?"

            with df_SERVER_SRVAD1['create_engine'][0].begin() as conn:
                df_result = pd.read_sql(query, conn, params=params)             
                
            if not df_result.empty:
                df_result["pgramg"] = df_result["sgramg"]
                
                df_result["ptype_two"] = df_result["ptype"].astype(str).str[:2]

                df_result["pdate"] = pd.to_datetime(df_result["pdate"])  # 轉換為 datetime
                df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期          

                df_result = df_result.groupby(['bdate','ptype_two','ptype','gramg','pgramg'])                    .agg(ptime=('ptime','sum'), wei1=('weigh', 'sum'))                    .reset_index()        

                df_result = df_result[df_result['wei1']>0]
                df_result["bdate"] = df_result["bdate"].astype(str)
                df_result["wei1"] = df_result["wei1"].astype(float).round(3).astype(str)
                df_result["gramg"] = df_result["gramg"].astype(str)
                df_result["pgramg"] = df_result["pgramg"].astype(str)
                df_result['mname'] = MachineCode
                df_result["weigh_adchem"] = 0.0
                df_result["weigh_adcoat"] = 0.0
                df_result["weigh_adpulp"] = 0.0
                
                df_result["weigh_percentage"] = 0.0
                df_result["weigh_equivalent"] = 0.0
                df_result["product_capacity_daily"] = 0.0
                df_result["inventory"] = 0.0
                df_result["weigh_steam"] = 0.0
                df_result["weigh_electricity"] = 0.0
                df_result["weigh_cy"] = 0.0                

                result_json = [{"bdate": b, "mname": m, "ptype_two":p_t, "ptype":p, "gramg":g,"pgramg":pg,"ptime": t, "weigh": w,
                               "weigh_adchem": w_adchem,"weigh_adcoat": w_adcoat,"weigh_adpulp": w_adpulp,
                               "weigh_percentage": w_p,"weigh_equivalent": w_eq,"product_capacity_daily": pcd,"inventory": inv,
                                "weigh_steam": w_s,"weigh_electricity": w_el,"weigh_cy": w_cy} 
                               for b,m,p_t,p,g,pg,t,w,w_adchem,w_adcoat,w_adpulp,
                               w_p,w_eq,pcd,inv,w_s,w_el,w_cy in zip(df_result["bdate"], 
                                      df_result["mname"],df_result["ptype_two"],
                                      df_result["ptype"], df_result["gramg"], df_result["pgramg"],
                                      df_result["ptime"],df_result["wei1"],
                                      df_result["weigh_adchem"],df_result["weigh_adcoat"],df_result["weigh_adpulp"],
                        df_result["weigh_percentage"], df_result["weigh_equivalent"],df_result["product_capacity_daily"],
                        df_result["inventory"],df_result["weigh_steam"],df_result["weigh_electricity"],df_result["weigh_cy"])]  
            else:
                result_json = []                
                
        elif MachineCode in ['C1','C2','C7']:
            params = (MachineCode, stime, etime, "N")
            query = "EXEC a_c_day_report_sp @mname=?, @sdate=?, @edate=?, @shft=?"

            with df_SERVER_SRVAD1['create_engine'][0].begin() as conn:
                df_result = pd.read_sql(query, conn, params=params)
                
            with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:
                sql =   """
                      SELECT pm,mname,bdate,relno,SUM([tqty_d]) AS [adcoat_tqty_d]
                      FROM [AMIS].[dbo].[adcoat]
                      WHERE bdate >='"""+ str(stime) +"""' AND bdate <= '"""+ str(etime) +"""'
                      AND mname = '"""+ str(MachineCode) +"""'
                      GROUP BY pm,mname,bdate,relno
                """       
                query = conn.execute(text(sql))
                df_adcoat = pd.DataFrame([dict(i) for i in query])

            if not df_result.empty:
                df_result = df_result.merge(df_adcoat,on='relno',how='left')
                
                df_result["ptype_two"] = df_result["ptype"].astype(str).str[:2]

                df_result["pdate"] = pd.to_datetime(df_result["pdate"])  # 轉換為 datetime
                df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期

                df_result = df_result.groupby(['bdate','ptype_two','ptype','gramg','pgramg'])                    .agg(ptime=('ptime','sum'), wei1=('weigh', 'sum'), weigh_adcoat=('adcoat_tqty_d', 'sum'))                    .reset_index()

                df_result["weigh_adcoat"] = np.where(
                    df_result["wei1"].notna() & (df_result["wei1"] != 0),
                    (df_result["weigh_adcoat"].astype(float) / df_result["wei1"].astype(float)).round(3),
                    np.nan
                )

                df_result = df_result[df_result['wei1']>0]
                df_result["bdate"] = df_result["bdate"].astype(str)
                df_result["wei1"] = df_result["wei1"].astype(float).round(3).astype(str)
                df_result["gramg"] = df_result["gramg"].astype(str)
                df_result["pgramg"] = df_result["pgramg"].astype(str)
                df_result['mname'] = MachineCode
                df_result["weigh_adchem"] = 0.0
                df_result["weigh_adcoat"] = df_result["weigh_adcoat"].astype(str)
                df_result["weigh_adpulp"] = 0.0
                
                df_result["weigh_percentage"] = 0.0
                df_result["weigh_equivalent"] = 0.0
                df_result["product_capacity_daily"] = 0.0
                df_result["inventory"] = 0.0
                df_result["weigh_steam"] = 0.0
                df_result["weigh_electricity"] = 0.0
                df_result["weigh_cy"] = 0.0                

                result_json = [{"bdate": b, "mname": m, "ptype_two":p_t, "ptype":p, "gramg":g,"pgramg":pg,"ptime": t, "weigh": w,
                               "weigh_adchem": w_adchem,"weigh_adcoat": w_adcoat,"weigh_adpulp": w_adpulp,
                               "weigh_percentage": w_p,"weigh_equivalent": w_eq,"product_capacity_daily": pcd,"inventory": inv,
                                "weigh_steam": w_s,"weigh_electricity": w_el,"weigh_cy": w_cy} 
                               for b,m,p_t,p,g,pg,t,w,w_adchem,w_adcoat,w_adpulp,
                               w_p,w_eq,pcd,inv,w_s,w_el,w_cy in zip(df_result["bdate"], df_result["mname"],df_result["ptype_two"],
                                          df_result["ptype"], df_result["gramg"], df_result["pgramg"],
                                          df_result["ptime"],df_result["wei1"],
                                          df_result["weigh_adchem"],df_result["weigh_adcoat"],df_result["weigh_adpulp"],
                        df_result["weigh_percentage"], df_result["weigh_equivalent"],df_result["product_capacity_daily"],
                        df_result["inventory"],df_result["weigh_steam"],df_result["weigh_electricity"],df_result["weigh_cy"])]  
            else:
                result_json = [] 
        elif MachineCode in ['EA','EB','EC','ED','E3','EO','EP','EQ','ER']:
            params = (MachineCode, mname, stime, etime, "N")
            query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

            with df_SERVER_SRVAD1['create_engine'][0].begin() as conn:
                df_result = pd.read_sql(query, conn, params=params)
                
            if not df_result.empty:
                df_result["pgramg"] = df_result["sgramg"]
                
                df_result["ptype_two"] = df_result["ptype"].astype(str).str[:2]

                df_result["pdate"] = pd.to_datetime(df_result["pdate"])  # 轉換為 datetime
                df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期          

                df_result = df_result.groupby(['bdate','ptype_two','ptype','gramg','pgramg'])                    .agg(ptime=('ptime','sum'), wei1=('weigh', 'sum'))                    .reset_index()        

                df_result = df_result[df_result['wei1']>0]
                df_result["bdate"] = df_result["bdate"].astype(str)
                df_result["wei1"] = df_result["wei1"].astype(float).round(3).astype(str)
                df_result["gramg"] = df_result["gramg"].astype(str)
                df_result["pgramg"] = df_result["pgramg"].astype(str)
                df_result['mname'] = MachineCode
                df_result["weigh_adchem"] = 0.0
                df_result["weigh_adcoat"] = 0.0
                df_result["weigh_adpulp"] = 0.0    
                
                df_result["weigh_percentage"] = 0.0
                df_result["weigh_equivalent"] = 0.0
                df_result["product_capacity_daily"] = 0.0
                df_result["inventory"] = 0.0
                df_result["weigh_steam"] = 0.0
                df_result["weigh_electricity"] = 0.0
                df_result["weigh_cy"] = 0.0                

                result_json = [{"bdate": b, "mname": m, "ptype_two":p_t, "ptype":p, "gramg":g,"pgramg":pg,"ptime": t, "weigh": w,
                               "weigh_adchem": w_adchem,"weigh_adcoat": w_adcoat,"weigh_adpulp": w_adpulp,
                               "weigh_percentage": w_p,"weigh_equivalent": w_eq,"product_capacity_daily": pcd,"inventory": inv,
                                "weigh_steam": w_s,"weigh_electricity": w_el,"weigh_cy": w_cy} 
                               for b,m,p_t,p,g,pg,t,w,w_adchem,w_adcoat,w_adpulp,
                               w_p,w_eq,pcd,inv,w_s,w_el,w_cy in zip(df_result["bdate"], df_result["mname"],df_result["ptype_two"],
                                          df_result["ptype"], df_result["gramg"],df_result["pgramg"],
                                          df_result["ptime"],df_result["wei1"],
                                          df_result["weigh_adchem"],df_result["weigh_adcoat"],df_result["weigh_adpulp"],
                        df_result["weigh_percentage"], df_result["weigh_equivalent"],df_result["product_capacity_daily"],
                        df_result["inventory"],df_result["weigh_steam"],df_result["weigh_electricity"],df_result["weigh_cy"])]  
            else:
                result_json = []      
        elif MachineCode in ['WA','WB','WR','WS','WJ','WE','WW']:
            with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:
                sql =   """
                select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
                                    c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
                                    (case when a.patch='S' then a.blenth-a.plenth else a.blenth+a.plenth end) as blenth,
                                    (case when a.patch='S' then a.barea-a.parea else a.barea+a.parea end) as barea,
                                    (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
                                    (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
                                FROM  amwind a 
                                INNER JOIN ampaper b ON a.ptype = b.ptype 
                                Left JOIN amrunt c ON a.runno = c.runno  
                                WHERE  a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""'
                                GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk 
                                ORDER BY  a.pdate, a.relno
                """       
                query = conn.execute(text(sql))
                df_result = pd.DataFrame([dict(i) for i in query])  
                
            if not df_result.empty:
                df_result["ptype_two"] = df_result["ptype"].astype(str).str[:2]

                df_result["pdate"] = pd.to_datetime(df_result["pdate"])  # 轉換為 datetime
                df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期          

                df_result = df_result.groupby(['bdate','ptype_two','ptype','gramg','pgramg'])                    .agg(ptime=('ptime','sum'), wei1=('weigh', 'sum'))                    .reset_index()        

                df_result = df_result[df_result['wei1']>0]
                df_result["bdate"] = df_result["bdate"].astype(str)
                df_result["wei1"] = df_result["wei1"].astype(float).round(3).astype(str)
                df_result["gramg"] = df_result["gramg"].astype(str)
                df_result["pgramg"] = df_result["pgramg"].astype(str)
                df_result['mname'] = MachineCode
                df_result["weigh_adchem"] = 0.0
                df_result["weigh_adcoat"] = 0.0
                df_result["weigh_adpulp"] = 0.0
                
                df_result["weigh_percentage"] = 0.0
                df_result["weigh_equivalent"] = 0.0
                df_result["product_capacity_daily"] = 0.0
                df_result["inventory"] = 0.0
                df_result["weigh_steam"] = 0.0
                df_result["weigh_electricity"] = 0.0
                df_result["weigh_cy"] = 0.0                

                result_json = [{"bdate": b, "mname": m, "ptype_two":p_t, "ptype":p, "gramg":g,"pgramg":pg,"ptime": t, "weigh": w,
                               "weigh_adchem": w_adchem,"weigh_adcoat": w_adcoat,"weigh_adpulp": w_adpulp,
                               "weigh_percentage": w_p,"weigh_equivalent": w_eq,"product_capacity_daily": pcd,"inventory": inv,
                                "weigh_steam": w_s,"weigh_electricity": w_el,"weigh_cy": w_cy} 
                               for b,m,p_t,p,g,pg,t,w,w_adchem,w_adcoat,w_adpulp,
                               w_p,w_eq,pcd,inv,w_s,w_el,w_cy in zip(df_result["bdate"], df_result["mname"],df_result["ptype_two"],
                                      df_result["ptype"], df_result["gramg"],df_result["pgramg"], 
                                      df_result["ptime"],df_result["wei1"],
                                      df_result["weigh_adchem"],df_result["weigh_adcoat"],df_result["weigh_adpulp"],
                        df_result["weigh_percentage"], df_result["weigh_equivalent"],df_result["product_capacity_daily"],
                        df_result["inventory"],df_result["weigh_steam"],df_result["weigh_electricity"],df_result["weigh_cy"])]  
            else:
                result_json = []                     
                

        ExecutionTime = time.time() - startTime

        return result_json


# In[5]:


class ERP_SR_summary:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, stime: str, etime: str, mname: str, start_Time: str, end_Time: str, detail: bool = False, ERPtime: bool = False):
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'}    

        if mname == "18":
            mname_t = "'WR','WJ','WK'"
            sub_r = "'R'"
        elif mname == "19":
            mname_t = "'WS','WJ','WK'"
            sub_r = "'S'"
        elif mname == "20":
            mname_t = "'WE','WW'"
            sub_r = "'T'"
        elif mname == "21":
            mname_t = "'WA','WB'"
            sub_r = "'W'"
        else:
            pass

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn: 
            if not start_Time or ERPtime:
                sql =   """
                    SELECT mes_no, batch_no
                    FROM (
                        SELECT 
                            mes_no, 
                            batch_no, 
                            ROW_NUMBER() OVER (PARTITION BY mes_no ORDER BY batch_no) AS rn
                        FROM [10.10.1.27].[YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST]
                        WHERE substring(batch_no, 10, 2) = 'SR' 
                          AND status_code = 'S'
                    ) t
                    WHERE rn = 1 AND mes_no IN (
                        select distinct runno from adwind 
                        where mname in("""+ str(mname_t) +""") and substring(runno,1,1) = """+ str(sub_r) +"""
                        and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                        and prod not in('3','5','6') 
                    )          
                """       
                query = conn.execute(text(sql))  
                df_batch_no = pd.DataFrame([dict(i) for i in query])           

                sql =   """
                SELECT 
                    *,
                    '4'+ptype+pclass+RIGHT('000' + CAST(CAST(CAST(pgramg AS FLOAT) * 10 AS INT)  AS VARCHAR), 5)+prodn AS itemNo            
                FROM
                (
                    SELECT *,CASE 
                        WHEN x_yn = 'Y' AND pstatus = '成品' THEN 'A4FG'
                        WHEN pstatus = '成品' THEN 
                            CASE 
                                WHEN '"""+ str(mname) +"""' = '18' AND prodn <> 'R' THEN 'A3FG'
                                WHEN '"""+ str(mname) +"""' = '19' AND prodn <> 'R' THEN 'A2FG'
                                WHEN ('"""+ str(mname) +"""' = '20' AND prodn <> 'R') 
                                     OR ('"""+ str(mname) +"""' = '18' AND prodn <> 'R') 
                                     OR ('"""+ str(mname) +"""' = '19' AND prodn <> 'R') THEN 'A6FG'
                                WHEN '"""+ str(mname) +"""' = '21' AND prodn <> 'R' THEN 'A7FG'   
                                ELSE NULL  -- 如果沒有符合條件，不設值
                            END
                        ELSE 'FTA.SFG.SR.PM' + CAST('"""+ str(mname) +"""' AS VARCHAR)  -- 非 "成品" 情況，store 依 mname 設定
                    END AS store
                    FROM
                    (
                        select *,
                        CASE 
                            WHEN prod IN ('1','9') THEN  
                                CASE 
                                    WHEN LEFT(ptype, 1) = 'H' AND CAST(width AS FLOAT) >= 100 
                                        THEN RIGHT('00' + CAST(CAST(width AS INT) AS VARCHAR), 4) + 'RL00'
                                    WHEN LEFT(ptype, 1) = 'H' OR CAST(width AS FLOAT) < 100 
                                        THEN 
                                            CASE 
                                                WHEN RIGHT(CAST(CAST(width10 AS INT) AS VARCHAR), 1) = '5' 
                                                    THEN RIGHT('00' + CAST(CAST(width10 AS INT) - 1 AS VARCHAR), 3) + 'KRL00'
                                                WHEN RIGHT(CAST(CAST(width10 AS INT) AS VARCHAR), 1) = '8' 
                                                    THEN RIGHT('00' + CAST(CAST(width10 AS INT) - 2 AS VARCHAR), 3) + 'KRL00'
                                                ELSE RIGHT('00' + CAST(CAST(width10 AS INT) AS VARCHAR), 3) + 'KRL00'
                                            END
                                    ELSE 
                                        RIGHT('00' + CAST(CAST(width AS INT) AS VARCHAR), 4) + 'RL00'
                                END
                            WHEN prod IN ('2', '4', '7', '8') THEN 'R'
                            ELSE NULL 
                        END AS prodn,
                        CASE WHEN prod = 1 THEN '成品'
                        WHEN prod = 2 Then '裁切'
                        WHEN prod = 4 Then '中倉'
                        WHEN prod = 7 Then '分條'
                        WHEN prod = 8 Then '含浸' 
                        WHEN prod = 9 THEN '成品' END AS pstatus

                        FROM
                        (
                            select 
                                CASE 
                                    WHEN ABS(width * 10) - FLOOR(ABS(width * 10)) = 0.5
                                        THEN 
                                            CASE 
                                                WHEN FLOOR(ABS(width * 10)) % 2 = 0 
                                                    THEN FLOOR(width * 10)
                                                ELSE CEILING(width * 10)
                                            END
                                    ELSE ROUND(width * 10, 0)
                                END AS width10,
                            adwind.*,b.chsnm
                            from adwind 
                            inner join ampaper b on adwind.ptype = b.ptype
                            where mname in("""+ str(mname_t) +""") and substring(runno,1,1) = """+ str(sub_r) +"""
                            and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                            and prod not in('3','5','6') 
                            --order by runno, prod, ptype, pclass, width, pgramg, x_yn, relno, swinno     
                        ) n
                    ) m 
                ) t
                WHERE store NOT LIKE '%SR%'
                """                       
            else:
                sql =   """
                    SELECT mes_no, batch_no
                    FROM (
                        SELECT 
                            mes_no, 
                            batch_no, 
                            ROW_NUMBER() OVER (PARTITION BY mes_no ORDER BY batch_no) AS rn
                        FROM [10.10.1.27].[YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST]
                        WHERE substring(batch_no, 10, 2) = 'SR' 
                          AND status_code = 'S'
                    ) t
                    WHERE rn = 1 AND mes_no IN (
                        select distinct runno from adwind 
                        where mname in("""+ str(mname_t) +""") and substring(runno,1,1) = """+ str(sub_r) +"""
                        and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                        and pdate between '"""+ str(start_Time) +"""' and '"""+ str(end_Time) +"""' 
                        and prod not in('3','5','6') 
                    )          
                """       
                query = conn.execute(text(sql))  
                df_batch_no = pd.DataFrame([dict(i) for i in query])           

                sql =   """
                SELECT 
                    *,
                    '4'+ptype+pclass+RIGHT('000' + CAST(CAST(CAST(pgramg AS FLOAT) * 10 AS INT)  AS VARCHAR), 5)+prodn AS itemNo            
                FROM
                (
                    SELECT *,CASE 
                        WHEN x_yn = 'Y' AND pstatus = '成品' THEN 'A4FG'
                        WHEN pstatus = '成品' THEN 
                            CASE 
                                WHEN '"""+ str(mname) +"""' = '18' AND prodn <> 'R' THEN 'A3FG'
                                WHEN '"""+ str(mname) +"""' = '19' AND prodn <> 'R' THEN 'A2FG'
                                WHEN ('"""+ str(mname) +"""' = '20' AND prodn <> 'R') 
                                     OR ('"""+ str(mname) +"""' = '18' AND prodn <> 'R') 
                                     OR ('"""+ str(mname) +"""' = '19' AND prodn <> 'R') THEN 'A6FG'
                                WHEN '"""+ str(mname) +"""' = '21' AND prodn <> 'R' THEN 'A7FG'   
                                ELSE NULL  -- 如果沒有符合條件，不設值
                            END
                        ELSE 'FTA.SFG.SR.PM' + CAST('"""+ str(mname) +"""' AS VARCHAR)  -- 非 "成品" 情況，store 依 mname 設定
                    END AS store
                    FROM
                    (
                        select *,
                        CASE 
                            WHEN prod IN ('1','9') THEN  
                                CASE 
                                    WHEN LEFT(ptype, 1) = 'H' AND CAST(width AS FLOAT) >= 100 
                                        THEN RIGHT('00' + CAST(CAST(width AS INT) AS VARCHAR), 4) + 'RL00'
                                    WHEN LEFT(ptype, 1) = 'H' OR CAST(width AS FLOAT) < 100 
                                        THEN 
                                            CASE 
                                                WHEN RIGHT(CAST(CAST(width10 AS INT) AS VARCHAR), 1) = '5' 
                                                    THEN RIGHT('00' + CAST(CAST(width10 AS INT) - 1 AS VARCHAR), 3) + 'KRL00'
                                                WHEN RIGHT(CAST(CAST(width10 AS INT) AS VARCHAR), 1) = '8' 
                                                    THEN RIGHT('00' + CAST(CAST(width10 AS INT) - 2 AS VARCHAR), 3) + 'KRL00'
                                                ELSE RIGHT('00' + CAST(CAST(width10 AS INT) AS VARCHAR), 3) + 'KRL00'
                                            END
                                    ELSE 
                                        RIGHT('00' + CAST(CAST(width AS INT) AS VARCHAR), 4) + 'RL00'
                                END
                            WHEN prod IN ('2', '4', '7', '8') THEN 'R'
                            ELSE NULL 
                        END AS prodn,
                        CASE WHEN prod = 1 THEN '成品'
                        WHEN prod = 2 Then '裁切'
                        WHEN prod = 4 Then '中倉'
                        WHEN prod = 7 Then '分條'
                        WHEN prod = 8 Then '含浸' 
                        WHEN prod = 9 THEN '成品' END AS pstatus

                        FROM
                        (
                            select 
                                CASE 
                                    WHEN ABS(width * 10) - FLOOR(ABS(width * 10)) = 0.5
                                        THEN 
                                            CASE 
                                                WHEN FLOOR(ABS(width * 10)) % 2 = 0 
                                                    THEN FLOOR(width * 10)
                                                ELSE CEILING(width * 10)
                                            END
                                    ELSE ROUND(width * 10, 0)
                                END AS width10,
                            adwind.*,b.chsnm
                            from adwind 
                            inner join ampaper b on adwind.ptype = b.ptype
                            where mname in("""+ str(mname_t) +""") and substring(runno,1,1) = """+ str(sub_r) +"""
                            and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                            and pdate between '"""+ str(start_Time) +"""' and '"""+ str(end_Time) +"""' 
                            and prod not in('3','5','6') 
                            --order by runno, prod, ptype, pclass, width, pgramg, x_yn, relno, swinno     
                        ) n
                    ) m 
                ) t
                WHERE store NOT LIKE '%SR%'
                """       
            query = conn.execute(text(sql))  
            df_adwind = pd.DataFrame([dict(i) for i in query])
            
            if df_adwind.empty:
                result_json = {
                    "summary": {
                        "weigh_count_total": 0,
                        "weigh_sum_total": 0
                    },
                    "groups": []
                }                        

                ExecutionTime = time.time() - startTime

                return result_json                
            

#             sql =   """
#                 SELECT runno,MAX(replace(core_tube_d,'"','')) AS core_tube_d ,MAX(roll_type) AS roll_type,
#                 MAX(CASE WHEN x_yn = 'Y' THEN SOLD_TO_CUST_NAME ELSE '' END) AS SOLD_TO_CUST_NAME
#                 FROm adrunt_edit_temp 
#                 where y_mk>=YEAR('"""+ str(stime) +"""') AND len(roll_type)>0
#                 group by runno
#             """       
            
            sql =   """
                SELECT runno,MAX(roll_type) AS roll_type
                FROm adrunt_edit_temp 
                where y_mk>=YEAR('"""+ str(stime) +"""') AND len(roll_type)>0
                group by runno
            """                   
            
            query = conn.execute(text(sql))  
            df_roll_type_old = pd.DataFrame([dict(i) for i in query])  # ABD020I1                  

            itemNos = df_adwind['winno'].unique().tolist()
            # 變成 'A','B','C' 格式
            in_clause = ",".join(f"'{x}'" for x in itemNos)
            sql = f"""
                  SELECT winno,
                  --face AS roll_type, 
                  diam AS core_tube_d,NULL AS SOLD_TO_CUST_NAME
                  FROM [SRVADA1].[ERP-A].[dbo].[AprirolltagT]
                  WHERE winno IN ({in_clause})
            """            
            query = conn.execute(text(sql))  
            df_roll_type = pd.DataFrame([dict(i) for i in query])  # ABD020I1          
            
            
        srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
        with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:
            in_list = ", ".join([f"''{item}''" for item in list(df_adwind['itemNo'].unique())])  # 注意雙單引號
            sql = f"""
            SELECT * FROM OPENQUERY(ERPDB, 'SELECT ITEM_NUMBER,CATALOG_ELEM_VAL_010 FROM XXIFV050_ITEMS_FTA_V WHERE ITEM_NUMBER IN ({in_list})')
            """        
            query = conn.execute(text(sql))  
            df_CHPGTERPDBAAR01 = pd.DataFrame([dict(i) for i in query]) 
            
            winno_list = ", ".join([f"'{item}'" for item in list(df_adwind['winno'].unique())])
            sql_td = f"""
            SELECT 
                [LOT_NUMBER],
                [TRANSACTION_DATE]
            FROM (
                -- 這裡就是子查詢，先把編號（RowNum）算出來
                SELECT 
                    [LOT_NUMBER],
                    [TRANSACTION_DATE],
                    ROW_NUMBER() OVER (PARTITION BY [LOT_NUMBER] ORDER BY [TRANSACTION_DATE] DESC) AS RowNum
                FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST]
                WHERE [LOT_NUMBER] IN ({winno_list})
                  AND [PREVIOUS_RXID] IS NULL
                  AND [STATUS_CODE] = 'S'
            ) AS RankedTransactions -- 子查詢在大多數 SQL 資料庫中必須取一個別名（Alias）
            WHERE RowNum = 1; -- 外層再過濾出第一筆
            """
            query = conn.execute(text(sql_td))
            df_TRANSACTION_DATE = pd.DataFrame([dict(i) for i in query])
            
        df_adwind = df_adwind.merge(df_CHPGTERPDBAAR01,left_on = 'itemNo', right_on = 'ITEM_NUMBER',how='left')
        df_adwind['store'] = np.where(
            df_adwind['CATALOG_ELEM_VAL_010'] == 'NCR',
            'A6FG',
            df_adwind['store']
        )               
        
        df_adwind['note'] = np.where(
            df_adwind['CATALOG_ELEM_VAL_010'].notna(),
            '',
            '料號不存在，請檢查資料正確性'
        )
        
        # 將 key 欄位都轉為大寫 20250721新增
        df_adwind['runno'] = df_adwind['runno'].str.upper()
        df_batch_no['mes_no'] = df_batch_no['mes_no'].str.upper()
        # 20250721新增
        
        df_adwind_merge = df_adwind.merge(df_batch_no,left_on = 'runno',right_on='mes_no',how = 'left')
        
        df_adwind_merge = df_adwind_merge.merge(df_roll_type_old,left_on = 'runno',right_on='runno',how = 'left')
        
        if df_roll_type.empty:
            df_adwind_merge['core_tube_d'] = ''
            df_adwind_merge['SOLD_TO_CUST_NAME'] = ''
        else:
            df_adwind_merge = df_adwind_merge.merge(df_roll_type,left_on = 'winno',right_on='winno',how = 'left')
        
        df_adwind_merge['roll_type'] = df_adwind_merge['roll_type'].fillna('')  
        df_adwind_merge['core_tube_d'] = df_adwind_merge['core_tube_d'].fillna('') 
        df_adwind_merge['SOLD_TO_CUST_NAME'] = df_adwind_merge['SOLD_TO_CUST_NAME'].fillna('')
        
        if not df_TRANSACTION_DATE.empty:
            df_adwind_merge = df_adwind_merge.merge(df_TRANSACTION_DATE, left_on='winno', right_on='LOT_NUMBER', how='left', suffixes=('', '_td'))
            df_adwind_merge = df_adwind_merge.drop(columns=['LOT_NUMBER'], errors='ignore')
            df_adwind_merge['TRANSACTION_DATE'] = df_adwind_merge['TRANSACTION_DATE'].fillna('').astype(str)
        else:
            df_adwind_merge['TRANSACTION_DATE'] = ''

        if ERPtime and start_Time:
            df_adwind_merge = df_adwind_merge[
                (df_adwind_merge['TRANSACTION_DATE'] >= start_Time) &
                (df_adwind_merge['TRANSACTION_DATE'] <= end_Time)
            ]
        
#         # 匯出csv 測試用
#         df_adwind_merge.loc[:,['relno','winno','runno','ptype','pclass',
#                                'pgramg','width','lenth','pdate','chsnm','pstatus','store','itemNo',
#                                'batch_no','roll_type','core_tube_d','SOLD_TO_CUST_NAME','weigh']]\
#         .sort_values(by=['pdate','winno'])\
#         .to_csv('df_adwind_merge.csv',index=0,encoding='big5')

        if detail:
            if not df_adwind_merge.empty:
                df_adwind_merge['bdate'] = df_adwind_merge['bdate'].astype(str)
                df_adwind_merge['pdate'] = df_adwind_merge['pdate'].astype(str)
                df_adwind_merge['weigh'] = df_adwind_merge['weigh'].astype(float)
                for k in df_adwind_merge.columns:
                    if k not in ['weigh']:
                        df_adwind_merge[k] = df_adwind_merge[k].astype(str)

                group_date_col = 'TRANSACTION_DATE' if ERPtime else 'pdate'
                groups = []
                grouped_bdate = df_adwind_merge.groupby(group_date_col)

                for group_date, df_bdate in grouped_bdate:
                    weigh_count_subtotal = len(df_bdate)
                    weigh_sum_subtotal = round(df_bdate["weigh"].sum(), 3)

                    runno_groups = []
                    grouped_runno = df_bdate.groupby('runno')

                    for runno, df_runno in grouped_runno:
                        weigh_count_runno_subtotal = len(df_runno)
                        weigh_sum_runno_subtotal = round(df_runno["weigh"].sum(), 3)

                        items = [{
                            "relno": row["relno"],
                            "winno": row["winno"],
                            "pdate": row["pdate"],
                            "bdtm": row["bdtm"],
                            "batch_no": row["batch_no"],
                            "ptype": row["ptype"],
                            "pgramg": row["pgramg"],
                            "lenth": row["lenth"],
                            "width": row["width"],
                            "pclass": row["pclass"],
                            "store": row["store"],
                            "weigh": str(row["weigh"]),
                            "roll_type": row["roll_type"],
                            "core_tube_d": row["core_tube_d"],
                            "SOLD_TO_CUST_NAME": row["SOLD_TO_CUST_NAME"],
                            "TRANSACTION_DATE": row["TRANSACTION_DATE"],
                            "note": row["note"],
                        } for _, row in df_runno.iterrows()]

                        runno_groups.append({
                            "runno": runno,
                            "weigh_count_runno_subtotal": weigh_count_runno_subtotal,
                            "weigh_sum_runno_subtotal": weigh_sum_runno_subtotal,
                            "items": items
                        })

                    groups.append({
                        "bdate": group_date,
                        "weigh_count_subtotal": weigh_count_subtotal,
                        "weigh_sum_subtotal": weigh_sum_subtotal,
                        "runno_groups": runno_groups
                    })

                result_json = {
                    "summary": {
                        "weigh_count_total": len(df_adwind_merge),
                        "weigh_sum_total": round(df_adwind_merge["weigh"].sum(), 3)
                    },
                    "groups": groups
                }
            else:
                result_json = {
                    "summary": {
                        "weigh_count_total": 0,
                        "weigh_sum_total": 0
                    },
                    "groups": []
                }
        else:
            df_result = df_adwind_merge.groupby(['runno','bdate', 'batch_no', 'ptype', 'pgramg','lenth','width','pclass',
                                                 'store','core_tube_d','roll_type','SOLD_TO_CUST_NAME'])\
                .agg(weigh_sum=('weigh', 'sum'), weigh_count=('weigh', 'count'),note=('note', 'max'),
                     TRANSACTION_DATE=('TRANSACTION_DATE', 'max'))\
                .reset_index()

            for k in list(df_result.columns):
                if k not in ['weigh_count','weigh_sum']:
                    df_result[k] = df_result[k].astype(str)
                else:
                    df_result[k] = df_result[k].astype(float)
            
            if not df_result.empty:
                # 確保 T 欄位為 float
                df_result["weigh_count"] = df_result["weigh_count"].astype(float)
                df_result["weigh_sum"] = df_result["weigh_sum"].astype(float)

                groups = []
                grouped_bdate = df_result.groupby('bdate')

                for bdate, df_bdate in grouped_bdate:
                    weigh_count_subtotal = round(df_bdate["weigh_count"].sum(), 2)
                    weigh_sum_subtotal = round(df_bdate["weigh_sum"].sum(), 3)

                    runno_groups = []
                    grouped_runno = df_bdate.groupby('runno')

                    for runno, df_runno in grouped_runno:
                        weigh_count_runno_subtotal = round(df_runno["weigh_count"].sum(), 2)
                        weigh_sum_runno_subtotal = round(df_runno["weigh_sum"].sum(), 3)

                        items = [{
                            "batch_no": row["batch_no"],
                            "ptype": row["ptype"],
                            "pgramg": row["pgramg"],
                            "lenth": row["lenth"],
                            "width": row["width"],
                            "pclass": row["pclass"],
                            "store": row["store"],
                            "weigh_count": str(row["weigh_count"]),
                            "weigh_sum": str(row["weigh_sum"]),
                            "roll_type": row["roll_type"],
                            "core_tube_d": row["core_tube_d"],
                            "SOLD_TO_CUST_NAME": row["SOLD_TO_CUST_NAME"],
                            "TRANSACTION_DATE": row["TRANSACTION_DATE"],
                            "note": row["note"],
                        } for _, row in df_runno.iterrows()]

                        runno_groups.append({
                            "runno": runno,
                            "weigh_count_runno_subtotal": weigh_count_runno_subtotal,
                            "weigh_sum_runno_subtotal": weigh_sum_runno_subtotal,
                            "items": items
                        })

                    groups.append({
                        "bdate": bdate,
                        "weigh_count_subtotal": weigh_count_subtotal,
                        "weigh_sum_subtotal": weigh_sum_subtotal,
                        "runno_groups": runno_groups
                    })

                # 全體總結
                result_json = {
                    "summary": {
                        "weigh_count_total": round(df_result["weigh_count"].sum(), 2),
                        "weigh_sum_total": round(df_result["weigh_sum"].sum(), 3)
                    },
                    "groups": groups
                }            

            else:
                result_json = {
                    "summary": {
                        "weigh_count_total": 0,
                        "weigh_sum_total": 0
                    },
                    "groups": []
                }                        

        ExecutionTime = time.time() - startTime

        return result_json


# In[6]:


class ERP_SH_summary:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, mname: str, start_Time: str, end_Time: str, detail: bool = False, ERPtime: bool = False):  
        startTime = time.time()

        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        
        if mname == "18":
            sub_r = "'R'"
        elif mname == "19":
            sub_r = "'S'"
        elif mname == "20":
            sub_r = "'T'"
        elif mname == "21":
            sub_r = "'W'"
        else:
            pass        

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            sql =   """
                SELECT runno,
                --MAX(CASE WHEN x_yn = 'Y' THEN SOLD_TO_CUST_NAME ELSE '' END) AS SOLD_TO_CUST_NAME
                NULL AS SOLD_TO_CUST_NAME
                FROm adrunt_edit_temp 
                where y_mk>=YEAR('"""+ str(stime) +"""') AND len(roll_type)=0
                group by runno
            """
            query = conn.execute(text(sql))  
            df_SOLD_TO_CUST_NAME = pd.DataFrame([dict(i) for i in query])  # ABD020I1
            
            if not start_Time or ERPtime:
                sql =   """
                ;with raw_data as
                (
                    select 
                        a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                    from openquery([10.10.1.27],
                    '
                    SELECT * 
                    FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] 
                    WHERE Creation_date >= DATEADD(m,-6,getdate()) AND substring(batch_no,10,2) = ''SH'' AND status_code = ''S''
                    ') a
                    inner join adpack b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass <> 'A') --and substring(batch_no,10,2) = 'SH'
                    where substring(runno,1,1) = """+ str(sub_r) +""" and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and b.re <> 0 --and a.status_code = 'S'

                    union

                    select a.batch_no, stkno, mname, bdate, runno, bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                    from openquery([10.10.1.27],
                    '
                    SELECT * 
                    FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] 
                    WHERE Creation_date >= dateadd(m,-6,getdate()) AND substring(batch_no,10,2) = ''SH'' AND status_code = ''S''
                    ') a
                    inner join adsel b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass in ('A','P') or b.pclass is null) --and substring(batch_no,10,2) = 'SH'
                    where substring(runno,1,1) = """+ str(sub_r) +""" and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and b.nstation not in('SP','WP','WH','SH') and b.re <> 0 --and a.status_code = 'S'
                    --order by runno, batch_no, ptype, psize1, psize2, x_yn, bhno            
                )
                SELECT *,rewt*re*0.0004535924 AS T,
                CASE WHEN x_yn = 'Y' Then '外銷' ELSE '內銷' END AS ExportSales,
                CASE WHEN x_yn = 'Y' Then 'A4FG'
                WHEN x_yn = 'N' AND substring(runno,1,1) = 'R' THEN 'A3FG'
                WHEN x_yn = 'N' AND substring(runno,1,1) = 'S' THEN 'A2FG'
                WHEN x_yn = 'N' AND substring(runno,1,1) = 'W' THEN 'A1FG'
                END AS store,
                '4'+ptype+pclass+RIGHT('000' + CAST(CAST(CAST(pgramg AS FLOAT) * 10 AS INT)  AS VARCHAR), 5)+psize1+psize2 AS itemNo
                FROM raw_data

                """       
            else:
                sql =   """
                ;with raw_data as
                (
                    select 
                        a.batch_no, stkno, mname, bdate, runno, b.bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                    from openquery([10.10.1.27],
                    '
                    SELECT * 
                    FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] 
                    WHERE Creation_date >= DATEADD(m,-6,getdate()) AND substring(batch_no,10,2) = ''SH'' AND status_code = ''S''
                    ') a
                    inner join adpack b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass <> 'A') --and substring(batch_no,10,2) = 'SH'
                    inner join (select bhno,pdate from ampack) c on c.bhno = b.bhno
                    where substring(runno,1,1) = """+ str(sub_r) +""" and b.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and b.re <> 0 --and a.status_code = 'S'
                    and c.pdate between '"""+ str(start_Time) +"""' and '"""+ str(end_Time) +"""' 

                    union

                    select a.batch_no, stkno, mname, bdate, runno, b.bhno, ptype, pgramg, psize1, psize2, pack, rewt, re, grain, pclass, x_yn, bdtm
                    from openquery([10.10.1.27],
                    '
                    SELECT * 
                    FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] 
                    WHERE Creation_date >= dateadd(m,-6,getdate()) AND substring(batch_no,10,2) = ''SH'' AND status_code = ''S''
                    ') a
                    inner join adsel b on b.runno = a.mes_no and (b.pclass = substring(a.item_no,6,1) or b.pclass in ('A','P') or b.pclass is null) --and substring(batch_no,10,2) = 'SH'
                    inner join (select bhno,pdate from amsel) c on c.bhno = b.bhno
                    where substring(runno,1,1) = """+ str(sub_r) +""" and b.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and b.nstation not in('SP','WP','WH','SH') and b.re <> 0 --and a.status_code = 'S'
                    and c.pdate between '"""+ str(start_Time) +"""' and '"""+ str(end_Time) +"""'
                    --order by runno, batch_no, ptype, psize1, psize2, x_yn, bhno            
                )
                SELECT *,rewt*re*0.0004535924 AS T,
                CASE WHEN x_yn = 'Y' Then '外銷' ELSE '內銷' END AS ExportSales,
                CASE WHEN x_yn = 'Y' Then 'A4FG'
                WHEN x_yn = 'N' AND substring(runno,1,1) = 'R' THEN 'A3FG'
                WHEN x_yn = 'N' AND substring(runno,1,1) = 'S' THEN 'A2FG'
                WHEN x_yn = 'N' AND substring(runno,1,1) = 'W' THEN 'A1FG'
                END AS store,
                '4'+ptype+pclass+RIGHT('000' + CAST(CAST(CAST(pgramg AS FLOAT) * 10 AS INT)  AS VARCHAR), 5)+psize1+psize2 AS itemNo
                FROM raw_data

                """                       
            query = conn.execute(text(sql))  
            df_result = pd.DataFrame([dict(i) for i in query])
            
        if not df_result.empty:
            srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
            with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:            
                in_list = ", ".join([f"'{item}'" for item in list(df_result['batch_no'].unique())])  # 注意雙單引號
                sql = f"""
                SELECT distinct [BATCH_NO],[LOT_NUMBER]
                FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST] WHERE [BATCH_NO] IN ({in_list})
                """        
                query = conn.execute(text(sql))
                df_CHPGTERPDBAAR01_BATCH_NO = pd.DataFrame([dict(i) for i in query])
                
                stkno_list = ", ".join([f"'{item}'" for item in list(df_result['stkno'].unique())])
                sql_td = f"""
                SELECT
                    [LOT_NUMBER],
                    [TRANSACTION_DATE]
                FROM (
                    -- 這裡就是子查詢，先把編號（RowNum）算出來
                    SELECT 
                        [LOT_NUMBER],
                        [TRANSACTION_DATE],
                        ROW_NUMBER() OVER (PARTITION BY [LOT_NUMBER] ORDER BY [TRANSACTION_DATE] DESC) AS RowNum
                    FROM [YFYPRODERP_FTA].[dbo].[XXIF_CHP_P250_IN_MMT_PROD_ST]
                    WHERE [LOT_NUMBER] IN ({stkno_list})
                      AND [PREVIOUS_RXID] IS NULL
                      AND [STATUS_CODE] = 'S'
                ) AS RankedTransactions -- 子查詢在大多數 SQL 資料庫中必須取一個別名（Alias）
                WHERE RowNum = 1; -- 外層再過濾出第一筆
                """
                query = conn.execute(text(sql_td))
                df_TRANSACTION_DATE = pd.DataFrame([dict(i) for i in query])                
            
            if not df_CHPGTERPDBAAR01_BATCH_NO.empty:
                df_result = df_result.merge(df_CHPGTERPDBAAR01_BATCH_NO,left_on = ['batch_no','stkno'], 
                                            right_on = ['BATCH_NO','LOT_NUMBER'],how='left')

                df_result['LOT_NUMBER'] = df_result['LOT_NUMBER'].fillna('').astype(str)
            else:
                df_result['LOT_NUMBER'] = ''
                
            if not df_TRANSACTION_DATE.empty:
                df_result = df_result.merge(df_TRANSACTION_DATE, left_on='stkno', right_on='LOT_NUMBER', how='left', suffixes=('', '_td'))
                df_result = df_result.drop(columns=['LOT_NUMBER_td'], errors='ignore')
                df_result['TRANSACTION_DATE'] = df_result['TRANSACTION_DATE'].fillna('').astype(str)
            else:
                df_result['TRANSACTION_DATE'] = ''

            if ERPtime and start_Time:
                df_result = df_result[
                    (df_result['TRANSACTION_DATE'] >= start_Time) &
                    (df_result['TRANSACTION_DATE'] <= end_Time)
                ]

            if detail:
                df_result = df_result.merge(df_SOLD_TO_CUST_NAME,left_on = 'runno',right_on='runno',how = 'left')
                df_result['SOLD_TO_CUST_NAME'] = df_result['SOLD_TO_CUST_NAME'].fillna('')

                srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
                with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:            
                    in_list = ", ".join([f"''{item}''" for item in list(df_result['itemNo'].unique())])  # 注意雙單引號
                    sql = f"""
                SELECT * FROM OPENQUERY(ERPDB, 'SELECT ITEM_NUMBER,CATALOG_ELEM_VAL_010,CATALOG_ELEM_VAL_060 FROM XXIFV050_ITEMS_FTA_V WHERE ITEM_NUMBER IN ({in_list})')
                """        
                    query = conn.execute(text(sql))  
                    df_CHPGTERPDBAAR01 = pd.DataFrame([dict(i) for i in query])
                    
                df_result = df_result.merge(df_CHPGTERPDBAAR01,left_on = 'itemNo', right_on = 'ITEM_NUMBER',how='left')

                df_result['note'] = np.where(
                    df_result['CATALOG_ELEM_VAL_010'].notna(),
                    np.where(
                        df_result['LOT_NUMBER'].ne(''),
                        '',
                        '資料未轉移至JT'
                    ),
                    '料號不存在，請檢查資料正確性'
                )                

                df_result['rewt'] = np.where(
                    df_result['CATALOG_ELEM_VAL_060'].notna(),
                    df_result['CATALOG_ELEM_VAL_060'],
                    df_result['rewt']
                )

                df_result['T'] = df_result['re'].astype(float) * df_result['rewt'].astype(float) * 0.0004535924   
                
                df_result['bdate'] = df_result['bdate'].astype(str)
                df_result['re'] = df_result['re'].astype(float)
                df_result['T'] = df_result['T'].astype(float)
                for k in list(df_result.columns):
                    if k not in ['re', 'T']:
                        df_result[k] = df_result[k].astype(str)
                
                group_date_col = 'TRANSACTION_DATE' if ERPtime else 'bdtm'
                groups = []
                grouped_bdate = df_result.groupby(group_date_col)

                for group_date, df_bdate in grouped_bdate:
                    re_subtotal = round(df_bdate["re"].sum(), 2)
                    T_subtotal = round(df_bdate["T"].sum(), 3)

                    runno_groups = []
                    grouped_runno = df_bdate.groupby('runno')

                    for runno, df_runno in grouped_runno:
                        re_runno_subtotal = round(df_runno["re"].sum(), 2)
                        T_runno_subtotal = round(df_runno["T"].sum(), 3)

                        items = [{
                            "bhno": row["bhno"],
                            "stkno": row["stkno"],
                            "bdtm": row["bdtm"],
                            "batch_no": row["batch_no"],
                            "ptype": row["ptype"],
                            "pgramg": row["pgramg"],
                            "psize1": row["psize1"],
                            "psize2": row["psize2"],
                            "store": row["store"],
                            "ExportSales": row["ExportSales"],
                            "pclass": row["pclass"],
                            "rewt": row["rewt"],
                            "re": str(row["re"]),
                            "T": str(row["T"]),
                            "LOT_NUMBER": row["LOT_NUMBER"],
                            "TRANSACTION_DATE": row["TRANSACTION_DATE"],
                            "SOLD_TO_CUST_NAME": row["SOLD_TO_CUST_NAME"],
                            "note": row["note"]
                        } for _, row in df_runno.iterrows()]

                        runno_groups.append({
                            "runno": runno,
                            "re_runno_subtotal": re_runno_subtotal,
                            "T_runno_subtotal": T_runno_subtotal,
                            "items": items
                        })

                    groups.append({
                        "bdate": group_date,
                        "re_subtotal": re_subtotal,
                        "T_subtotal": T_subtotal,
                        "runno_groups": runno_groups
                    })
                    
                result_json = {
                    "summary": {
                        "re_total": round(df_result["re"].sum(), 2),
                        "T_total": round(df_result["T"].sum(), 3)
                    },
                    "groups": groups
                }

            else:
                df_result = (
                    df_result.groupby([
                        'runno', 'bdate', 'batch_no', 'ptype', 'pgramg', 'psize1', 'psize2',
                        'store', 'ExportSales', 'pclass', 'rewt', 'itemNo'
                    ], as_index=False)
                    .agg({
                        're': 'sum',
                        'T': 'sum',
                        # count(*) 對應到 group 內的筆數，可以選任何欄位 count
                        'mname': 'count',
                        'LOT_NUMBER': 'max',
                        'TRANSACTION_DATE': 'max'
                    })
                    .rename(columns={'mname': 'amount'})  # 把剛剛 count 的欄位改名為 amount
                )             

                df_result = df_result[
                    ['runno','bdate','batch_no','ptype','pgramg','psize1','psize2','store',
                     'ExportSales','pclass','rewt','itemNo','re','T','amount','LOT_NUMBER','TRANSACTION_DATE']
                ]         

                df_result = df_result.merge(df_SOLD_TO_CUST_NAME,left_on = 'runno',right_on='runno',how = 'left')
                df_result['SOLD_TO_CUST_NAME'] = df_result['SOLD_TO_CUST_NAME'].fillna('')

                srv_CHPGTERPDBAAR01 = self.servers['CHPGTERPDBAAR01'] 
                with srv_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:            
                    in_list = ", ".join([f"''{item}''" for item in list(df_result['itemNo'].unique())])  # 注意雙單引號
                    sql = f"""
                SELECT * FROM OPENQUERY(ERPDB, 'SELECT ITEM_NUMBER,CATALOG_ELEM_VAL_010,CATALOG_ELEM_VAL_060 FROM XXIFV050_ITEMS_FTA_V WHERE ITEM_NUMBER IN ({in_list})')
                """        
                    query = conn.execute(text(sql))  
                    df_CHPGTERPDBAAR01 = pd.DataFrame([dict(i) for i in query]) 

                df_result = df_result.merge(df_CHPGTERPDBAAR01,left_on = 'itemNo', right_on = 'ITEM_NUMBER',how='left')

                df_result['note'] = np.where(
                    df_result['CATALOG_ELEM_VAL_010'].notna(),
                    np.where(
                        df_result['LOT_NUMBER'].ne(''),
                        '',
                        '資料未轉移至JT'
                    ),
                    '料號不存在，請檢查資料正確性'
                )

                df_result['rewt'] = np.where(
                    df_result['CATALOG_ELEM_VAL_060'].notna(),
                    df_result['CATALOG_ELEM_VAL_060'],
                    df_result['rewt']
                )

                df_result['T'] = df_result['re'].astype(float) * df_result['rewt'].astype(float) * 0.0004535924

                for k in list(df_result.columns):
                    if k not in ['re','T']:
                        df_result[k] = df_result[k].astype(str)
                    else:
                        df_result[k] = df_result[k].astype(float)                

                # 確保 T 欄位為 float
                df_result["re"] = df_result["re"].astype(float)
                df_result["T"] = df_result["T"].astype(float)

                # 計算總計
                re_total = round(df_result["re"].sum(), 2)
                T_total = round(df_result["T"].sum(), 3)

                # 依照 bdate, runno, batch_no 分組後，組出 groups 陣列
                groups = []
                grouped = df_result.groupby(['bdate'])

                for bdate, group in grouped:
                    re_subtotal = round(group["re"].sum(), 2)
                    T_subtotal = round(group["T"].sum(), 3)

                    items = [{
                        "runno": row["runno"],
                        "batch_no": row["batch_no"],                    
                        "ptype": row["ptype"],
                        "pgramg": row["pgramg"],
                        "psize1": row["psize1"],
                        "psize2": row["psize2"],
                        "store": row["store"],
                        "ExportSales": row["ExportSales"],
                        "pclass": row["pclass"],
                        "rewt": row["rewt"],
                        "re": str(row["re"]),
                        "T": str(row["T"]),
                        "amount": row["amount"],
                        "SOLD_TO_CUST_NAME": row["SOLD_TO_CUST_NAME"],
                        "TRANSACTION_DATE": row["TRANSACTION_DATE"],
                        "note": row["note"]
                    } for _, row in group.iterrows()]

                    groups.append({
                        "bdate": bdate,
                        "re_subtotal": re_subtotal,
                        "T_subtotal": T_subtotal,
                        "items": items
                    })

                result_json = {
                    "summary": {
                        "re_total": re_total,
                        "T_total": T_total
                    },
                    "groups": groups
                }
        else:
            result_json = {
                "summary": {
                    "re_total": 0,
                    "T_total": 0
                },
                "groups": []
            }            

        ExecutionTime = time.time() - startTime

        return result_json


# In[7]:


class adchem_use_d:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, mname: str):  
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        
        if mname == "18":
            sub_r = "'R'"
        elif mname == "19":
            sub_r = "'S'"
        elif mname == "20":
            sub_r = "'T'"
        elif mname == "21":
            sub_r = "'W'"
        else:
            pass        

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            sql =   """
                SELECT 
                    [adchem_use_d].mname,
                    [adchem_use_d].ym,
                    [adchem_use_d].bdate,
                    [adchem_use_d].sno,
                    [adchem_use_d].cost_id,
                    b.chsnm,
                    b.mat_id_erp,
                    [adchem_use_d].rqty
                from [AMIS].[dbo].[adchem_use_d]
                inner join admatcode_gp b  on b.cost_id=[adchem_use_d].cost_id and b.mtype = 'CH' and b.us_status = 'Y'
                where [adchem_use_d].bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                and [adchem_use_d].mname = '"""+ str(mname) +"""'
                order by mname,ym,bdate,sno,cost_id
            """       
            query = conn.execute(text(sql))  
            df_result = pd.DataFrame([dict(i) for i in query]) 
        
        for k in list(df_result.columns):
            if k !='rqty':
                df_result[k] = df_result[k].astype(str)
            
        if not df_result.empty:
            
            result_json = [{"mname": m,"ym":ym, "bdate": bdate, "sno":sno,"cost_id":c_id, "chsnm":c,"mat_id_erp": mat, "rqty": rq} 
                           for m,ym,bdate,sno,c_id,c,mat,rq in zip(df_result["mname"],df_result["ym"], 
                                                  df_result["bdate"],df_result["sno"],df_result["cost_id"],df_result["chsnm"],
                                                  df_result["mat_id_erp"], df_result["rqty"])]
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[8]:


class adcoat_use_d:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, mname: str): 
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        
        if mname == "18":
            mname_t = "'18'"
            sub_r = "'R'"
        elif mname == "19":
            mname_t = "'19','C2'"
            sub_r = "'S'"
        elif mname == "20":
            mname_t = "'20','C7','C8','C9'"
            sub_r = "'T'"
        elif mname == "21":
            mname_t = "'21','C1','C6'"
            sub_r = "'W'"
        else:
            pass        

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            sql = """
            SELECT
                adcoat_use_d.mname,
                adcoat_use_d.bdate,
                adcoat_use_d.cost_id,
                b.chsnm,
                b.mat_id_erp,
                adcoat_use_d.mat_id,
                adcoat_use_d.rqty
            FROM adcoat_use_d
            inner join admatcode_gp b on b.cost_id = adcoat_use_d.cost_id
            WHERE 1=1
            AND mname = '"""+ str(mname) +"""'
            AND adcoat_use_d.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
            ORDER BY  adcoat_use_d.mname,adcoat_use_d.bdate,adcoat_use_d.cost_id
            """            

            query = conn.execute(text(sql))  
            df_result = pd.DataFrame([dict(i) for i in query]) 
        
        for k in list(df_result.columns):
            if k !='rqty':
                df_result[k] = df_result[k].astype(str)
            
        if not df_result.empty:

            result_json = [{"bdate":b,"cost_id": c,"chsnm":ch, "mat_id_erp": mat_erp, "mat_id":mat, "rqty":r} 
                           for b,c,ch,mat_erp,mat,r in zip(df_result["bdate"],df_result["cost_id"],df_result["chsnm"], 
                                                  df_result["mat_id_erp"],df_result["mat_id"],df_result["rqty"])]
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[9]:


class adpulp_use_d:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, stime: str, etime: str, mname: str): 
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        
        if mname == "18":
            mname_t = "'18'"
            sub_r = "'R'"
        elif mname == "19":
            mname_t = "'19','C2'"
            sub_r = "'S'"
        elif mname == "20":
            mname_t = "'20','C7','C8','C9'"
            sub_r = "'T'"
        elif mname == "21":
            mname_t = "'21','C1','C6'"
            sub_r = "'W'"
        else:
            pass        

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            sql =   """
            ;With a_m_day_report AS
            (
                select a.mname,a.relno, a.ptype,a.gramg,a.rgramg,a.recycle,
                ((a.gramg - a.ctqty)*(1-(a.asnum/100))*a.lenth*a.width)/1000000 / 1000 AS pulp_qty
                FROM   [SRVAD1].[AMIS].[dbo].[amreel] a 
                WHERE   a.bdate  between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
            ),
            merge_data as
            (               
                SELECT 
                    bdate,
                    ptype,
                    mname,
                    [mat_id_erp],
                    [cost_id],                    
                    [schsnm],
                    '' AS SourceNo,
                    NULL AS Stage,
                    NULL AS Type,
                    SUM([use_qty]) AS [use_qty],
                    1 AS Unit,
                    1 AS Rate
                FROM
                (
                    SELECT [adpulp].[mname]
                          ,[adpulp].[relno]
                          ,[amreel].[ptype]
                          ,[sno]
                          ,[ftype]
                          ,[adpulp].[cost_id]
                          ,[adpulp].[scost_id]
                          ,[adpulp].[mat_id]
                          ,[item]
                          ,[adpulp].[bdate]
                          ,[PER]
                          ,[qty]
                          ,[wqty]
                          ,a_m_day_report.pulp_qty * [PER] * 1.0 / 100 AS [use_qty]
                          ,[admatcode_gp].mat_id_erp
                          ,[admatcode_gp].[schsnm]
                      FROM [SRVAD1].[AMIS].[dbo].[adpulp]
                      LEFT JOIN [SRVAD1].[AMIS].[dbo].[admatcode_gp] ON [adpulp].cost_id = [admatcode_gp].cost_id AND [adpulp].[scost_id] = [admatcode_gp].[scost_id]
                      LEFT JOIN [SRVAD1].[AMIS].[dbo].[amreel] ON [amreel].relno = [adpulp].relno
                      LEFT JOIN a_m_day_report ON a_m_day_report.relno = [adpulp].relno
                      WHERE [adpulp].bdate  between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                ) t
                GROUP BY bdate,mname,ptype,scost_id,[mat_id_erp],[cost_id],[schsnm]
            )
            SELECT bdate,ptype,mname,[mat_id_erp],[cost_id],[schsnm],[use_qty] FROM merge_data
            WHERE mname='"""+ str(mname) +"""'
            ORDER BY bdate,ptype,mname,[mat_id_erp],[cost_id],[schsnm],[use_qty]
    
            """       
            
            query = conn.execute(text(sql))  
            df_result = pd.DataFrame([dict(i) for i in query]) 
        
        for k in list(df_result.columns):
            if k !='use_qty':
                df_result[k] = df_result[k].astype(str)
        
        if not df_result.empty:

            result_json = [{"bdate": b,"ptype":p, "mname": m,"mat_id_erp": mat_erp,"cost_id":c, "schsnm":s, "use_qty":u} 
                           for b,p,m,mat_erp,c,s,u in zip(df_result["bdate"],df_result["ptype"], 
                                                  df_result["mname"],df_result["mat_id_erp"],df_result["cost_id"],
                                                  df_result["schsnm"],df_result["use_qty"])]
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[10]:


class adcoat_use_d_amortization:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, stime: str, etime: str, mname: str):
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        
        if mname == "18":
            mname_t = "'18'"
            sub_r = "'R'"
        elif mname == "19":
            mname_t = "'19','C2'"
            sub_r = "'S'"
        elif mname == "20":
            mname_t = "'20','C7','C8','C9'"
            sub_r = "'T'"
        elif mname == "21":
            mname_t = "'21','C1','C6'"
            sub_r = "'W'"
        else:
            pass               

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            sql =   """
           SELECT 
           t.mname,t.bdate,[XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no,t.runno,t.relno,t.cost_id,t.mat_id_erp,t.rqty,t.tqty
           FROM
           (
                SELECT a.mname,a.bdate,b.runno,a.relno,a.cost_id,c.mat_id_erp,sum(a.rqty) rqty,sum([tqty_d]) tqty--,b.ptype,a.scost_id
                FROM adcoat a ,amcoat b ,admatcode_gp c 
                where a.scost_id = c.scost_id and (c.mtype='CT' or c.CT_use='Y') 
                and a.relno = b.relno and a.mname = b.mname and a.mname in ("""+ str(mname_t) +""") 
                and a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                group by a.mname,b.ptype,c.mat_id_erp,b.runno,a.scost_id,a.bdate,a.cost_id,a.relno,b.y_mk      
           ) t
           LEFT JOIN [10.10.1.27].[YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] ON [XXIF_CHP_P208_IN_CRE_BATCH_ST].mes_no = t.runno
           AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no not like '%SR%' 
           AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no not like '%SH%' 
           AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].status_code = 'S'   
           order by t.mname,t.bdate,[XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no,t.runno,t.relno,t.cost_id,t.mat_id_erp
            """       
            
            query = conn.execute(text(sql))  
            df_result = pd.DataFrame([dict(i) for i in query]) 
        
        for k in list(df_result.columns):
            if k not in ['rqty', 'tqty']:
                df_result[k] = df_result[k].astype(str)
            df_result[k] = df_result[k].replace({np.nan: None})
        
        if not df_result.empty:

            result_json = [{"mname": m,"bdate": b,"batch_no":b_no,"runno":ru,"relno":re,"cost_id":c,
                            "mat_id_erp": mat_erp, "rqty":r, "tqty":t} 
                           for m,b,b_no,ru,re,c,mat_erp,r,t in zip(df_result["mname"],df_result["bdate"], 
                                                  df_result["batch_no"],df_result["runno"],df_result["relno"],
                                                  df_result["cost_id"],df_result["mat_id_erp"],
                                                  df_result["rqty"],df_result["tqty"])]
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[11]:


class adchem_use_d_amortization:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, mname: str):
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        
        if mname == "18":
            mname_t = "'18'"
            sub_r = "'R'"
        elif mname == "19":
            mname_t = "'19','C2'"
            sub_r = "'S'"
        elif mname == "20":
            mname_t = "'20','C7','C8','C9'"
            sub_r = "'T'"
        elif mname == "21":
            mname_t = "'21','C1','C6'"
            sub_r = "'W'"
        else:
            pass               

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            sql =   """    
           
            SELECT 
            t.mname,t.bdate,[XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no,t.runno,t.relno,t.cost_id,t.mat_id_erp,t.rqty,t.tqty
            FROM
            (
                SELECT b.ptype,a.bdate,a.mname,b.runno,a.relno,a.cost_id,a.scost_id,c.mat_id_erp,sum(a.fqty) rqty,sum(a.tqty_d) tqty
                FROM adchem a inner join amchem b  on a.relno = b.relno and a.relno not like '%B%' and a.utype = b.utype
                inner join admatcode_gp c on a.cost_id = c.cost_id and c.CH_use='Y'
                group by b.ptype,a.bdate,a.mname,b.runno,c.mat_id_erp,a.relno,b.relno,a.cost_id,a.scost_id,c.scost_id,b.y_mk
                having a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and sum(a.fqty) > '0'  and a.relno not like '%B%'
                and a.mname = '"""+ str(mname) +"""'
            ) t
            LEFT JOIN [10.10.1.27].[YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] ON [XXIF_CHP_P208_IN_CRE_BATCH_ST].mes_no = t.runno
            AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no not like '%SR%' 
            AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no not like '%SH%' 
            AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].status_code = 'S'
            order by t.mname,t.bdate,[XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no,t.runno,t.relno,t.cost_id,t.mat_id_erp
            """       
            
            query = conn.execute(text(sql))  
            df_result = pd.DataFrame([dict(i) for i in query]) 
        
        for k in list(df_result.columns):
            if k not in ['rqty', 'tqty']:
                df_result[k] = df_result[k].astype(str)
            df_result[k] = df_result[k].replace({np.nan: None})
        
        if not df_result.empty:

            result_json = [{"mname": m,"bdate": b,"batch_no":b_no,"runno":ru,"relno":re,"cost_id":c,
                            "mat_id_erp": mat_erp, "rqty":r, "tqty":t} 
                           for m,b,b_no,ru,re,c,mat_erp,r,t in zip(df_result["mname"],df_result["bdate"], 
                                                  df_result["batch_no"],df_result["runno"],df_result["relno"],
                                                  df_result["cost_id"],df_result["mat_id_erp"],
                                                  df_result["rqty"],df_result["tqty"])]
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[12]:


class adpulp_use_d_amortization:
    def __init__(self, servers):
        self.servers = servers     
        
    def fetch(self, stime: str, etime: str, mname: str):
        startTime = time.time()
        
        if not stime:
            return {'success': False, 'message': 'Missing stime parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing etime parameter'}        
        if not mname:
            return {'success': False, 'message': 'Missing mname parameter'} 
        
        if mname == "18":
            mname_t = "'18'"
            sub_r = "'R'"
        elif mname == "19":
            mname_t = "'19','C2'"
            sub_r = "'S'"
        elif mname == "20":
            mname_t = "'20','C7','C8','C9'"
            sub_r = "'T'"
        elif mname == "21":
            mname_t = "'21','C1','C6'"
            sub_r = "'W'"
        else:
            pass               

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn: 
            sql =   """
            ;With a_m_day_report AS
            (
                select a.mname,a.relno, a.ptype,a.gramg,a.rgramg,a.recycle,
                ((a.gramg - a.ctqty)*(1-(a.asnum/100))*a.lenth*a.width)/1000000 / 1000 AS pulp_qty
                FROM   [SRVAD1].[AMIS].[dbo].[amreel] a 
                WHERE   a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
            ),
            merge_data as
            (               
                SELECT 
                    mname,bdate,[runno],[relno],[cost_id],[mat_id_erp],SUM([use_qty]) AS [rqty],SUM([use_qty]) AS [tqty]
                FROM
                (
                    SELECT [adpulp].[mname]
                          ,[adpulp].[relno]
                          ,[amreel].[runno]
                          ,[amreel].[ptype]
                          ,[sno]
                          ,[ftype]
                          ,[adpulp].[cost_id]
                          ,[adpulp].[scost_id]
                          ,[adpulp].[mat_id]
                          ,[item]
                          ,[adpulp].[bdate]
                          ,[PER]
                          ,[qty]
                          ,[wqty]
                          ,a_m_day_report.pulp_qty * [PER] * 1.0 / 100 AS [use_qty]
                          ,[admatcode_gp].mat_id_erp
                          ,[admatcode_gp].[schsnm]
                      FROM [SRVAD1].[AMIS].[dbo].[adpulp]
                      LEFT JOIN [SRVAD1].[AMIS].[dbo].[admatcode_gp] ON [adpulp].cost_id = [admatcode_gp].cost_id AND [adpulp].[scost_id] = [admatcode_gp].[scost_id]
                      LEFT JOIN [SRVAD1].[AMIS].[dbo].[amreel] ON [amreel].relno = [adpulp].relno
                      LEFT JOIN a_m_day_report ON a_m_day_report.relno = [adpulp].relno
                      WHERE [adpulp].bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                ) t
                GROUP BY mname,bdate,[runno],[relno],[cost_id],[mat_id_erp]
            )
           SELECT t.mname,t.bdate,[XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no,t.runno,t.relno,t.cost_id,t.mat_id_erp,t.rqty,t.tqty
           FROM
           (
                SELECT * FROM merge_data
                WHERE mname='"""+ str(mname) +"""'
           ) t
           LEFT JOIN [10.10.1.27].[YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST] ON [XXIF_CHP_P208_IN_CRE_BATCH_ST].mes_no = t.runno
           AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no not like '%SR%' 
           AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no not like '%SH%' 
           AND [XXIF_CHP_P208_IN_CRE_BATCH_ST].status_code = 'S'  
           order by t.mname,t.bdate,[XXIF_CHP_P208_IN_CRE_BATCH_ST].batch_no,t.runno,t.relno,t.cost_id,t.mat_id_erp
            """       
            
            query = conn.execute(text(sql))  
            df_result = pd.DataFrame([dict(i) for i in query]) 
        
        for k in list(df_result.columns):
            if k not in ['rqty', 'tqty']:
                df_result[k] = df_result[k].astype(str)
            df_result[k] = df_result[k].replace({np.nan: None})
        
        if not df_result.empty:

            result_json = [{"mname": m,"bdate": b,"batch_no":b_no,"runno":ru,"relno":re,"cost_id":c,
                            "mat_id_erp": mat_erp, "rqty":r, "tqty":t} 
                           for m,b,b_no,ru,re,c,mat_erp,r,t in zip(df_result["mname"],df_result["bdate"], 
                                                  df_result["batch_no"],df_result["runno"],df_result["relno"],
                                                  df_result["cost_id"],df_result["mat_id_erp"],
                                                  df_result["rqty"],df_result["tqty"])]
        else:
            result_json = []

        ExecutionTime = time.time() - startTime

        return result_json


# In[13]:


# 紙別銷售類別


# In[14]:


class Ampaper_category:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, stime: str, etime: str, mname: str, mode: str, year_month_from: str): 
        startTime = time.time()
        
        if not year_month_from:
            pass
        else:
            dt = datetime.datetime.strptime(year_month_from, "%Y-%m")
            stime = dt.strftime('%Y-%m-%d')
            etime = (dt + relativedelta(months=1) - timedelta(days=1)).strftime("%Y-%m-%d")            
        
        if not mname:
            return {'success': False, 'message': 'Missing machine_name parameter'}
        if not stime:
            return {'success': False, 'message': 'Missing date_from parameter'}   
        if not etime:
            return {'success': False, 'message': 'Missing date_to parameter'}
        if not mode:
            saleclass = '1'
        elif mode == 'class':
            saleclass = '0'
        else:
            saleclass = '1'
            
        if mname == "18":
            mname_r = "''"
            mname_c = "''"
            mname_e = "''"
            mname_w = "'WR'"
            sub_r = "'R'"
        elif mname == "19":
            mname_r = "''"
            mname_c = "'C2'"
            mname_e = "'E3'"
            mname_w = "'WS','WJ','WK'"
            sub_r = "'S'"
        elif mname == "20":
            mname_r = "'RT'"
            mname_c = "'C7'"
            mname_e = "'EO','EP','EQ','ER'"
            mname_w = "'WE','WW'"
            sub_r = "'T'"
        elif mname == "21":
            mname_r = "'R1'"
            mname_c = "'C1'"
            mname_e = "'EA','EB','EC','ED'"
            mname_w = "'WA','WB'"
            sub_r = "'W'"
        else:
            pass        
        
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
        
        if saleclass == '0':
            srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
            with srv_SRVMESDBA1['create_engine'][0].connect() as conn:            
                sql =   """

                    SELECT [class] as [saleclass]
                            ,[ptype2]
                            ,[chsnm]
                            ,[ptype]
                            ,[chlnm]
                        FROM [AMIS].[dbo].[ampaper_category]
                        WHERE plant_id like 'A%'
                        AND len(saleclass) > 0
                        AND ptype IN (
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreel] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname = '"""+ str(mname) +"""'
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreld] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_r) +""") 
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amcotr] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_c) +""") 
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Ampres] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_e) +""") 
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amwind] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_w) +""")
                        )
                        order by saleclass,ptype2,ptype
                """

                query = conn.execute(text(sql))  
                df_Ampaper_category = pd.DataFrame([dict(i) for i in query])            
        else:
            srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
            with srv_SRVMESDBA1['create_engine'][0].connect() as conn:
                if not year_month_from:
                    sql =   """
                    SELECT [saleclass]
                            ,[ptype2]
                            ,[chsnm]
                            ,[ptype]
                            ,[chlnm]
                        FROM [AMIS].[dbo].[ampaper_category]
                        WHERE plant_id like 'A%'
                        AND len(saleclass) > 0
                        AND ptype IN (
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreel] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname = '"""+ str(mname) +"""'
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreld] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_r) +""") 
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amcotr] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_c) +""") 
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Ampres] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_e) +""") 
                            UNION
                            SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amwind] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_w) +""")                                                 
                        )
                        order by saleclass,ptype2,ptype
                    """
                else:
                    if mname == '18':
                        sql =   """

                        SELECT [saleclass]
                                ,[ptype2]
                                ,[chsnm]
                                ,[ptype]
                                ,[chlnm]
                            FROM [AMIS].[dbo].[ampaper_category]
                            WHERE plant_id like 'A%'
                            AND len(saleclass) > 0
                            AND ptype IN (
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreel] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname = '"""+ str(mname) +"""'
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreld] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_r) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amcotr] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_c) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Ampres] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_e) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amwind] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_w) +""")                                                 
                            )

                          union

                          SELECT 類別 AS [saleclass],
                          PN2 AS [ptype2],
                          '' AS chsnm,
                          PN4 AS [ptype],
                          '' AS chlnm

                          FROM [CostSheet].[dbo].[Equivalent_production]
                          WHERE 年 = '"""+ str(end_year) +"""'
                          --and ABS([塗前約當量(噸)] + [塗後約當量(噸)]) > 0
                          and (機台 = 'PM' + '"""+ str(mname) +"""' OR 機台 = '含浸')
                          GROUP BY 機台,類別,PN2,PN4

                          order by saleclass,ptype2,ptype
                        """                        
                    
                    elif mname == '19':
                        sql =   """

                        SELECT [saleclass]
                                ,[ptype2]
                                ,[chsnm]
                                ,[ptype]
                                ,[chlnm]
                            FROM [AMIS].[dbo].[ampaper_category]
                            WHERE plant_id like 'A%'
                            AND len(saleclass) > 0
                            AND ptype IN (
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreel] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname = '"""+ str(mname) +"""'
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreld] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_r) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amcotr] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_c) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Ampres] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_e) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amwind] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_w) +""")                                                 
                            )

                          union

                          SELECT 類別 AS [saleclass],
                          PN2 AS [ptype2],
                          '' AS chsnm,
                          PN4 AS [ptype],
                          '' AS chlnm

                          FROM [CostSheet].[dbo].[Equivalent_production]
                          WHERE 年 = '"""+ str(end_year) +"""'
                          --and ABS([塗前約當量(噸)] + [塗後約當量(噸)]) > 0
                          and (機台 = 'PM' + '"""+ str(mname) +"""' OR 機台 = 'NCR')
                          GROUP BY 機台,類別,PN2,PN4

                          order by saleclass,ptype2,ptype
                        """                                      
                    else:
                        sql =   """

                        SELECT [saleclass]
                                ,[ptype2]
                                ,[chsnm]
                                ,[ptype]
                                ,[chlnm]
                            FROM [AMIS].[dbo].[ampaper_category]
                            WHERE plant_id like 'A%'
                            AND len(saleclass) > 0
                            AND ptype IN (
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreel] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname = '"""+ str(mname) +"""'
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amreld] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_r) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amcotr] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_c) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Ampres] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_e) +""") 
                                UNION
                                SELECT distinct ptype FROM [SRVAD1].[AMIS].[dbo].[Amwind] WHERE bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and mname in ("""+ str(mname_w) +""")                                                 
                            )

                          union

                          SELECT 類別 AS [saleclass],
                          PN2 AS [ptype2],
                          '' AS chsnm,
                          PN4 AS [ptype],
                          '' AS chlnm

                          FROM [CostSheet].[dbo].[Equivalent_production]
                          WHERE 年 = '"""+ str(end_year) +"""'
                          --and ABS([塗前約當量(噸)] + [塗後約當量(噸)]) > 0
                          and 機台 = 'PM' + '"""+ str(mname) +"""'
                          GROUP BY 機台,類別,PN2,PN4

                          order by saleclass,ptype2,ptype
                        """

                query = conn.execute(text(sql))  
                df_Ampaper_category = pd.DataFrame([dict(i) for i in query])

        def build_nested_json(df):
            result = []
            saleclass_order = {}

            for _, row in df.iterrows():
                sc = row['saleclass']
                pt2 = row['ptype2']
                pt2_name = row['chsnm']
                pt = row['ptype']
                pt_name = row['chlnm']

                # Level 1 - saleclass
                if sc not in saleclass_order:
                    saleclass_order[sc] = {
                        "id": str(len(saleclass_order) + 1),
                        "name": sc,
                        "chsnm": sc,
                        "order": len(saleclass_order) + 1,
                        "children": []
                    }
                    result.append(saleclass_order[sc])

                sc_obj = saleclass_order[sc]

                # Level 2 - ptype2
                pt2_match = next((item for item in sc_obj['children'] if item['name'] == pt2), None)
                if pt2_match is None:
                    pt2_match = {
                        "id": f"{sc_obj['id']}.{len(sc_obj['children']) + 1}",
                        "name": pt2,
                        "chsnm": pt2_name,  # 加上中文名
                        "order": len(sc_obj['children']) + 1,
                        "children": []
                    }
                    sc_obj['children'].append(pt2_match)

                # Level 3 - ptype
                pt_match = {
                    "id": f"{pt2_match['id']}.{len(pt2_match['children']) + 1}",
                    "name": pt,
                    "chsnm": pt_name,  # 加上中文名
                    "order": len(pt2_match['children']) + 1,
                }
                pt2_match['children'].append(pt_match)

            return result

        nested_json = build_nested_json(df_Ampaper_category)

        # 最終 JSON 結構
        result_json = {
            "metadata": {
                "name": "Ampaper_category",
                "source": "API",
                "description": "Ampaper_category"
            },
            "data": nested_json
        }

        ExecutionTime = time.time() - startTime

        return result_json


# In[15]:


class Defect_induced_recycle_analysis_report:
    def __init__(self, servers):
        self.servers = servers 
        
    def fetch(self, stime: str, etime: str, mname: str): 
        startTime = time.time()     

        if not mname:
            return {'success': False, 'message': 'Missing machineName parameter'}        
        
        try:
            if stime:
                dt = datetime.datetime.strptime(stime, '%Y-%m')
                start_year, start_month = dt.year, dt.month
            else:
                start_year, start_month = 2024, 1
        except (ValueError, TypeError):
            start_year, start_month = 2024, 1
        
        try:
            if etime:
                dt = datetime.datetime.strptime(etime, '%Y-%m')
                end_year, end_month = dt.year, dt.month
            else:
                today = datetime.datetime.today()
                end_year, end_month = today.year, today.month
        except (ValueError, TypeError):
                today = datetime.datetime.today()
                end_year, end_month = today.year, today.month

        
        start_ym_str = f"{start_year}{start_month:02d}"
        end_ym_str = f"{end_year}{end_month:02d}"
        
        try:
            srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
            with srv_SRVMESDBA1['create_engine'][0].connect() as conn:
                if mname == '21':
                    sql =   """
                        SELECT * FROM [AMIS].[dbo].[Processing_yield_and_recycle_rate_PM21]
                        WHERE 年月 >='"""+ str(start_ym_str) +"""' AND 年月 <='"""+ str(end_ym_str) +"""'
                    """       
                elif mname == '20':
                    sql =   """
                        SELECT * FROM [AMIS].[dbo].[Processing_yield_and_recycle_rate_PM20]
                        WHERE 年月 >='"""+ str(start_ym_str) +"""' AND 年月 <='"""+ str(end_ym_str) +"""'
                    """                     
                query = conn.execute(text(sql))  
                df_all_data = pd.DataFrame([dict(i) for i in query])
        except:
            df_all_data = pd.DataFrame()
            
        if not df_all_data.empty:
            dt = datetime.datetime.strptime(df_all_data.sort_values(by=['年月'],ascending=False).head(1)['年月'].item(), '%Y%m')
            if dt.month == 12:
                year, month = dt.year+1, 1
            else:
                year, month = dt.year, dt.month+1
        else:
            today = datetime.datetime.today()
            today_year, today_month = today.year, today.month
            today_ym_str = f"{today_year}{today_month:02d}"
            if start_ym_str == today_ym_str:
                year, month = today_year, today_month
            else:
                year, month = 2024, 1
            
        sql_year, sql_month = year, month
            
        # 儲存資料
        all_data = pd.DataFrame()

        PM21_columns = ['日期', '週', 'PN2', '紙別', '基重', '抄造量(T)', '生產量(T)', '得率', '回爐量(T)', '回爐率',
               '改抄(T)', '斷紙(T)', '不良品量(T)', 'タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
               '紙邊不齊', '飄邊', '物性不足', '破孔', '其他', '處理對策及說明']

        PM20_columns = ['日期', '週', '紙別', '基重', '報到量(T)', '生產量(T)', '長度+漲米得率（％）', '寬幅得率（％）',
               '回爐量(T)', '回爐率（％）', '漲米重量', 'Trim Loss(T)', '紙頭紙尾損失(T)', '不良品量（T)',
               '原紙死痕', '原紙破孔', 'baggy', '軟邊', '油污', '夾雜', '參差', '其它', '處理對策及說明']

        while (year < end_year) or (year == end_year and month <= end_month):
            ym_str = f"{year}{month:02d}"

            if mname =='21':
                try:
                    if ym_str in ['202503','202504','202505','202506','202507','202508','202509','202510','202511','202512']:
                        file_path = fr'\\Srvafp1\週報\生產一處\各段加工得率及回爐率\塗佈量與塗前水分雙因子GreenZone可視化系統統計資料\{ym_str}加工得率與不良品改善統計表_生產一處.xlsx'
                    else:                 
                        file_path = fr'\\Srvafp1\週報\生產一處\各段加工得率及回爐率\{ym_str}加工得率與不良品改善統計表_生產一處.xlsx'
                    
#                     file_path = fr'\\Srvafp1\週報\生產一處\各段加工得率及回爐率\{ym_str}加工得率與不良品改善統計表_生產一處.xlsx'    
                    
                    df = pd.read_excel(file_path, sheet_name='抄紙機 ', skiprows=0, header=1)

                    df = df.loc[:df[df['紙別'].isna()].index[0] - 1, :].iloc[:, :-2]
                    df.iloc[:, 10:-1] = df.iloc[:, 10:-1].fillna(0)

                    df.columns = PM21_columns

                    df['年月'] = ym_str
                    all_data = pd.concat([all_data, df], ignore_index=True)

#                     print(f"機台{mname} {ym_str} 匯入成功")
                except Exception as e:
                    pass
#                     print(f"機台{mname} {ym_str} 匯入失敗: {e}") 
            elif mname =='20':
                try:            
                    file_path = fr'\\Srvafp1\週報\生產三處\各段加工得率及回爐率\{year}\{ym_str}加工得率與不良品改善統計表-生產三處.xlsx'
                    
                    df_1 = pd.read_excel(file_path, sheet_name='複捲機W', skiprows=0, header=1)

                    df_1 = df_1.loc[:df_1[df_1['日期'].isna()].index[0] - 1, :].iloc[:, :df_1.columns.get_loc('處理對策及說明')+1]
                    df_1.iloc[:, 14:-1] = df_1.iloc[:, 14:-1].fillna(0)

                    df_1.columns = PM20_columns

                    file_path = fr'\\Srvafp1\週報\生產三處\各段加工得率及回爐率\{year}\{ym_str}加工得率與不良品改善統計表-生產三處.xlsx'
                        
                    df_2 = pd.read_excel(file_path, sheet_name='複捲機E', skiprows=0, header=1)

                    df_2 = df_2.loc[:df_2[df_2['日期'].isna()].index[0] - 1, :].iloc[:, :df_2.columns.get_loc('處理對策及說明')+1]
                    df_2.iloc[:, 14:-1] = df_2.iloc[:, 14:-1].replace(r'^\s*$', np.nan, regex=True).fillna(0).astype(float)

                    df_2.columns = PM20_columns  

                    df_1['年月'] = ym_str
                    df_1['機台'] = '複捲機W'
                    df_2['年月'] = ym_str
                    df_2['機台'] = '複捲機E'
                    all_data = pd.concat([all_data, df_1, df_2], ignore_index=True)

        #             print(f"機台{mname} {ym_str} 匯入成功")
                except Exception as e:
                    pass
        #             print(f"機台{mname} {ym_str} 匯入失敗: {e}")         


            # 遞增年月
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
                
        if mname == '20':
            if not all_data.empty:
                all_data = all_data.loc[:,['年月','週','日期','紙別','基重','原紙死痕', '原紙破孔', 'baggy', '軟邊', '油污', '夾雜', '參差', '其它',]]
                all_data['週'] = all_data['週'].astype('Int64')
                all_data = all_data[~all_data['紙別'].isna()]
                all_data = all_data[~all_data['基重'].isna()]

                if datetime.datetime.today().day > 6:
                    insert_today = datetime.datetime.today() - relativedelta(months=1)
                else:
                    insert_today = datetime.datetime.today() - relativedelta(months=2)
                insert_year, inset_month = insert_today.year, insert_today.month
                insert_ym_str = f"{insert_year}{inset_month:02d}"
                
                sql_insert_ym_str = f"{sql_year}{sql_month:02d}"

                insert_this_year, inset_this_month = datetime.datetime.today().year, datetime.datetime.today().month
                insert_this_ym_str =  f"{insert_this_year}{inset_this_month:02d}"

                insert_all_data = all_data[(all_data['年月']>=min(insert_ym_str,sql_insert_ym_str)) &                                           (all_data['年月']<insert_this_ym_str)].copy()

                if insert_all_data.empty:
                    pass
                else:
                    with srv_SRVMESDBA1['create_engine'][0].connect() as conn:
                        insert_all_data.to_sql(name='Processing_yield_and_recycle_rate_PM20', con=conn, if_exists='append', index=False
                                        , dtype=mapping_df_types(all_data))

                        # 刪除重複資料（所有欄位都相同的情況）
                        cleanup_sql = """
                            ;WITH CTE AS (
                                SELECT *,
                                       ROW_NUMBER() OVER (
                                           PARTITION BY 年月, 週, 日期, 紙別, 基重,
                                                        原紙死痕, 原紙破孔, baggy, 軟邊, 油污, 夾雜, 參差, 其它
                                           ORDER BY (SELECT NULL)
                                       ) AS rn
                                FROM [AMIS].[dbo].[Processing_yield_and_recycle_rate_PM20]
                            )
                            DELETE FROM CTE WHERE rn > 1;
                        """

                        conn.execution_options(autocommit=True).execute(cleanup_sql)                           
            
                all_data = pd.concat([df_all_data,all_data],ignore_index=True)
            else:
                all_data = df_all_data.copy()
                
            all_data['年月'] = all_data['年月'].astype(float).astype(int)
            all_data['日期'] = all_data['日期'].astype(float).astype(int)
            all_data = all_data.sort_values(by=['年月','日期'],ascending=True).reset_index(drop=True)                  
            
            all_data = pd.concat([all_data,pd.DataFrame(all_data.loc[:,['原紙死痕', '原紙破孔', 'baggy', '軟邊',
                                                                        '油污', '夾雜', '參差', '其它']].sum()).T],
                     ignore_index=True)
            
            all_data.loc[all_data.index[-1], '紙別'] = '總和'

            all_data['總和'] = all_data.loc[:,['原紙死痕', '原紙破孔', 'baggy', '軟邊','油污', '夾雜', '參差', '其它']].sum(axis=1)
            
            start = datetime.datetime.strptime(stime, "%Y-%m")
            end = datetime.datetime.strptime(etime, "%Y-%m")
            month_diff = (end.year - start.year) * 12 + (end.month - start.month) + 1  
            
            sum_row = all_data.loc[all_data['紙別'] == '總和', ['原紙死痕', '原紙破孔', 'baggy', '軟邊', '油污', '夾雜', '參差', '其它', '總和']]
            avg_row = (sum_row / month_diff).round(2)
            avg_row['紙別'] = str(month_diff)+'個月平均'

            all_data = pd.concat([all_data, avg_row], ignore_index=True)
            
            df_result = all_data.copy()       

            for k in list(df_result.columns):
                if k not in ['原紙死痕', '原紙破孔', 'baggy', '軟邊', '油污', '夾雜', '參差', '其它', '總和']:
                    if k in ['年月', '週', '日期']:
                        df_result[k] = df_result[k].apply(lambda x: int(x) if pd.notna(x) and np.isfinite(x) else None)
                    else:
                        df_result[k] = df_result[k].astype(str)
                else:
                    df_result[k] = df_result[k].astype(float).round(3)                    
                df_result[k] = df_result[k].replace({np.nan: None})
                df_result[k] = df_result[k].replace({'nan': None})
                df_result[k] = df_result[k].replace({'<NA>': None})

            if not df_result.empty:

                result_json = [{"年月": ym,"週": w,'日期':date,"紙別":ptype,"基重":gramg,
                                "原紙死痕":d1,"原紙破孔":d2,"baggy":d3,"軟邊":d4,"油污":d5,
                                "夾雜":d6,"參差":d7,"其它":d8,"總和":d9} 
                               for ym,w,date,ptype,gramg,
                               d1,d2,d3,d4,d5,d6,d7,d8,d9 in zip(df_result["年月"],df_result["週"],df_result["日期"],  
                                                      df_result["紙別"],df_result["基重"],df_result["原紙死痕"],
                                                      df_result["原紙破孔"],df_result["baggy"],
                                                      df_result["軟邊"],df_result["油污"],
                                                      df_result["夾雜"],df_result["參差"],
                                                      df_result["其它"],df_result["總和"])]
            else:
                result_json = []                
    
    
        elif mname =='21':
            if not all_data.empty:
                all_data['抽吸不良流流'] = all_data['抽吸不良流流'].replace(' ',0)
                all_data['基重變化'] = np.where(
                    all_data['處理對策及說明'] == '基重變化',
                    all_data['其他'],
                    0
                )
                all_data['初出紙基重變化'] = np.where(
                    all_data['處理對策及說明'].astype(str).str.contains('初出紙基重變化', na=False),
                    all_data['其他'],
                    0
                )            
                all_data['其他'] = np.where(
                    all_data['處理對策及說明'].astype(str).str.contains('基重變化', na=False),
                    0,
                    all_data['其他']
                )
                all_data = all_data.loc[:,['年月','週','日期','紙別','基重','タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
                                                 '紙邊不齊', '飄邊', '物性不足', '破孔','基重變化', '初出紙基重變化', '其他','抄造量(T)', '生產量(T)',]]
                all_data['週'] = all_data['週'].astype('Int64')
                all_data = all_data[~all_data['紙別'].isna()]
                all_data = all_data[~all_data['基重'].isna()]

                if datetime.datetime.today().day > 6:
                    insert_today = datetime.datetime.today() - relativedelta(months=1)
                else:
                    insert_today = datetime.datetime.today() - relativedelta(months=2)
                insert_year, inset_month = insert_today.year, insert_today.month
                insert_ym_str = f"{insert_year}{inset_month:02d}"   
                
                sql_insert_ym_str = f"{sql_year}{sql_month:02d}"

                insert_this_year, inset_this_month = datetime.datetime.today().year, datetime.datetime.today().month
                insert_this_ym_str =  f"{insert_this_year}{inset_this_month:02d}"

                insert_all_data = all_data[(all_data['年月']>=min(insert_ym_str,sql_insert_ym_str)) &                                           (all_data['年月']<insert_this_ym_str)].copy()            

                if insert_all_data.empty:
                    pass
                else:
                    insert_all_data['基重'] = insert_all_data['基重'].astype(float).round(1).astype(str)
                    
                    with srv_SRVMESDBA1['create_engine'][0].connect() as conn:
                        insert_all_data.to_sql(name='Processing_yield_and_recycle_rate_PM21', con=conn, if_exists='append', index=False
                                        , dtype=mapping_df_types(all_data)) 
                        
                        # 刪除重複資料（所有欄位都相同的情況）
                        cleanup_sql = """
                            ;WITH CTE AS (
                                SELECT *,
                                       ROW_NUMBER() OVER (
                                           PARTITION BY 年月, 週, 日期, 紙別, 基重,
                                                        タㄦミ, 黑痕, 透氣度異常, 抽吸不良流流,
                                                        死紋, 汙點, 紙邊不齊, 飄邊, 物性不足,
                                                        破孔, 基重變化, 初出紙基重變化, 其他,
                                                        [抄造量(T)], [生產量(T)]
                                           ORDER BY (SELECT NULL)
                                       ) AS rn
                                FROM [AMIS].[dbo].[Processing_yield_and_recycle_rate_PM21]
                            )
                            DELETE FROM CTE WHERE rn > 1;
                        """

                        conn.execution_options(autocommit=True).execute(cleanup_sql)                        
                        
                all_data = pd.concat([df_all_data,all_data],ignore_index=True)   
            else:
                all_data = df_all_data.copy()
                
            all_data['年月'] = all_data['年月'].astype(float).astype(int)
            all_data['日期'] = all_data['日期'].astype(float).astype(int)
            all_data = all_data.sort_values(by=['年月','日期'],ascending=True).reset_index(drop=True)                
  
            all_data = pd.concat([all_data,pd.DataFrame(all_data.loc[:,['タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
                                                         '紙邊不齊', '飄邊', '物性不足', '破孔','基重變化', '初出紙基重變化', '其他']].sum()).T],
                     ignore_index=True)  
    
            all_data.loc[all_data.index[-1], '紙別'] = '總和'
            
            all_data['總和'] = all_data.loc[:,['タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
                                             '紙邊不齊', '飄邊', '物性不足', '破孔','基重變化', '初出紙基重變化', '其他']].sum(axis=1)            
            
            
            start = datetime.datetime.strptime(stime, "%Y-%m")
            end = datetime.datetime.strptime(etime, "%Y-%m")
            month_diff = (end.year - start.year) * 12 + (end.month - start.month) + 1  
            
            sum_row = all_data.loc[all_data['紙別'] == '總和', ['タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
                                             '紙邊不齊', '飄邊', '物性不足', '破孔','基重變化', '初出紙基重變化', '其他', '總和']]
            avg_row = (sum_row / month_diff).round(2)
            avg_row['紙別'] = str(month_diff)+'個月平均'

            all_data = pd.concat([all_data, avg_row], ignore_index=True)            
            
            df_result = all_data.copy()

            for k in list(df_result.columns):
                if k not in ['タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
                                             '紙邊不齊', '飄邊', '物性不足', '破孔','基重變化', '初出紙基重變化', '其他', '總和']:
                    if k in ['年月', '週', '日期']:
                        df_result[k] = df_result[k].apply(lambda x: int(x) if pd.notna(x) and np.isfinite(x) else None)
                    else:
                        df_result[k] = df_result[k].astype(str)
                else:
                    df_result[k] = df_result[k].astype(float).round(3)
                df_result[k] = df_result[k].replace({np.nan: None})
                df_result[k] = df_result[k].replace({'nan': None})
                df_result[k] = df_result[k].replace({'<NA>': None})

            if not df_result.empty:

                result_json = [{"年月": ym,"週": w,'日期':date,"紙別":ptype,"基重":gramg,
                                "タㄦミ":d1,"黑痕":d2,"透氣度異常":d3,"抽吸不良流流":d4,"死紋":d5,
                                "汙點":d6,"紙邊不齊":d7,"飄邊":d8,"物性不足":d9,"破孔":d10,"基重變化":d11,"初出紙基重變化":d12,
                                "其他":d13,"總和":d14} 
                               for ym,w,date,ptype,gramg,
                               d1,d2,d3,d4,d5,d6,d7,d8,d9,d10,d11,d12,d13,d14 in zip(df_result["年月"],df_result["週"],df_result["日期"],
                                                      df_result["紙別"],df_result["基重"],df_result["タㄦミ"],
                                                      df_result["黑痕"],df_result["透氣度異常"],
                                                      df_result["抽吸不良流流"],df_result["死紋"],
                                                      df_result["汙點"],df_result["紙邊不齊"],
                                                      df_result["飄邊"],df_result["物性不足"],
                                                      df_result["破孔"],df_result["基重變化"],df_result["初出紙基重變化"],
                                                      df_result["其他"],df_result["總和"])]
            else:
                result_json = []

        ExecutionTime = time.time() - startTime  

        return result_json


# In[16]:


class Defect_induced_recycle_chart:
    def __init__(self, servers):
        self.servers = servers    
    
    def fetch(self, stime: str, etime: str, mname: str): 
        startTime = time.time()      

        if not mname:
            return {'success': False, 'message': 'Missing machineName parameter'}        
        
        try:
            if stime:
                dt = datetime.datetime.strptime(stime, '%Y-%m')
                start_year, start_month = dt.year, dt.month
            else:
                start_year, start_month = 2024, 1
        except (ValueError, TypeError):
            start_year, start_month = 2024, 1
        
        try:
            if etime:
                dt = datetime.datetime.strptime(etime, '%Y-%m')
                end_year, end_month = dt.year, dt.month
            else:
                today = datetime.datetime.today()
                end_year, end_month = today.year, today.month
        except (ValueError, TypeError):
                today = datetime.datetime.today()
                end_year, end_month = today.year, today.month

        start_ym_str = f"{start_year}{start_month:02d}"
        end_ym_str = f"{end_year}{end_month:02d}"
        
        try:
            srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
            with srv_SRVMESDBA1['create_engine'][0].connect() as conn:
                if mname == '21':
                    sql =   """
                        SELECT * FROM [AMIS].[dbo].[Processing_yield_and_recycle_rate_PM21]
                        WHERE 年月 >='"""+ str(start_ym_str) +"""' AND 年月 <='"""+ str(end_ym_str) +"""'
                    """       
                elif mname == '20':
                    sql =   """
                        SELECT * FROM [AMIS].[dbo].[Processing_yield_and_recycle_rate_PM20]
                        WHERE 年月 >='"""+ str(start_ym_str) +"""' AND 年月 <='"""+ str(end_ym_str) +"""'
                    """                     
                query = conn.execute(text(sql))  
                df_all_data = pd.DataFrame([dict(i) for i in query])
        except:
            df_all_data = pd.DataFrame()
            
        if not df_all_data.empty:
            dt = datetime.datetime.strptime(df_all_data.sort_values(by=['年月'],ascending=False).head(1)['年月'].item(), '%Y%m')
            if dt.month == 12:
                year, month = dt.year+1, 1
            else:
                year, month = dt.year, dt.month+1
        else:
            today = datetime.datetime.today()
            today_year, today_month = today.year, today.month
            today_ym_str = f"{today_year}{today_month:02d}"
            if start_ym_str == today_ym_str:
                year, month = today_year, today_month
            else:
                year, month = 2024, 1
            
        # 儲存資料
        all_data = pd.DataFrame()

        PM21_columns = ['日期', '週', 'PN2', '紙別', '基重', '抄造量(T)', '生產量(T)', '得率', '回爐量(T)', '回爐率',
               '改抄(T)', '斷紙(T)', '不良品量(T)', 'タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
               '紙邊不齊', '飄邊', '物性不足', '破孔', '其他', '處理對策及說明']

        PM20_columns = ['日期', '週', '紙別', '基重', '報到量(T)', '生產量(T)', '長度+漲米得率（％）', '寬幅得率（％）',
               '回爐量(T)', '回爐率（％）', '漲米重量', 'Trim Loss(T)', '紙頭紙尾損失(T)', '不良品量（T)',
               '原紙死痕', '原紙破孔', 'baggy', '軟邊', '油污', '夾雜', '參差', '其它', '處理對策及說明']

        while (year < end_year) or (year == end_year and month <= end_month):
            ym_str = f"{year}{month:02d}"

            if mname =='21':
                try:
                    if ym_str in ['202503','202504','202505','202506','202507','202508','202509','202510','202511','202512']:
                        file_path = fr'\\Srvafp1\週報\生產一處\各段加工得率及回爐率\塗佈量與塗前水分雙因子GreenZone可視化系統統計資料\{ym_str}加工得率與不良品改善統計表_生產一處.xlsx'
                    else:                 
                        file_path = fr'\\Srvafp1\週報\生產一處\各段加工得率及回爐率\{ym_str}加工得率與不良品改善統計表_生產一處.xlsx'
                    
#                     file_path = fr'\\Srvafp1\週報\生產一處\各段加工得率及回爐率\{ym_str}加工得率與不良品改善統計表_生產一處.xlsx'
                        
                    df = pd.read_excel(file_path, sheet_name='抄紙機 ', skiprows=0, header=1)

                    df = df.loc[:df[df['週'].isna()].index[0] - 1, :].iloc[:, :-2]
                    df.iloc[:, 10:-1] = df.iloc[:, 10:-1].fillna(0)

                    df.columns = PM21_columns

                    df['年月'] = ym_str
                    all_data = pd.concat([all_data, df], ignore_index=True)                   
                except Exception as e:
                    pass
            elif mname =='20':
                try:                        
                    file_path = fr'\\Srvafp1\週報\生產三處\各段加工得率及回爐率\{year}\{ym_str}加工得率與不良品改善統計表-生產三處.xlsx'
                    
                    df_1 = pd.read_excel(file_path, sheet_name='複捲機W', skiprows=0, header=1)

                    df_1 = df_1.loc[:df_1[df_1['日期'].isna()].index[0] - 2, :].iloc[:, :df_1.columns.get_loc('處理對策及說明')+1]
                    df_1.iloc[:, 14:-1] = df_1.iloc[:, 14:-1].fillna(0)

                    df_1.columns = PM20_columns
                    
                    file_path = fr'\\Srvafp1\週報\生產三處\各段加工得率及回爐率\{year}\{ym_str}加工得率與不良品改善統計表-生產三處.xlsx'
                        
                    df_2 = pd.read_excel(file_path, sheet_name='複捲機E', skiprows=0, header=1)

                    df_2 = df_2.loc[:df_2[df_2['日期'].isna()].index[0] - 2, :].iloc[:, :df_2.columns.get_loc('處理對策及說明')+1]
                    df_2.iloc[:, 14:-1] = df_2.iloc[:, 14:-1].replace(r'^\s*$', np.nan, regex=True).fillna(0).astype(float)

                    df_2.columns = PM20_columns  

                    df_1['年月'] = ym_str
                    df_1['機台'] = '複捲機W'
                    df_2['年月'] = ym_str
                    df_2['機台'] = '複捲機E'
                    all_data = pd.concat([all_data, df_1, df_2], ignore_index=True)
                except Exception as e:
                    pass   

            # 遞增年月
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1             

        if mname =='20':
            all_data = pd.concat([df_all_data,all_data],ignore_index=True)
            all_data_group = all_data.loc[:,['年月','週','紙別','基重','原紙死痕', '原紙破孔', 'baggy', '軟邊', '油污', '夾雜', '參差', '其它',]].            groupby(['年月']).agg(a=('原紙死痕','sum'), 
                                 b=('原紙破孔','sum'),
                                 c=('baggy','sum'), 
                                 d=('軟邊','sum'),
                                 e=('油污','sum'),
                                 f=('夾雜','sum'),
                                 g=('參差','sum'),
                                ).reset_index()

            all_data_group.columns = ['年月','原紙死痕', '原紙破孔', 'baggy', '軟邊', '油污', '夾雜', '參差',]

            # 將資料轉成長格式
            df_melted = all_data_group.melt(id_vars=["年月"], var_name="category", value_name="value")
            df_melted = df_melted.sort_values(by=['年月','category'])
            df_melted['value'] = df_melted['value'].astype(float).round(3)

            # 轉換成 list of dict 並格式化
            content = [
                {
                    "yearmonth": str(row["年月"]),
                    "category": row["category"],
                    "value": row["value"]
                }
                for _, row in df_melted.iterrows()
            ]                
  
        elif mname == '21':
            if not all_data.empty:
                all_data['抽吸不良流流'] = all_data['抽吸不良流流'].replace(' ',0)
                all_data['基重變化'] = np.where(
                    all_data['處理對策及說明'] == '基重變化',
                    all_data['其他'],
                    0
                )
                all_data['初出紙基重變化'] = np.where(
                    all_data['處理對策及說明'].astype(str).str.contains('初出紙基重變化', na=False),
                    all_data['其他'],
                    0
                )      

                all_data['其他'] = np.where(
                    all_data['處理對策及說明'].astype(str).str.contains('基重變化', na=False),
                    0,
                    all_data['其他']
                )
                all_data = pd.concat([df_all_data,all_data],ignore_index=True)
            else:
                all_data = df_all_data.copy()
            all_data_group = all_data.loc[:,['年月','週','紙別','基重','タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
                                             '紙邊不齊', '飄邊', '物性不足', '破孔','基重變化','初出紙基重變化',
#                                              '基重變化(含初出紙)',
                                             '抄造量(T)', '生產量(T)',]].\
            groupby(['年月']).agg(a=('タㄦミ','sum'), 
                                 b=('黑痕','sum'),
                                 c=('透氣度異常','sum'), 
                                 d=('抽吸不良流流','sum'),
                                 e=('死紋','sum'),
                                 f=('汙點','sum'),
                                 g=('紙邊不齊','sum'),
                                 h=('飄邊','sum'),
                                 i=('物性不足','sum'),
                                 j=('破孔','sum'),
                                 k=('基重變化','sum'),
                                 l=('初出紙基重變化','sum'),
#                                  m=('基重變化(含初出紙)','sum'),
                                 n=('抄造量(T)','sum'),
                                 o=('生產量(T)','sum'),
                                ).reset_index()

            all_data_group.columns = ['年月','タㄦミ', '黑痕', '透氣度異常', '抽吸不良流流', '死紋', '汙點',
                                             '紙邊不齊', '飄邊', '物性不足', '破孔','基重變化','初出紙基重變化',
#                                               '基重變化(含初出紙)',
                                              '抄造量','生產量']

            all_data_group['回爐率(基重變化_抄造量)'] = all_data_group.apply(
                lambda row: (
                    (row['基重變化'] / row['抄造量'])
                ) if row['抄造量'] not in [0, None, np.nan] else 0,
                axis=1
            )            
#             all_data_group['回爐率(基重變化_生產量)'] = all_data_group.apply(
#                 lambda row: (
#                     (row['基重變化'] / row['生產量'])
#                 ) if row['生產量'] not in [0, None, np.nan] else 0,
#                 axis=1
#             )                   
            all_data_group['回爐率(初出紙基重變化_抄造量)'] = all_data_group.apply(
                lambda row: (
                    (row['初出紙基重變化'] / row['抄造量'])
                ) if row['抄造量'] not in [0, None, np.nan] else 0,
                axis=1
            )          
#             all_data_group['回爐率(初出紙基重變化_生產量)'] = all_data_group.apply(
#                 lambda row: (
#                     (row['初出紙基重變化'] / row['生產量'])
#                 ) if row['生產量'] not in [0, None, np.nan] else 0,
#                 axis=1
#             )                  

            # 將資料轉成長格式
            df_melted = all_data_group.melt(id_vars=["年月"], var_name="category", value_name="value")
            df_melted = df_melted.sort_values(by=['年月','category'])
            df_melted['value'] = df_melted['value'].astype(float).round(3)

            # 轉換成 list of dict 並格式化
            content = [
                {
                    "yearmonth": str(row["年月"]),
                    "category": row["category"],
                    "value": row["value"]
                }
                for _, row in df_melted.iterrows()
            ]

        # 最終 JSON 結構
        result_json = {
            "metadata": {
                "name": "Defect_induced_recycle_chart",
                "source": "/MES/defect-induced-recycle/chart",
                "description": "Defect_induced_recycle_chart"
            },
            "data": {
                "Content": content
            }
        }                 

        ExecutionTime = time.time() - startTime

        return result_json           


# In[17]:


# 加工良率每日報表


# In[31]:


class Yield_daily_report:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, stime: str, etime: str, mname: str, Product_Category: str):  
        startTime = time.time()

        if not stime:
            return {'success': False, 'message': 'Missing date_from parameter'}
        if not etime:
            return {'success': False, 'message': 'Missing date_to parameter'}        
        if not Product_Category:
            return {'success': False, 'message': 'Missing category parameter'} 
        
        srv_SRVMESDBA1 = self.servers['SRVMESDBA1'] 
        with srv_SRVMESDBA1['create_engine'][0].connect() as conn:        
            sql =   """
                SELECT [saleclass]
                      ,[class]
                      ,[ptype2]
                      ,[chsnm]
                      ,[ptype]
                      ,[chlnm]
                  FROM [AMIS].[dbo].[ampaper_category]
                  WHERE plant_id = 'A'
                  AND len(saleclass) > 0
                  order by saleclass,ptype2,ptype
            """
            query = conn.execute(text(sql))  
            df_Ampaper_category = pd.DataFrame([dict(i) for i in query])


        MachineCode = 'R1'

        params = (MachineCode, stime, etime, "N")
        query = "EXEC a_r_day_report_sp @mname=?, @sdate=?, @edate=?, @shft=?"

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            df_result = pd.read_sql(query, conn, params=params)

        if not df_result.empty:
            df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
            df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

            df_result_groupby = df_result.groupby(['bdate','class'])                .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)                .reset_index()

            df_result_groupby['lenth_rate'] = np.where(
                (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
                round((df_result_groupby['lenth'] - df_result_groupby['back']) / df_result_groupby['blenth'] * 100, 2),
                0
            )

            df_result_groupby['defective_quantity'] = np.where(
                (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
                round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
                0
            )
            # 儲存成1號再捲機結果
            df_result_R1 = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

            df_result_R1.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
        else:
            df_result_R1 = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    

        # ------------------------------------------------------------------
        MachineCode = 'C1'

        params = (MachineCode, stime, etime, "N")
        query = "EXEC a_c_day_report_sp @mname=?, @sdate=?, @edate=?, @shft=?"

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:        
            df_result = pd.read_sql(query, conn, params=params)

        if not df_result.empty:    
            df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
            df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

            df_result_groupby = df_result.groupby(['bdate','class'])                .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)                .reset_index()

            df_result_groupby['lenth_rate'] = np.where(
                (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
                round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
                0
            )

            df_result_groupby['defective_quantity'] = np.where(
                (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
                round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
                0
            )
            # 儲存成1號塗佈機結果
            df_result_C1 = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

            df_result_C1.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
        else:
            df_result_C1 = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    



        # ------------------------------------------------------------------
        MachineCode = 'EA'
        mname = '21'

        params = (MachineCode, mname, stime, etime, "N")
        query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:
            df_result = pd.read_sql(query, conn, params=params)

        if not df_result.empty:
            df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
            df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

            df_result_groupby = df_result.groupby(['bdate','class'])                .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)                .reset_index()

            df_result_groupby['lenth_rate'] = np.where(
                (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
                round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
                0
            )

            df_result_groupby['defective_quantity'] = np.where(
                (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
                round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
                0
            )
            # 儲存成1號塗佈機結果
            df_result_EA = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

            df_result_EA.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
        else:
            df_result_EA = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    


        # ------------------------------------------------------------------
        MachineCode = 'EB'
        mname = '21'

        params = (MachineCode, mname, stime, etime, "N")
        query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:
            df_result = pd.read_sql(query, conn, params=params)

        if not df_result.empty:    
            df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
            df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

            df_result_groupby = df_result.groupby(['bdate','class'])                .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)                .reset_index()

            df_result_groupby['lenth_rate'] = np.where(
                (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
                round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
                0
            )

            df_result_groupby['defective_quantity'] = np.where(
                (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
                round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
                0
            )
            # 儲存成1號塗佈機結果
            df_result_EB = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

            df_result_EB.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
        else:
            df_result_EB = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    

        # ------------------------------------------------------------------
        MachineCode = 'EC'
        mname = '21'

        params = (MachineCode, mname, stime, etime, "N")
        query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:
            df_result = pd.read_sql(query, conn, params=params)

        if not df_result.empty:
            df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
            df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

            df_result_groupby = df_result.groupby(['bdate','class'])                .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)                .reset_index()

            df_result_groupby['lenth_rate'] = np.where(
                (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
                round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
                0
            )

            df_result_groupby['defective_quantity'] = np.where(
                (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
                round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
                0
            )
            # 儲存成1號塗佈機結果
            df_result_EC = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

            df_result_EC.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
        else:
            df_result_EC = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    

        # ------------------------------------------------------------------
        MachineCode = 'ED'
        mname = '21'

        params = (MachineCode, mname, stime, etime, "N")
        query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

        srv_SRVAD1 = self.servers['SRVAD1'] 
        with srv_SRVAD1['create_engine'][0].connect() as conn:
            df_result = pd.read_sql(query, conn, params=params)

        if not df_result.empty:
            df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
            df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

            df_result_groupby = df_result.groupby(['bdate','class'])                .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)                .reset_index()

            df_result_groupby['lenth_rate'] = np.where(
                (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
                round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
                0
            )

            df_result_groupby['defective_quantity'] = np.where(
                (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
                round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
                0
            )
            # 儲存成1號塗佈機結果
            df_result_ED = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

            df_result_ED.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
        else:
            df_result_ED = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])        


        # ------------------------------------------------------------------
        def find_W_quality(stime, etime, MachineCode):

            srv_SRVAD1 = self.servers['SRVAD1'] 
            with srv_SRVAD1['create_engine'][0].connect() as conn:
                sql =   """

             ;WITH raw_data as
             (
                    select 
                        aa.bdate,aa.mname, aa.ptype, sum(aa.tl) as tl, sum(aa.pht) as pht, sum(aa.s5) as s5, sum(aa.s6) as s6,
                        CASE WHEN ptype IN ('KL00','SL00','SL0C','KV00') THEN '格拉新' 
                             WHEN ptype IN ('KWCL','KWCA') THEN 'CCK' 
                             ELSE '1' END AS IS_KL
                    from (
                        select a.y_mk, a.mname, a.relno, a.ptype, 
                        convert(decimal(18,3),
                            (convert(decimal(18,2),
                                    convert(decimal(18,3) ,
                                        case a.patch when 'C' then a.blenth+a.plenth 
                                                     when 'S' then a.blenth-a.plenth 
                                                     else a.blenth end * convert(decimal(12,0),a.barea/a.blenth*1000)/1000
                                        ) / 
                                        case a.patch when 'C' then a.blenth+a.plenth 
                                                     when 'S' then a.blenth-a.plenth 
                                                     else a.blenth end * 1000
                                    )- convert(decimal(18,2),a.warea/a.lenth*1000)
                            ) * a.lenth * a.pgramg / 1000000000
                        ) as tl, 
                                    convert(decimal(18,3),
                                    (case a.patch when 'C' then a.blenth+a.plenth 
                                                  when 'S' then a.blenth-a.plenth 
                                                  else a.blenth end - a.lenth) * 
                                    convert(decimal(18,2),convert(decimal(18,3),
                                    case a.patch when 'C' then a.blenth+a.plenth 
                                                 when 'S' then a.blenth-a.plenth 
                                                 else a.blenth end * 
                                    convert(decimal(12,0),a.barea/a.blenth*1000)/1000) / 
                                    case a.patch when 'C' then a.blenth+a.plenth 
                                                 when 'S' then a.blenth-a.plenth 
                                                 else a.blenth end * 1000)* a.pgramg / 1000000000) as pht, 
                                    convert(decimal(18,3),case when sum(b.area) > 0 then sum(b.area) else 0 end * a.pgramg /1000000) as s5,
                                    convert(decimal(18,3),case when sum(c.area) > 0 then sum(c.area) else 0 end * a.pgramg /1000000) as s6, 
                                    a.bdate
                        from amwind a
                        left join (
                            select adb.mname, adb.relno, sum(adb.lenth) as 'lenth', sum(adb.area) as 'area'
                            from (
                                select mname, relno, winsno, bdate, lenth, 
                                sum(case when width<100 then width*25.4 else width end) as 'width', 
                                lenth*sum(case when width<100 then width*25.4 else width end)/1000 as 'area'
                                from [AMIS].[dbo].[adwind] 
                                where prod in(5) 
                                group by mname, relno, winsno, bdate, pgramg, lenth
                            ) adb 
                            group by adb.mname, adb.relno
                        ) b on a.mname = b.mname and a.relno = b.relno 
                        left join (
                            select adb.mname, adb.relno, sum(adb.lenth) as 'lenth', sum(adb.area) as 'area'
                            from (
                                select mname, relno, winsno, bdate, lenth, 
                                sum(case when width<100 then width*25.4 else width end) as 'width', 
                                lenth*sum(case when width<100 then width*25.4 else width end)/1000 as 'area' 
                                from [AMIS].[dbo].[adwind] 
                                where prod in(6) 
                                group by mname, relno, winsno, bdate, pgramg, lenth
                            )adb
                            group by adb.mname, adb.relno
                        ) c on a.mname = c.mname and a.relno = c.relno 
                        group by a.y_mk, a.mname, a.relno, a.ptype, a.pgramg, a.patch, a.blenth, a.plenth, a.lenth, a.barea, a.warea, a.weigh, a.bdate
                    ) aa
                    where aa.mname = '"""+ str(MachineCode) +"""' and aa.bdate between convert(varchar(10), '"""+ str(stime) +"""', 111) and convert(varchar(10), '"""+ str(etime) +"""', 111) 
                    group by aa.bdate,aa.mname, aa.ptype 
                    --order by aa.bdate,aa.mname, aa.ptype      
             )
              SELECT t.bdate,t.mname,t.ptype,t.tl,t.pht,
                  CASE WHEN (SELECT COUNT(*) FROM raw_data WHERE ptype IN ('SL00','KL00','SL0C','KV00')) = 1 and t.IS_KL = '格拉新' AND n.weigh>ISNULL(m.weigh,0) THEN n.weigh 
                       WHEN (SELECT COUNT(*) FROM raw_data WHERE ptype IN ('KWCA','KWCL')) = 1 and t.IS_KL = 'CCK' AND n.weigh>ISNULL(m.weigh,0) THEN n.weigh
                  ELSE m.weigh END as s5,
                  t.s6
                FROM raw_data t
                LEFT JOIN (
                    select t.bdate,t.mname, t.ptype ,sum(weigh) as weigh
                    from
                    (
                        SELECT chkno,code,dest,pgramg,gramg,weigh,ptype,bdate,mname
                        FROM (
                            select a.chkno, a.code, b.dest,c.pgramg,c.gramg,c.weigh,c.ptype,a.bdate,a.mname,
                                ROW_NUMBER() OVER (
                                    PARTITION BY a.chkno, c.ptype, c.gramg, c.pgramg, c.weigh 
                                    ORDER BY a.code
                                ) AS rn
                            from adqumk a
                            inner join adcode b on b.code = a.code and b.pgid='QUMK'
                            inner join adrecycle c on a.chkno=c.chkno
                            inner join (
                                select chkno from adrecycle 
                                where bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                                and mname = '"""+ str(MachineCode) +"""'
                                and weigh > 0 and status = 'B' and reason <> '紙頭紙尾' and status1 is null
                            ) adrecycle_2 on adrecycle_2.chkno = a.chkno
                            where 1=1
                            and a.mname = '"""+ str(MachineCode) +"""'
                        ) t
                        WHERE t.rn = 1   
                    ) t
                    group by t.bdate,t.mname, t.ptype 
                ) m on t.bdate = m.bdate and t.mname = m.mname and t.ptype = m.ptype
                LEFT JOIN (
                    select t.bdate,t.mname, t.IS_KL ,sum(weigh) as weigh
                    from
                    (
                        SELECT chkno,code,dest,pgramg,gramg,weigh,ptype,bdate,mname,
                        CASE WHEN ptype IN ('KL00','SL00','SL0C','KV00') THEN '格拉新' 
                             WHEN ptype IN ('KWCL','KWCA') THEN 'CCK'
                             ELSE '1' END AS IS_KL
                        FROM (
                            select a.chkno, a.code, b.dest,c.pgramg,c.gramg,c.weigh,c.ptype,a.bdate,a.mname,
                                ROW_NUMBER() OVER (
                                    PARTITION BY a.chkno, c.ptype, c.gramg, c.pgramg, c.weigh 
                                    ORDER BY a.code
                                ) AS rn
                            from adqumk a
                            inner join adcode b on b.code = a.code and b.pgid='QUMK'
                            inner join adrecycle c on a.chkno=c.chkno
                            inner join (
                                select chkno from adrecycle 
                                where bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                                and mname = '"""+ str(MachineCode) +"""'
                                and weigh > 0 and status = 'B' and reason <> '紙頭紙尾' and status1 is null
                            ) adrecycle_2 on adrecycle_2.chkno = a.chkno
                            where 1=1
                            and a.mname = '"""+ str(MachineCode) +"""'
                        ) t
                        WHERE t.rn = 1   
                    ) t
                    group by t.bdate,t.mname, t.IS_KL
                ) n on t.bdate = n.bdate and t.mname = n.mname and t.IS_KL = n.IS_KL        

                """       
                query = conn.execute(text(sql))
                df_result_W_quality = pd.DataFrame([dict(i) for i in query])
                
                if not df_result_W_quality.empty:
                    df_result_W_quality['s5'] = df_result_W_quality['s5'].astype(float)
                    df_result_W_quality['s6'] = df_result_W_quality['s6'].astype(float)

            return df_result_W_quality

        def find_W_amwind(stime, etime, MachineCode):
            if stime == etime:
                stime_t = stime
                etime_t = str((datetime.datetime.strptime(etime, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'))
            else:
                stime_t = stime
                etime_t = etime

            stime_t_1 = str((datetime.datetime.strptime(stime, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d'))
            
            stime_t_month = str((datetime.datetime.strptime(stime, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d'))            

            srv_SRVAD1 = self.servers['SRVAD1'] 
            with srv_SRVAD1['create_engine'][0].connect() as conn:            
                sql =   """
                select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
                                    c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
                                    (case when a.patch='S' then a.blenth-a.plenth-t.olenth else a.blenth+a.plenth end) as blenth,
                                    (case when a.patch='S' then a.barea-a.parea-t.oarea else a.barea+a.parea end) as barea,
                                    (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
                                    (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
                                FROM  amwind a 
                                INNER JOIN ampaper b ON a.ptype = b.ptype 
                                Left JOIN amrunt c ON a.runno = c.runno
                                left join (
                                    select 
                                        mname, 
                                        relno, 
                                        sum(olenth) as olenth, 
                                        convert(decimal(12,3),sum(olenth)*width/1000) as oarea 
                                    from (
                                        select a.mname, a.y_mk, a.relno, a.winsno, a.runno, a.bdate, a.olenth, 
                                        case when b.width<100 then b.width*25.4 else b.width end as 'width' 
                                        from adwind a
                                        left join amwind b on a.relno = b.relno 
                                        where 1=1
                                        --and a.mname='WB' 
                                        and a.y_mk >= year(getdate())-8 
                                        and a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
                                        and a.mname= '"""+ str(MachineCode) +"""'
                                        group by a.mname, a.y_mk, a.relno, a.winsno, a.runno, a.bdate, a.olenth, b.width
                                    ) o
                                    group by mname, relno, width
                                ) t on t.relno = a.relno                                
                                WHERE  a.bdate between '"""+ str(stime_t_1) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""'
                                and a.flag = 'Y'
                                GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk,t.olenth,t.oarea
                                ORDER BY  a.pdate, a.relno
                """       
                query = conn.execute(text(sql))
                df_result = pd.DataFrame([dict(i) for i in query])

                sql =   """
                    SELECT bdate,ptype,sum(width) AS width,count(*) as winsno
                    FROM
                    (
                        SELECT bdate,relno,winsno,sum(width) AS width,MAX(ptype) AS ptype
                        FROM
                        (                    
                            select 
                                a.bdate,a.relno,a.winno,a.swinno,a.ptype,a.pclass,a.pgramg,a.width,a.lenth,a.weigh,a.splice,a.prod,a.roll,a.olenth,a.winsno
                            from adwind a 
                            where a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and a.mname = '"""+ str(MachineCode) +"""' AND prod != '6'
                            AND relno IN
                            (
                                select distinct relno
                                from
                                (
                                select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
                                                    c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
                                                    (case when a.patch='S' then a.blenth-a.plenth else a.blenth+a.plenth end) as blenth,
                                                    (case when a.patch='S' then a.barea-a.parea else a.barea+a.parea end) as barea,
                                                    (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
                                                    (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
                                                FROM  amwind a 
                                                INNER JOIN ampaper b ON a.ptype = b.ptype 
                                                Left JOIN amrunt c ON a.runno = c.runno  
                                                WHERE  a.bdate between '"""+ str(stime_t_1) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""'
                                                GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk    
                                  ) t
                            )
                        ) m 
                        group by bdate,relno,winsno
                    ) n 
                    group by bdate,ptype
                """       
                query = conn.execute(text(sql))
                df_result_width = pd.DataFrame([dict(i) for i in query]) 

                sql =   """
                    SELECT bdate,ptype,sum(weigh) AS weigh,count(*) as winsno
                    FROM
                    (
                        SELECT bdate,relno,winsno,sum(weigh) AS weigh,MAX(ptype) AS ptype
                        FROM
                        (                    
                            select 
                                a.bdate,a.relno,a.winno,a.swinno,a.ptype,a.pclass,a.pgramg,a.width,a.lenth,a.weigh,a.splice,a.prod,a.roll,a.olenth,a.winsno
                            from adwind a 
                            where a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and a.mname = '"""+ str(MachineCode) +"""'
                            AND relno IN
                            (
                                select distinct relno
                                from
                                (
                                select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
                                                    c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
                                                    (case when a.patch='S' then a.blenth-a.plenth else a.blenth+a.plenth end) as blenth,
                                                    (case when a.patch='S' then a.barea-a.parea else a.barea+a.parea end) as barea,
                                                    (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
                                                    (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
                                                FROM  amwind a 
                                                INNER JOIN ampaper b ON a.ptype = b.ptype 
                                                Left JOIN amrunt c ON a.runno = c.runno  
                                                WHERE  a.bdate between '"""+ str(stime_t_1) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""'
                                                GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk    
                                  ) t
                            )
                        ) m 
                        group by bdate,relno,winsno
                    ) n 
                    group by bdate,ptype
                """       
                query = conn.execute(text(sql))
                df_result_weigh = pd.DataFrame([dict(i) for i in query])

                sql =   """
                        SELECT bdate,relno,winsno,lenth,MAX(ptype) AS ptype
                        FROM
                        (
                            select 
                                a.bdate,a.relno,a.winno,a.swinno,a.ptype,a.pclass,a.pgramg,a.width,a.lenth,a.weigh,a.splice,a.prod,a.roll,a.olenth,a.winsno
                            from adwind a 
                            where a.bdate between '"""+ str(stime_t_month) +"""' and '"""+ str(etime_t) +"""' and a.mname = '"""+ str(MachineCode) +"""'
                            AND relno IN
                            (
                                select distinct relno
                                from
                                (
                                select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
                                                    c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
                                                    (case when a.patch='S' then a.blenth-a.plenth else a.blenth+a.plenth end) as blenth,
                                                    (case when a.patch='S' then a.barea-a.parea else a.barea+a.parea end) as barea,
                                                    (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
                                                    (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
                                                FROM  amwind a 
                                                INNER JOIN ampaper b ON a.ptype = b.ptype 
                                                Left JOIN amrunt c ON a.runno = c.runno  
                                                WHERE  a.bdate between '"""+ str(stime_t_1) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""' AND a.flag = 'Y'
                                                GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk    
                                  ) t
                            )
                        ) m 
                        group by bdate,relno,winsno,lenth
                """       
                query = conn.execute(text(sql))
                df_result_lenth = pd.DataFrame([dict(i) for i in query])                
            
            if not df_result_width.empty:
                df_result_width = df_result_width.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
                df_result_weigh = df_result_weigh.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
                df_result_lenth = df_result_lenth.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')

                df_result_lenth = df_result_lenth.groupby(['bdate','relno','winsno','ptype','class'])                    .agg(lenth=('lenth','max')).reset_index()            

                df_result_width_groupby = df_result_width.groupby(['bdate','class'])                    .agg(width=('width','sum'),winsno=('winsno','sum'))                    .reset_index()

                df_result_weigh_groupby = df_result_weigh.groupby(['bdate','class'])                    .agg(weigh2=('weigh','sum'),winsno=('winsno','sum'))                    .reset_index()

                df_result_lenth_groupby = df_result_lenth.groupby(['bdate','class'])                    .agg(lenth2=('lenth','sum'),winsno=('winsno','sum'))                    .reset_index() 
            
                df_result_lenth_Cross_day_relno = df_result_lenth.groupby(['relno','bdate']).size().reset_index().groupby(['relno']).size()
                df_result_lenth_Cross_day_relno = df_result_lenth_Cross_day_relno[df_result_lenth_Cross_day_relno>1].reset_index()

                df_result_lenth_Cross_day = df_result_lenth[df_result_lenth['relno'].isin(list(df_result_lenth_Cross_day_relno['relno']))]                .groupby(['bdate','relno'])['lenth'].sum().reset_index()
                df_result_lenth_Cross_day.rename(columns={'lenth':'lenth2'},inplace=True)
                df_result_lenth_Cross_day['bdate'] = pd.to_datetime(df_result_lenth_Cross_day['bdate']).dt.date.astype(object)            

                df_result_lenth_Cross_day = df_result_lenth_Cross_day[df_result_lenth_Cross_day['bdate']==                                                                      datetime.datetime.strptime(stime, '%Y-%m-%d').date()].                                                                      reset_index(drop=True)
                df_result_lenth_Cross_day = df_result_lenth_Cross_day.loc[:,['relno','lenth2']]                
                
                
                df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')

                df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

                df_result = df_result.merge(df_result_lenth_Cross_day,on=['relno'],how='left')
                df_result['blenth'] = np.where(
                            (df_result['lenth2'].notna()) & (df_result['lenth2'] != 0),
                            df_result['lenth2'],
                            df_result['blenth']
                        ) 
                
                df_result = df_result[(df_result['bdate']==datetime.datetime.strptime(stime, '%Y-%m-%d').date()) |                                      (~df_result['lenth2'].isna())].reset_index(drop=True)

                df_result["bdate"] = datetime.datetime.strptime(stime, '%Y-%m-%d').date()

                df_result['lenth'] = np.where(
                    df_result['lenth'] <= df_result['blenth'],
                    df_result['lenth'],
                    df_result['blenth']
                )                    

                df_result_groupby = df_result.groupby(['bdate','class'])                    .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),blenth=('blenth','sum'),winset=('winset','sum'))                    .reset_index()

                df_result_groupby['weigh'] = df_result_groupby['weigh'].astype(float)
                df_result_groupby['bdate'] = pd.to_datetime(df_result_groupby['bdate'])

                if stime == etime:
                    df_result_groupby['bdate'] = df_result_groupby['bdate'].min() 
                    df_result_groupby = df_result_groupby.groupby(['bdate','class'])                        .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),blenth=('blenth','sum'),winset=('winset','sum'))                        .reset_index()                    
                    df_result_groupby = df_result_groupby.merge(df_result_width_groupby.loc[:,['bdate','class','width','winsno']],
                                                                on = ['bdate','class'],
                                                                how='outer')                
                else:
                    df_result_groupby = df_result_groupby.merge(df_result_width_groupby.loc[:,['bdate','class','width','winsno']],
                                                                on = ['bdate','class'],
                                                                how='left')         

                df_result_groupby = df_result_groupby.merge(df_result_weigh_groupby.loc[:,['bdate','class','weigh2']],
                                                            on = ['bdate','class'],
                                                            how='left')
                df_result_groupby = df_result_groupby.merge(df_result_lenth_groupby.loc[:,['bdate','class','lenth2']],
                                                            on = ['bdate','class'],
                                                            how='left')                   

                df_result_groupby['lenth'] = np.where(
                            df_result_groupby['lenth2']<=df_result_groupby['lenth'],
                            df_result_groupby['lenth2'],
                            df_result_groupby['lenth']
                        )              

                df_result_groupby['width'] = df_result_groupby['width'].astype(float)
                df_result_groupby['winsno'] = df_result_groupby['winsno'].astype(float)
                df_result_groupby['weigh'] = df_result_groupby['weigh2'].copy().astype(float)
            else:
                df_result_groupby = pd.DataFrame(columns=['bdate','class','weigh','lenth','blenth','winset',
                                                          'lenth2','weigh2','lenth3','width','winsno'])    

            return df_result_groupby
        
        def find_W_quality_reason(stime, etime, MachineCode):
            srv_SRVAD1 = self.servers['SRVAD1'] 
            with srv_SRVAD1['create_engine'][0].connect() as conn:            
                sql =   """          
                    SELECT bdate, ptype, dest,sum(weigh) as weigh
                    FROM
                    (
                        SELECT chkno,code,dest,pgramg,gramg,weigh,ptype,bdate
                        FROM (
                            select a.chkno, a.code, b.dest,c.pgramg,c.gramg,c.weigh,c.ptype,a.bdate,
                                ROW_NUMBER() OVER (
                                    PARTITION BY a.chkno, c.ptype, c.gramg, c.pgramg, c.weigh 
                                    ORDER BY a.code
                                ) AS rn
                            from adqumk a
                            inner join adcode b on b.code = a.code and b.pgid='QUMK'
                            inner join adrecycle c on a.chkno=c.chkno
                            inner join (
                                select chkno from adrecycle 
                                where bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                                and mname = '"""+ str(MachineCode) +"""'
                                and weigh > 0 and status = 'B' and reason <> '紙頭紙尾' and status1 is null
                            ) adrecycle_2 on adrecycle_2.chkno = a.chkno
                            where 1=1
                            and a.mname = '"""+ str(MachineCode) +"""'
                            and a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
                        ) t
                        WHERE t.rn = 1                    
                    ) t
                    group by bdate, ptype, dest
                    order by bdate, ptype, dest                
                """
                query = conn.execute(text(sql))
                df_result = pd.DataFrame([dict(i) for i in query])   
                
            return df_result
        
        def find_W_Summary(stime, etime, df_Ampaper_category):

            start_date = datetime.datetime.strptime(stime, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(etime, '%Y-%m-%d')

            current_date = start_date

            df_result_W_t = pd.DataFrame()
            df_result_W_quality_reason_t = pd.DataFrame()

            while current_date <= end_date:

                date_str = current_date.strftime('%Y-%m-%d')

                MachineCode = 'WA'

                df_result_WA_quality = find_W_quality(date_str, date_str, MachineCode)
                if not df_result_WA_quality.empty:
                    df_result_WA_quality = df_result_WA_quality.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
                    df_result_WA_quality = df_result_WA_quality.groupby(['bdate','class'])                        .agg(tl=('tl','sum'),pht=('pht','sum'),s5=('s5','sum'),s6=('s6','sum'))                        .reset_index()
                    df_result_WA_quality['bdate'] = pd.to_datetime(df_result_WA_quality['bdate'])

                df_result_WA_quality_reason = find_W_quality_reason(date_str, date_str, MachineCode)

                df_result_WA = find_W_amwind(date_str, date_str, MachineCode)
                
                if not df_result_WA.empty:
                    df_result_WA = df_result_WA.merge(df_result_WA_quality,on = ['bdate','class'],how='left')

                MachineCode = 'WB'

                df_result_WB_quality = find_W_quality(date_str, date_str, MachineCode)       
                if not df_result_WB_quality.empty:
                    df_result_WB_quality = df_result_WB_quality.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
                    df_result_WB_quality = df_result_WB_quality.groupby(['bdate','class'])                        .agg(tl=('tl','sum'),pht=('pht','sum'),s5=('s5','sum'),s6=('s6','sum'))                        .reset_index()
                    df_result_WB_quality['bdate'] = pd.to_datetime(df_result_WB_quality['bdate'])

                df_result_WB_quality_reason = find_W_quality_reason(date_str, date_str, MachineCode)

                df_result_WB = find_W_amwind(date_str, date_str, MachineCode)
                
                if not df_result_WB.empty:                
                    df_result_WB = df_result_WB.merge(df_result_WB_quality,on = ['bdate','class'],how='left')

                df_result_W_quality_reason = pd.concat([df_result_WA_quality_reason,df_result_WB_quality_reason]).reset_index(drop=True)

                if not df_result_W_quality_reason.empty:
                    df_result_W_quality_reason = df_result_W_quality_reason.groupby(['bdate','ptype','dest'])['weigh'].sum().reset_index()
                    df_result_W_quality_reason = df_result_W_quality_reason.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
                    df_result_W_quality_reason = df_result_W_quality_reason.groupby(['bdate','class','dest'])['weigh'].sum().reset_index()
                    df_result_W_quality_reason = (
                        df_result_W_quality_reason
                        .groupby(['bdate','class'])
                        .agg(
                            reason_str=('dest', lambda x: ''.join(
                                x + df_result_W_quality_reason.loc[x.index,'weigh'].round(3).astype(str) + 'T'
                            )),
                            weigh_sum=('weigh','sum')
                        )
                        .reset_index()
                    )
                    df_result_W_quality_reason.columns = ['bdate', 'class', 'df_result_W_reason_str','weigh_sum']
                    df_result_W_quality_reason['bdate'] = pd.to_datetime(df_result_W_quality_reason['bdate']).dt.date.astype(object)
                else:
                    df_result_W_quality_reason = pd.DataFrame(columns=['bdate', 'class', 'df_result_W_reason_str'])          

                df_result_groupby = pd.concat([df_result_WA, df_result_WB], ignore_index=True).groupby(['bdate', 'class'], as_index=False)[['weigh', 'lenth', 'blenth','winset','tl','pht','s5','s6','width','winsno']].sum()

                df_result_groupby['weigh'] = df_result_groupby['weigh'] - df_result_groupby['s5'] - df_result_groupby['s6']
                df_result_groupby['paper_head_tail_ton_rate'] = np.where(
                    (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
                    round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
                    0
                )


                df_result_groupby['width_rate'] = np.where(
                    (df_result_groupby['width'].notna()) & (df_result_groupby['width'] != 0),
                    round((df_result_groupby['width'] / (df_result_groupby['winsno'] * 4930) *100), 2),
                    0
                )

                df_result_groupby['width_rate'] = np.where(df_result_groupby['width_rate']>100,100,df_result_groupby['width_rate'])


                df_result_groupby['lenth_ton'] = (df_result_groupby['weigh'] / df_result_groupby['paper_head_tail_ton_rate'] * 100) - df_result_groupby['weigh'] + df_result_groupby['s5']
                df_result_groupby['width_ton'] = (df_result_groupby['weigh'] / df_result_groupby['width_rate'] * 100) - df_result_groupby['weigh']


                df_result_groupby['quality_ton'] = df_result_groupby['s5']
                df_result_groupby['paper_head_tail_ton'] = df_result_groupby['lenth_ton'] - df_result_groupby['quality_ton']

                df_result_groupby['lenth_rate'] = np.where(
                    ((df_result_groupby['weigh'] + df_result_groupby['lenth_ton']).notna()) & ((df_result_groupby['weigh'] + df_result_groupby['lenth_ton']) != 0),
                    round((df_result_groupby['weigh'] / (df_result_groupby['weigh'] + df_result_groupby['lenth_ton']) * 100), 2),
                    0
                )

                df_result_W = df_result_groupby.loc[:,['bdate','class','weigh','paper_head_tail_ton_rate','lenth_rate','width_rate',
                                         'paper_head_tail_ton','lenth_ton','width_ton','quality_ton']]
                df_result_W.columns = ['bdate','class','weigh_'+'W','paper_head_tail_ton_rate_'+'W','lenth_rate_'+'W','width_rate_'+'W',
                                         'paper_head_tail_ton_'+'W','lenth_ton_'+'W','width_ton_'+'W','quality_ton_'+'W']
                df_result_W['bdate'] = pd.to_datetime(df_result_W['bdate']).dt.date.astype(object)    

                df_result_W_t = pd.concat([df_result_W_t,df_result_W],ignore_index=True)
                df_result_W_quality_reason_t = pd.concat([df_result_W_quality_reason_t,df_result_W_quality_reason],ignore_index=True)

                current_date += timedelta(days=1) 

            return df_result_W_t,df_result_W_quality_reason_t
        
        df_result_W,df_result_W_quality_reason = find_W_Summary(stime, etime, df_Ampaper_category)

        df_keys = pd.concat([
            df_result_R1[['bdate', 'class']],
            df_result_C1[['bdate', 'class']],
            df_result_EA[['bdate', 'class']],
            df_result_EB[['bdate', 'class']],
            df_result_EC[['bdate', 'class']],
            df_result_ED[['bdate', 'class']],
            df_result_W[['bdate', 'class']],
            df_result_W_quality_reason[['bdate', 'class']]
        ], ignore_index=True).drop_duplicates().sort_values(by=['bdate', 'class'])

        # 2. 以所有出現過的 bdate/class 為主表，依序 left join 其他表
        df_result = df_keys             .merge(df_result_R1, on=['bdate', 'class'], how='left')             .merge(df_result_C1, on=['bdate', 'class'], how='left')             .merge(df_result_EA, on=['bdate', 'class'], how='left')             .merge(df_result_EB, on=['bdate', 'class'], how='left')             .merge(df_result_EC, on=['bdate', 'class'], how='left')             .merge(df_result_ED, on=['bdate', 'class'], how='left')             .merge(df_result_W, on=['bdate', 'class'], how='left')             .merge(df_result_W_quality_reason, on=['bdate', 'class'], how='left')        
        
        df_result['defective_reasons_ED'] = '紙頭紙尾'    
        df_result = df_result[df_result['class']==Product_Category]
        
        mask = ~np.isclose(df_result['quality_ton_W'], df_result['weigh_sum'])
        df_result.loc[mask, 'quality_ton_W'] = df_result.loc[mask, 'weigh_sum']        
        df_result.drop(columns=['weigh_sum'], inplace=True)        
        
        df_result_summary = df_result.replace([np.inf, -np.inf], np.nan).fillna(0)                            .groupby(['class']).sum(numeric_only=True).reset_index()

        for l in ['R1','C1','EA','EB','EC','ED']:
            col_def = 'defective_quantity_' + l
            col_weigh = 'weigh_' + l
            col_rate = 'lenth_rate_' + l            

            if col_def not in df_result_summary.columns:
                df_result_summary[col_def] = np.nan
            else:
                df_result_summary[col_def] = df_result_summary[col_def].round(1)
            if col_weigh not in df_result_summary.columns:
                df_result_summary[col_weigh] = np.nan
            else:
                df_result_summary[col_weigh] = df_result_summary[col_weigh].round(3)

            total = df_result_summary[col_def].fillna(0) + df_result_summary[col_weigh].fillna(0)
            with_nonzero = (total != 0)

            if len(df_result) == 1:
                df_result_summary[col_rate] = np.where(
                    with_nonzero,
                    df_result[col_rate],
                    np.nan
                )                
            else:
                df_result_summary[col_rate] = np.where(
                    with_nonzero,
                    (df_result_summary[col_weigh].fillna(0) / total).round(4) * 100,
                    np.nan
                )

        df_result_summary['paper_head_tail_ton_rate_W'] = np.where(
                ((df_result_summary['weigh_W'] + df_result_summary['paper_head_tail_ton_W']).notna()) &\
                ((df_result_summary['weigh_W'] + df_result_summary['paper_head_tail_ton_W']) != 0),
                round(df_result_summary['weigh_W'] /\
                      (df_result_summary['weigh_W'] + df_result_summary['paper_head_tail_ton_W']) * 100, 2),
                0
            )    

        df_result_summary['lenth_rate_W'] = np.where(
                ((df_result_summary['weigh_W'] + df_result_summary['lenth_ton_W']).notna()) &\
                ((df_result_summary['weigh_W'] + df_result_summary['lenth_ton_W']) != 0),
                round(df_result_summary['weigh_W'] /\
                      (df_result_summary['weigh_W'] + df_result_summary['lenth_ton_W']) * 100, 2),
                0
            )    

        df_result_summary['width_rate_W'] = np.where(
                ((df_result_summary['weigh_W'] + df_result_summary['width_ton_W']).notna()) &\
                ((df_result_summary['weigh_W'] + df_result_summary['width_ton_W']) != 0),
                round(df_result_summary['weigh_W'] /\
                      (df_result_summary['weigh_W'] + df_result_summary['width_ton_W']) * 100, 2),
                0
            )    
        
        df_result_summary['bdate'] = '合計'
        
        defective_quantity_summary = df_result_summary[['defective_quantity_R1', 'defective_quantity_C1',
                       'defective_quantity_EA', 'defective_quantity_EB',
                       'defective_quantity_EC', 'defective_quantity_ED',
                       'lenth_ton_W', 'width_ton_W']].fillna(0).sum(axis=1)
        
        numerator = df_result_summary[['weigh_EA', 'weigh_EB', 'weigh_EC', 'weigh_ED']].fillna(0).sum(axis=1)
        denominator = (
            df_result_summary[['weigh_EA', 'defective_quantity_EA',
                               'weigh_EB', 'defective_quantity_EB',
                               'weigh_EC', 'defective_quantity_EC',
                               'weigh_ED', 'defective_quantity_ED']]
            .fillna(0).sum(axis=1)
        )

        lenth_rate_summary = (
            df_result_summary['width_rate_W'].fillna(0) *
            df_result_summary['lenth_rate_R1'].fillna(0) *
            df_result_summary['lenth_rate_C1'].fillna(0) *
            (numerator / denominator.replace(0, np.nan)) *  # 防止除以 0
            df_result_summary['lenth_rate_W'].fillna(0) / 1000000
        )        
        
        paper_head_tail_ton_summary = (
            df_result_summary[['defective_quantity_R1', 'defective_quantity_C1',
                               'defective_quantity_EA', 'defective_quantity_EB',
                               'defective_quantity_EC', 'defective_quantity_ED',
                               'paper_head_tail_ton_W', 'width_ton_W']]
            .fillna(0).sum(axis=1)
        )        

        lenth_rate_summary_overall = (
            df_result_summary['width_rate_W'].fillna(0) *
            df_result_summary['lenth_rate_R1'].fillna(0) *
            df_result_summary['lenth_rate_C1'].fillna(0) *
            (numerator / denominator.replace(0, np.nan)) *
            df_result_summary['paper_head_tail_ton_rate_W'].fillna(0) / 1000000
        )
        
        df_result = pd.concat([df_result,df_result_summary], ignore_index=True)

        for k in list(df_result.columns):
            if k in ['weigh_R1','weigh_C1','weigh_EA','weigh_EB','weigh_EC','weigh_ED','weigh_W',
                     'paper_head_tail_ton_W','lenth_ton_W','width_ton_W','quality_ton_W']:
                # 先轉成 float 再格式化到三位小數字串
                df_result[k] = df_result[k].astype(float).map(lambda x: f"{x:.3f}" if pd.notnull(x) else None)
            elif k in ['lenth_rate_R1','lenth_rate_C1','lenth_rate_EA','lenth_rate_EB','lenth_rate_EC','lenth_rate_ED',
                       'paper_head_tail_ton_rate_W','lenth_rate_W','width_rate_W']:
                df_result[k] = df_result[k].astype(float).map(lambda x: f"{x:.2f}" if pd.notnull(x) else None)
            else:
                df_result[k] = df_result[k].apply(lambda x: str(x) if pd.notnull(x) else None)
        
        if not df_result.empty:

            detail_items = [{"bdate": b,
#                             "class":c,
                            "weigh_R1":wr,"lenth_rate_R1":lr,"defective_quantity_R1":dr,
                            "weigh_C1":wc,"lenth_rate_C1":lc,"defective_quantity_C1":dc,
                            "weigh_EA":w_ea,"lenth_rate_EA":l_ea,"defective_quantity_EA":d_ea,
                            "weigh_EB":w_eb,"lenth_rate_EB":l_eb,"defective_quantity_EB":d_eb,
                            "weigh_EC":w_ec,"lenth_rate_EC":l_ec,"defective_quantity_EC":d_ec,
                            "weigh_ED":w_ed,"lenth_rate_ED":l_ed,"defective_quantity_ED":d_ed,"defective_reasons_E":d_red,
                            "weigh_W":w_w,"paper_head_tail_ton_rate_W":p_rw,"lenth_rate_W":l_rw,
                            "width_rate_W":w_rw,"paper_head_tail_ton_W":p_w,"lenth_ton_W":l_tw,
                            "width_ton_W":w_tw,"quality_ton_W":q_tw,"df_result_W_reason_str":d_rwrs
                           } 
                           for b,
#                            c,
                           wr,lr,dr,wc,lc,dc,
                           w_ea,l_ea,d_ea,
                           w_eb,l_eb,d_eb,
                           w_ec,l_ec,d_ec,
                           w_ed,l_ed,d_ed,d_red,
                           w_w,p_rw,l_rw,w_rw,p_w,l_tw,w_tw,q_tw,d_rwrs in zip(df_result["bdate"],
#                                                                         df_result["class"], 
                                          df_result["weigh_R1"],df_result["lenth_rate_R1"],df_result["defective_quantity_R1"],
                                          df_result["weigh_C1"],df_result["lenth_rate_C1"],df_result["defective_quantity_C1"],
                                          df_result["weigh_EA"],df_result["lenth_rate_EA"],df_result["defective_quantity_EA"],
                                          df_result["weigh_EB"],df_result["lenth_rate_EB"],df_result["defective_quantity_EB"],
                                          df_result["weigh_EC"],df_result["lenth_rate_EC"],df_result["defective_quantity_EC"],
                                          df_result["weigh_ED"],df_result["lenth_rate_ED"],df_result["defective_quantity_ED"],df_result["defective_reasons_ED"],
                                          df_result["weigh_W"],df_result["paper_head_tail_ton_rate_W"],df_result["lenth_rate_W"],
                                          df_result["width_rate_W"],df_result["paper_head_tail_ton_W"],df_result["lenth_ton_W"],
                                          df_result["width_ton_W"],df_result["quality_ton_W"],df_result["df_result_W_reason_str"])]
            
            # 最終的 JSON 結構
            result_json = {
                "metadata": {
                    "name": "yield-daily-report",
                    "source": "/MES/yield-daily-report",
                    "description": "yield-daily-report"
                },
                "data": {
                    "content": detail_items,
                    "summary":{
                        "defective_quantity_summary" : None if pd.isna(round(defective_quantity_summary.item(),2)) else round(defective_quantity_summary.item(),2),
                        "lenth_rate_summary" : None if pd.isna(round(lenth_rate_summary.item(),2)) else round(lenth_rate_summary.item(),2),
                        "paper_head_tail_ton_summary" : None if pd.isna(round(paper_head_tail_ton_summary.item(),2)) else round(paper_head_tail_ton_summary.item(),2),
                        "lenth_rate_summary_overall" : None if pd.isna(round(lenth_rate_summary_overall.item(),2)) else round(lenth_rate_summary_overall.item(),2),
                    }
                
                }
            }            

        else:
            result_json = {
                "metadata": {
                    "name": "yield-daily-report",
                    "source": "/MES/yield-daily-report",
                    "description": "yield-daily-report"
                },
                "data": {    
                    "content": {},
                    "summary": {}
                }
            } 

        ExecutionTime = time.time() - startTime
        
        return result_json


# In[19]:


class Relno_production_history:
    def __init__(self, servers):
        self.servers = servers     
    
    def fetch(self, relno: str):  
        startTime = time.time()
        
        if not relno:
            return {'success': False, 'message': 'Missing relno parameter'}            
            
        try:
            srv_SRVAD1 = self.servers['SRVAD1'] 
            with srv_SRVAD1['create_engine'][0].connect() as conn:                
                sql =   """
                    DECLARE @relno varchar(20) = :relno;

                    select a.mname as m,a.runno as m_runno,a.pdate as m_pdate,(select ptype+' '+chsnm from ampaper where ptype=a.ptype) as m_ptype,a.recycle as m_recycle,a.rgramg as m_rgramg,g.gramg as m_gramg,g.pgramg as m_pgramg,

                            b.mname as r,b.runno as r_runno,b.pdate as r_pdate,(select ptype+' '+chsnm from ampaper where ptype=b.ptype) as r_ptype,
                            b.gramg as r_gramg, b.pgramg as r_pgramg,a.rweigh as r_bweigh, b.rweigh as r_weigh,
                            a.rweigh - b.rweigh AS r_weigh_diff,
                            ROUND(CAST((b.lenth - b.back) / (b.blenth * 1.0) AS float),8) AS r_lenth_rate,
                            ROUND(CAST((b.width) / (b.bwidth * 1.0) AS float),8) AS r_width_rate,
                            ROUND(CAST(( (b.lenth - b.back) / (b.blenth * 1.0) ) * ( (b.width) / (b.bwidth * 1.0) )AS float),8) AS r_area_rate,
                            ROUND(CAST((b.rweigh) / (a.rweigh * 1.0) AS float),8) AS r_weigh_rate,

                            c.mname as c,c.runno as c_runno,c.pdate as c_pdate,(select ptype+' '+chsnm from ampaper where ptype=c.ptype) as c_ptype,c.gramg as c_gramg,c.pgramg as c_pgramg,
                            c.bweigh as c_bweigh, c.weigh as c_weigh,
                            c.bweigh - c.weigh AS c_weigh_diff,
                            ROUND(CAST((c.lenth - c.back) / (c.blenth * 1.0) AS float),8) AS c_lenth_rate,
                            ROUND(CAST((c.width) / (c.width * 1.0) AS float),8) AS c_width_rate,
                            ROUND(CAST(( (c.lenth - c.back) / (c.blenth * 1.0) ) * ( (c.width) / (c.width * 1.0) )AS float),8) AS c_area_rate,
                            ROUND(CAST((c.weigh) / (c.bweigh * 1.0) AS float),8) AS c_weigh_rate,

                            d.mname as e,d.runno as e_runno,d.pdate as e_pdate,(select ptype+' '+chsnm from ampaper where ptype=d.ptype) as e_ptype,
                            d.gramg as e_gramg, d.pgramg as e_pgramg,
                            c.weigh as e_bweigh, d.weigh as e_weigh,
                            c.weigh - d.weigh AS e_weigh_diff,
                            ROUND(CAST((d.lenth - d.back) / (d.blenth * 1.0) AS float),8) AS e_lenth_rate,
                            ROUND(CAST((d.width) / (d.width * 1.0) AS float),8) AS e_width_rate,
                            ROUND(CAST(( (d.lenth - d.back) / (d.blenth * 1.0) ) * ( (d.width) / (d.width * 1.0) )AS float),8) AS e_area_rate,
                            ROUND(CAST((d.weigh) / (c.weigh * 1.0) AS float),8) AS e_weigh_rate,

                            e.mname as w,e.runno as w_runno,e.pdate as w_pdate,(select ptype+' '+chsnm from ampaper where ptype=e.ptype) as w_ptype,e.gramg as w_gramg,e.pgramg as w_pgramg,
                            ROUND((case when e.patch='S' then e.barea-e.parea else e.barea+e.parea end)*e.pgramg/1000000,3) AS w_bweigh,
                            e.weigh as w_weigh,
                            ROUND((case when e.patch='S' then e.barea-e.parea else e.barea+e.parea end)*e.pgramg/1000000,3) - e.weigh AS w_weigh_diff,
                            w_lenth_rate,w_width_rate,w_area_rate,
                            ROUND(CAST((e.weigh) / (ROUND((case when e.patch='S' then e.barea-e.parea else e.barea+e.parea end)*e.pgramg/1000000,3) * 1.0) AS float),8) AS w_weigh_rate

                    from amreel a 
                    left join amreld b on b.relno=a.relno and b.sno='1' 
                    left join amcotr c on c.relno=a.relno and c.sno='1' 
                    left join ampres d on d.relno=a.relno and d.sno='1' 
                    left join (
                        SELECT 
                            CASE WHEN patch = 'C' THEN ROUND(CAST( e.lenth / ((e.blenth + e.plenth) * 1.0) AS float),8)
                            WHEN patch = 'S' THEN ROUND(CAST((e.lenth) / ((e.blenth- e.plenth - t.olenth) * 1.0) AS float),8)
                            ELSE ROUND(CAST((e.lenth) / ((e.blenth + e.plenth) * 1.0) AS float),8) END AS w_lenth_rate,
                            ROUND(CAST((e.Wd_rate * 1.0 / 100.0) AS float),8) AS w_width_rate,
                            CASE WHEN patch = 'C' THEN ROUND(CAST( e.warea / ((e.barea + e.parea) * 1.0) AS float),8)
                                WHEN patch = 'S' THEN ROUND(CAST((e.warea) / ((e.barea- e.parea - t.oarea) * 1.0) AS float),8)
                                ELSE ROUND(CAST((e.warea) / ((e.barea + e.parea) * 1.0) AS float),8) END AS w_Area_rate,
                            e.*
                        FROM amwind e
                        left join (
                            select 
                                mname, 
                                relno, 
                                sum(olenth) as olenth, 
                                convert(decimal(12,3),sum(olenth)*width/1000) as oarea 
                            from (
                                select a.mname, a.y_mk, a.relno, a.winsno, a.runno, a.bdate, a.olenth, 
                                case when b.width<100 then b.width*25.4 else b.width end as 'width' 
                                from adwind a
                                left join amwind b on a.relno = b.relno 
                                where 1=1
                                --and a.mname='WB' 
                                and a.y_mk >= year(getdate())-8 
                                and a.relno = @relno
                                group by a.mname, a.y_mk, a.relno, a.winsno, a.runno, a.bdate, a.olenth, b.width
                            ) o
                            group by mname, relno, width
                        ) t on t.relno = e.relno
                        WHERE e.relno = @relno
                    ) e on e.relno=a.relno and e.sno='1'
                    left join bmatst f on f.relno=a.relno
                    Left join amrunt g on g.runno=a.runno
                    where a.relno=@relno
                """         
                query = conn.execute(text(sql), relno = relno)  
                df_result = pd.DataFrame([dict(i) for i in query])  

        except Exception as e:
            return {'success': False, 'message': f'Query failed: {str(e)}'}, 500

        for k in list(df_result.columns):
            df_result[k] = df_result[k].apply(lambda x: str(x) if pd.notnull(x) else None)            

        # 建立 JSON 結構
        result_json = {
            "data": df_result.to_dict(orient='records')
        }   


        ExecutionTime = time.time() - startTime

        return result_json


# In[ ]:





# In[ ]:





# In[41]:


# from sqlalchemy import create_engine
# from urllib.parse import quote_plus as urlquote

# df_SERVER_SRVMESDBA1 = pd.DataFrame([['SRVMESDBA1','AMIS']], columns=['SERVER', 'DB'])

# df_SERVER_SRVMESDBA1['create_engine'] = ''
# df_SERVER_SRVMESDBA1['cnx'] = ''

# df_SERVER_SRVMESDBA1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("Fta@2023") + df_SERVER_SRVMESDBA1['SERVER'][0] + '/' + df_SERVER_SRVMESDBA1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
#                                                     pool_pre_ping=True,
#                                                     pool_recycle=1800,  # 避免 MySQL idle 超時
#                                                     pool_size=5,  # 視應用情境而定
#                                                     max_overflow=10)
# df_SERVER_SRVMESDBA1['cnx'][0] = df_SERVER_SRVMESDBA1['create_engine'][0].connect() 

# df_SERVER_SRVAD1 = pd.DataFrame([['SRVAD1','AMIS']], columns=['SERVER', 'DB'])

# df_SERVER_SRVAD1['create_engine'] = ''
# df_SERVER_SRVAD1['cnx'] = ''

# df_SERVER_SRVAD1['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk") + df_SERVER_SRVAD1['SERVER'][0] + '/' + df_SERVER_SRVAD1['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
#                                                     pool_pre_ping=True,
#                                                     pool_recycle=1800,  # 避免 MySQL idle 超時
#                                                     pool_size=5,  # 視應用情境而定
#                                                     max_overflow=10)
# df_SERVER_SRVAD1['cnx'][0] = df_SERVER_SRVAD1['create_engine'][0].connect() 

# df_SERVER_CHPGTERPDBAAR01 = pd.DataFrame([['CHPGTERPDBAAR01','YFYPRODERP_FTA']], columns=['SERVER', 'DB'])

# df_SERVER_CHPGTERPDBAAR01['create_engine'] = ''
# df_SERVER_CHPGTERPDBAAR01['cnx'] = ''

# df_SERVER_CHPGTERPDBAAR01['create_engine'][0] = create_engine('mssql+pyodbc://sa:%s@' % urlquote("yfyoljk") + df_SERVER_CHPGTERPDBAAR01['SERVER'][0] + '/' + df_SERVER_CHPGTERPDBAAR01['DB'][0] + '?driver=ODBC+Driver+17+for+SQL+Server',fast_executemany=True,
#                                                     pool_pre_ping=True,
#                                                     pool_recycle=1800,  # 避免 MySQL idle 超時
#                                                     pool_size=5,  # 視應用情境而定
#                                                     max_overflow=10)
# df_SERVER_CHPGTERPDBAAR01['cnx'][0] = df_SERVER_CHPGTERPDBAAR01['create_engine'][0].connect() 


# In[42]:


# stime = '2026-03-10'
# etime = '2026-03-10'
# mname = '21'


# In[43]:


#         if mname == "18":
#             mname_t = "'WR','WJ','WK'"
#             sub_r = "'R'"
#         elif mname == "19":
#             mname_t = "'WS','WJ','WK'"
#             sub_r = "'S'"
#         elif mname == "20":
#             mname_t = "'WE','WW'"
#             sub_r = "'T'"
#         elif mname == "21":
#             mname_t = "'WA','WB'"
#             sub_r = "'W'"
#         else:
#             pass

#         with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:            
#             sql =   """
#                 SELECT mes_no, batch_no
#                 FROM (
#                     SELECT 
#                         mes_no, 
#                         batch_no, 
#                         ROW_NUMBER() OVER (PARTITION BY mes_no ORDER BY batch_no) AS rn
#                     FROM [10.10.1.27].[YFYPRODERP_FTA].[dbo].[XXIF_CHP_P208_IN_CRE_BATCH_ST]
#                     WHERE substring(batch_no, 10, 2) = 'SR' 
#                       AND status_code = 'S'
#                 ) t
#                 WHERE rn = 1 AND mes_no IN (
#                     select distinct runno from adwind 
#                     where mname in("""+ str(mname_t) +""") and substring(runno,1,1) = """+ str(sub_r) +"""
#                     and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
#                     and prod not in('3','5','6','9') 
#                 )          
#             """       
#             query = conn.execute(text(sql))  
#             df_batch_no = pd.DataFrame([dict(i) for i in query])           
            
#             sql =   """
#             SELECT 
#                 *,
#                 '4'+ptype+pclass+RIGHT('000' + CAST(CAST(CAST(pgramg AS FLOAT) * 10 AS INT)  AS VARCHAR), 5)+prodn AS itemNo            
#             FROM
#             (
#                 SELECT *,CASE 
#                     WHEN x_yn = 'Y' AND pstatus = '成品' THEN 'A4FG'
#                     WHEN pstatus = '成品' THEN 
#                         CASE 
#                             WHEN '"""+ str(mname) +"""' = '18' AND prodn <> 'R' THEN 'A3FG'
#                             WHEN '"""+ str(mname) +"""' = '19' AND prodn <> 'R' THEN 'A2FG'
#                             WHEN ('"""+ str(mname) +"""' = '20' AND prodn <> 'R') 
#                                  OR ('"""+ str(mname) +"""' = '18' AND prodn <> 'R') 
#                                  OR ('"""+ str(mname) +"""' = '19' AND prodn <> 'R') THEN 'A6FG'
#                             WHEN '"""+ str(mname) +"""' = '21' AND prodn <> 'R' THEN 'A7FG'   
#                             ELSE NULL  -- 如果沒有符合條件，不設值
#                         END
#                     ELSE 'FTA.SFG.SR.PM' + CAST('"""+ str(mname) +"""' AS VARCHAR)  -- 非 "成品" 情況，store 依 mname 設定
#                 END AS store
#                 FROM
#                 (
#                     select *,
#                     CASE 
#                         WHEN prod = '1' THEN 
#                             CASE 
#                                 WHEN LEFT(ptype, 1) = 'H' AND CAST(width AS FLOAT) >= 100 
#                                     THEN RIGHT('00' + CAST(CAST(width AS INT) AS VARCHAR), 4) + 'RL00'
#                                 WHEN LEFT(ptype, 1) = 'H' OR CAST(width AS FLOAT) < 100 
#                                     THEN 
#                                         CASE 
#                                             WHEN RIGHT(CAST(CAST(width10 AS INT) AS VARCHAR), 1) = '5' 
#                                                 THEN RIGHT('00' + CAST(CAST(width10 AS INT) - 1 AS VARCHAR), 3) + 'KRL00'
#                                             WHEN RIGHT(CAST(CAST(width10 AS INT) AS VARCHAR), 1) = '8' 
#                                                 THEN RIGHT('00' + CAST(CAST(width10 AS INT) - 2 AS VARCHAR), 3) + 'KRL00'
#                                             ELSE RIGHT('00' + CAST(CAST(width10 AS INT) AS VARCHAR), 3) + 'KRL00'
#                                         END
#                                 ELSE 
#                                     RIGHT('00' + CAST(CAST(width AS INT) AS VARCHAR), 4) + 'RL00'
#                             END
#                         WHEN prod IN ('2', '4', '7', '8') THEN 'R'
#                         ELSE NULL 
#                     END AS prodn,
#                     CASE WHEN prod = 1 THEN '成品'
#                     WHEN prod = 2 Then '裁切'
#                     WHEN prod = 4 Then '中倉'
#                     WHEN prod = 7 Then '分條'
#                     WHEN prod = 8 Then '含浸' END AS pstatus
                    
#                     FROM
#                     (
#                         select 
#                             CASE 
#                                 WHEN ABS(width * 10) - FLOOR(ABS(width * 10)) = 0.5
#                                     THEN 
#                                         CASE 
#                                             WHEN FLOOR(ABS(width * 10)) % 2 = 0 
#                                                 THEN FLOOR(width * 10)
#                                             ELSE CEILING(width * 10)
#                                         END
#                                 ELSE ROUND(width * 10, 0)
#                             END AS width10,
#                         adwind.*,b.chsnm
#                         from adwind 
#                         inner join ampaper b on adwind.ptype = b.ptype
#                         where mname in("""+ str(mname_t) +""") and substring(runno,1,1) = """+ str(sub_r) +"""
#                         and bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
#                         and prod not in('3','5','6','9') 
#                         --order by runno, prod, ptype, pclass, width, pgramg, x_yn, relno, swinno     
#                     ) n
#                 ) m 
#             ) t
#             WHERE store NOT LIKE '%SR%'
#             """       
#             query = conn.execute(text(sql))  
#             df_adwind = pd.DataFrame([dict(i) for i in query])
            

# #             sql =   """
# #                 SELECT runno,MAX(replace(core_tube_d,'"','')) AS core_tube_d ,MAX(roll_type) AS roll_type,
# #                 MAX(CASE WHEN x_yn = 'Y' THEN SOLD_TO_CUST_NAME ELSE '' END) AS SOLD_TO_CUST_NAME
# #                 FROm adrunt_edit_temp 
# #                 where y_mk>=YEAR('"""+ str(stime) +"""') AND len(roll_type)>0
# #                 group by runno
# #             """       

#             itemNos = df_adwind['winno'].unique().tolist()
#             # 變成 'A','B','C' 格式
#             in_clause = ",".join(f"'{x}'" for x in itemNos)
#             sql = f"""
#                   SELECT winno,face AS roll_type, diam AS core_tube_d,NULL AS SOLD_TO_CUST_NAME
#                   FROM [SRVADA1].[ERP-A].[dbo].[AprirolltagT]
#                   WHERE winno IN ({in_clause})
#             """            
#             query = conn.execute(text(sql))  
#             df_roll_type = pd.DataFrame([dict(i) for i in query])  # ABD020I1          
            
#         with df_SERVER_CHPGTERPDBAAR01['create_engine'][0].connect() as conn:
#             in_list = ", ".join([f"''{item}''" for item in list(df_adwind['itemNo'].unique())])  # 注意雙單引號
#             sql = f"""
#             SELECT * FROM OPENQUERY(ERPDB, 'SELECT ITEM_NUMBER,CATALOG_ELEM_VAL_010 FROM XXIFV050_ITEMS_FTA_V WHERE ITEM_NUMBER IN ({in_list})')
#             """        
#             query = conn.execute(text(sql))  
#             df_CHPGTERPDBAAR01 = pd.DataFrame([dict(i) for i in query]) 
            
#         df_adwind = df_adwind.merge(df_CHPGTERPDBAAR01,left_on = 'itemNo', right_on = 'ITEM_NUMBER',how='left')
#         df_adwind['store'] = np.where(
#             df_adwind['CATALOG_ELEM_VAL_010'] == 'NCR',
#             'A6FG',
#             df_adwind['store']
#         )               
        
#         df_adwind['note'] = np.where(
#             df_adwind['CATALOG_ELEM_VAL_010'].notna(),
#             '',
#             '料號不存在，請檢查資料正確性'
#         )
        
#         # 將 key 欄位都轉為大寫 20250721新增
#         df_adwind['runno'] = df_adwind['runno'].str.upper()
#         df_batch_no['mes_no'] = df_batch_no['mes_no'].str.upper()
#         # 20250721新增
        
#         df_adwind_merge = df_adwind.merge(df_batch_no,left_on = 'runno',right_on='mes_no',how = 'left')
        
#         df_adwind_merge = df_adwind_merge.merge(df_roll_type,left_on = 'winno',right_on='winno',how = 'left')
        
#         df_adwind_merge['roll_type'] = df_adwind_merge['roll_type'].fillna('')  
#         df_adwind_merge['core_tube_d'] = df_adwind_merge['core_tube_d'].fillna('') 
#         df_adwind_merge['SOLD_TO_CUST_NAME'] = df_adwind_merge['SOLD_TO_CUST_NAME'].fillna('')
        
#         df_result = df_adwind_merge.groupby(['runno','bdate', 'batch_no', 'ptype', 'pgramg','lenth','width','pclass','store',])\
#             .agg(weigh_sum=('weigh', 'sum'), weigh_count=('weigh', 'count'),
#                 roll_type=('roll_type', 'max'),core_tube_d=('core_tube_d', 'max'),SOLD_TO_CUST_NAME=('SOLD_TO_CUST_NAME', 'max'),
#                 note=('note', 'max'))\
#             .reset_index()


# In[44]:


# with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#     display(df_result)


# In[45]:


# stime = '2026-03-10'
# etime = '2026-03-10'
# mname = '21'
# Product_Category = '格拉新'


# In[46]:



# with df_SERVER_SRVMESDBA1['create_engine'][0].connect() as conn:        
#     sql =   """
#         SELECT [saleclass]
#               ,[class]
#               ,[ptype2]
#               ,[chsnm]
#               ,[ptype]
#               ,[chlnm]
#           FROM [AMIS].[dbo].[ampaper_category]
#           WHERE plant_id = 'A'
#           AND len(saleclass) > 0
#           order by saleclass,ptype2,ptype
#     """
#     query = conn.execute(text(sql))  
#     df_Ampaper_category = pd.DataFrame([dict(i) for i in query])


# MachineCode = 'R1'

# params = (MachineCode, stime, etime, "N")
# query = "EXEC a_r_day_report_sp @mname=?, @sdate=?, @edate=?, @shft=?"

# with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:        
#     df_result = pd.read_sql(query, conn, params=params)

# if not df_result.empty:
#     df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

#     df_result_groupby = df_result.groupby(['bdate','class'])\
#         .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)\
#         .reset_index()

#     df_result_groupby['lenth_rate'] = np.where(
#         (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
#         round((df_result_groupby['lenth'] - df_result_groupby['back']) / df_result_groupby['blenth'] * 100, 2),
#         0
#     )

#     df_result_groupby['defective_quantity'] = np.where(
#         (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
#         round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
#         0
#     )
#     # 儲存成1號再捲機結果
#     df_result_R1 = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

#     df_result_R1.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
# else:
#     df_result_R1 = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    

# # ------------------------------------------------------------------
# MachineCode = 'C1'

# params = (MachineCode, stime, etime, "N")
# query = "EXEC a_c_day_report_sp @mname=?, @sdate=?, @edate=?, @shft=?"

# with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:        
#     df_result = pd.read_sql(query, conn, params=params)

# if not df_result.empty:    
#     df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

#     df_result_groupby = df_result.groupby(['bdate','class'])\
#         .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)\
#         .reset_index()

#     df_result_groupby['lenth_rate'] = np.where(
#         (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
#         round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
#         0
#     )

#     df_result_groupby['defective_quantity'] = np.where(
#         (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
#         round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
#         0
#     )
#     # 儲存成1號塗佈機結果
#     df_result_C1 = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

#     df_result_C1.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
# else:
#     df_result_C1 = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    



# # ------------------------------------------------------------------
# MachineCode = 'EA'
# mname = '21'

# params = (MachineCode, mname, stime, etime, "N")
# query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

# with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:
#     df_result = pd.read_sql(query, conn, params=params)

# if not df_result.empty:
#     df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

#     df_result_groupby = df_result.groupby(['bdate','class'])\
#         .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)\
#         .reset_index()

#     df_result_groupby['lenth_rate'] = np.where(
#         (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
#         round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
#         0
#     )

#     df_result_groupby['defective_quantity'] = np.where(
#         (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
#         round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
#         0
#     )
#     # 儲存成1號塗佈機結果
#     df_result_EA = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

#     df_result_EA.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
# else:
#     df_result_EA = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    


# # ------------------------------------------------------------------
# MachineCode = 'EB'
# mname = '21'

# params = (MachineCode, mname, stime, etime, "N")
# query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

# with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:
#     df_result = pd.read_sql(query, conn, params=params)

# if not df_result.empty:    
#     df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

#     df_result_groupby = df_result.groupby(['bdate','class'])\
#         .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)\
#         .reset_index()

#     df_result_groupby['lenth_rate'] = np.where(
#         (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
#         round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
#         0
#     )

#     df_result_groupby['defective_quantity'] = np.where(
#         (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
#         round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
#         0
#     )
#     # 儲存成1號塗佈機結果
#     df_result_EB = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

#     df_result_EB.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
# else:
#     df_result_EB = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    

# # ------------------------------------------------------------------
# MachineCode = 'EC'
# mname = '21'

# params = (MachineCode, mname, stime, etime, "N")
# query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

# with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:
#     df_result = pd.read_sql(query, conn, params=params)

# if not df_result.empty:
#     df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

#     df_result_groupby = df_result.groupby(['bdate','class'])\
#         .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)\
#         .reset_index()

#     df_result_groupby['lenth_rate'] = np.where(
#         (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
#         round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
#         0
#     )

#     df_result_groupby['defective_quantity'] = np.where(
#         (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
#         round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
#         0
#     )
#     # 儲存成1號塗佈機結果
#     df_result_EC = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

#     df_result_EC.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
# else:
#     df_result_EC = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])    

# # ------------------------------------------------------------------
# MachineCode = 'ED'
# mname = '21'

# params = (MachineCode, mname, stime, etime, "N")
# query = "EXEC a_e_day_report_sp @mname=?,@pm=?, @sdate=?, @edate=?, @shft=?"            

# with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:
#     df_result = pd.read_sql(query, conn, params=params)

# if not df_result.empty:
#     df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

#     df_result_groupby = df_result.groupby(['bdate','class'])\
#         .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),back=('back','sum'),blenth=('blenth','sum'),)\
#         .reset_index()

#     df_result_groupby['lenth_rate'] = np.where(
#         (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
#         round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
#         0
#     )

#     df_result_groupby['defective_quantity'] = np.where(
#         (df_result_groupby['lenth_rate'].notna()) & (df_result_groupby['lenth_rate'] != 0),
#         round(((df_result_groupby['weigh'] / df_result_groupby['lenth_rate'] * 100) - df_result_groupby['weigh']), 1),
#         0
#     )
#     # 儲存成1號塗佈機結果
#     df_result_ED = df_result_groupby.loc[:,['bdate','class','weigh','lenth_rate','defective_quantity']].copy()

#     df_result_ED.columns = ['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode]
# else:
#     df_result_ED = pd.DataFrame(columns=['bdate','class','weigh_'+MachineCode,'lenth_rate_'+MachineCode,'defective_quantity_'+MachineCode])        


# # ------------------------------------------------------------------


# In[47]:


# def find_W_quality(stime, etime, MachineCode):

#     with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:
#         sql =   """

#      ;WITH raw_data as
#      (
#             select 
#                 aa.bdate,aa.mname, aa.ptype, sum(aa.tl) as tl, sum(aa.pht) as pht, sum(aa.s5) as s5, sum(aa.s6) as s6,
#                 CASE WHEN ptype IN ('KL00','SL00','SL0C','KV00') THEN '格拉新' 
#                      WHEN ptype IN ('KWCL','KWCA') THEN 'CCK' 
#                      ELSE '1' END AS IS_KL
#             from (
#                 select a.y_mk, a.mname, a.relno, a.ptype, 
#                 convert(decimal(18,3),
#                     (convert(decimal(18,2),
#                             convert(decimal(18,3) ,
#                                 case a.patch when 'C' then a.blenth+a.plenth 
#                                              when 'S' then a.blenth-a.plenth 
#                                              else a.blenth end * convert(decimal(12,0),a.barea/a.blenth*1000)/1000
#                                 ) / 
#                                 case a.patch when 'C' then a.blenth+a.plenth 
#                                              when 'S' then a.blenth-a.plenth 
#                                              else a.blenth end * 1000
#                             )- convert(decimal(18,2),a.warea/a.lenth*1000)
#                     ) * a.lenth * a.pgramg / 1000000000
#                 ) as tl, 
#                             convert(decimal(18,3),
#                             (case a.patch when 'C' then a.blenth+a.plenth 
#                                           when 'S' then a.blenth-a.plenth 
#                                           else a.blenth end - a.lenth) * 
#                             convert(decimal(18,2),convert(decimal(18,3),
#                             case a.patch when 'C' then a.blenth+a.plenth 
#                                          when 'S' then a.blenth-a.plenth 
#                                          else a.blenth end * 
#                             convert(decimal(12,0),a.barea/a.blenth*1000)/1000) / 
#                             case a.patch when 'C' then a.blenth+a.plenth 
#                                          when 'S' then a.blenth-a.plenth 
#                                          else a.blenth end * 1000)* a.pgramg / 1000000000) as pht, 
#                             convert(decimal(18,3),case when sum(b.area) > 0 then sum(b.area) else 0 end * a.pgramg /1000000) as s5,
#                             convert(decimal(18,3),case when sum(c.area) > 0 then sum(c.area) else 0 end * a.pgramg /1000000) as s6, 
#                             a.bdate
#                 from amwind a
#                 left join (
#                     select adb.mname, adb.relno, sum(adb.lenth) as 'lenth', sum(adb.area) as 'area'
#                     from (
#                         select mname, relno, winsno, bdate, lenth, 
#                         sum(case when width<100 then width*25.4 else width end) as 'width', 
#                         lenth*sum(case when width<100 then width*25.4 else width end)/1000 as 'area'
#                         from [AMIS].[dbo].[adwind] 
#                         where prod in(5) 
#                         group by mname, relno, winsno, bdate, pgramg, lenth
#                     ) adb 
#                     group by adb.mname, adb.relno
#                 ) b on a.mname = b.mname and a.relno = b.relno 
#                 left join (
#                     select adb.mname, adb.relno, sum(adb.lenth) as 'lenth', sum(adb.area) as 'area'
#                     from (
#                         select mname, relno, winsno, bdate, lenth, 
#                         sum(case when width<100 then width*25.4 else width end) as 'width', 
#                         lenth*sum(case when width<100 then width*25.4 else width end)/1000 as 'area' 
#                         from [AMIS].[dbo].[adwind] 
#                         where prod in(6) 
#                         group by mname, relno, winsno, bdate, pgramg, lenth
#                     )adb
#                     group by adb.mname, adb.relno
#                 ) c on a.mname = c.mname and a.relno = c.relno 
#                 group by a.y_mk, a.mname, a.relno, a.ptype, a.pgramg, a.patch, a.blenth, a.plenth, a.lenth, a.barea, a.warea, a.weigh, a.bdate
#             ) aa
#             where aa.mname = '"""+ str(MachineCode) +"""' and aa.bdate between convert(varchar(10), '"""+ str(stime) +"""', 111) and convert(varchar(10), '"""+ str(etime) +"""', 111) 
#             group by aa.bdate,aa.mname, aa.ptype 
#             --order by aa.bdate,aa.mname, aa.ptype      
#      )
#       SELECT t.bdate,t.mname,t.ptype,t.tl,t.pht,
#           CASE WHEN (SELECT COUNT(*) FROM raw_data WHERE ptype IN ('SL00','KL00','SL0C','KV00')) = 1 and t.IS_KL = '格拉新' AND n.weigh>ISNULL(m.weigh,0) THEN n.weigh 
#                WHEN (SELECT COUNT(*) FROM raw_data WHERE ptype IN ('KWCA','KWCL')) = 1 and t.IS_KL = 'CCK' AND n.weigh>ISNULL(m.weigh,0) THEN n.weigh
#           ELSE m.weigh END as s5,
#           t.s6
#         FROM raw_data t
#         LEFT JOIN (
#             select t.bdate,t.mname, t.ptype ,sum(weigh) as weigh
#             from
#             (
#                 SELECT chkno,code,dest,pgramg,gramg,weigh,ptype,bdate,mname
#                 FROM (
#                     select a.chkno, a.code, b.dest,c.pgramg,c.gramg,c.weigh,c.ptype,a.bdate,a.mname,
#                         ROW_NUMBER() OVER (
#                             PARTITION BY a.chkno, c.ptype, c.gramg, c.pgramg, c.weigh 
#                             ORDER BY a.code
#                         ) AS rn
#                     from adqumk a
#                     inner join adcode b on b.code = a.code and b.pgid='QUMK'
#                     inner join adrecycle c on a.chkno=c.chkno
#                     inner join (
#                         select chkno from adrecycle 
#                         where bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
#                         and mname = '"""+ str(MachineCode) +"""'
#                         and weigh > 0 and status = 'B' and reason <> '紙頭紙尾' and status1 is null
#                     ) adrecycle_2 on adrecycle_2.chkno = a.chkno
#                     where 1=1
#                     and a.mname = '"""+ str(MachineCode) +"""'
#                 ) t
#                 WHERE t.rn = 1   
#             ) t
#             group by t.bdate,t.mname, t.ptype 
#         ) m on t.bdate = m.bdate and t.mname = m.mname and t.ptype = m.ptype
#         LEFT JOIN (
#             select t.bdate,t.mname, t.IS_KL ,sum(weigh) as weigh
#             from
#             (
#                 SELECT chkno,code,dest,pgramg,gramg,weigh,ptype,bdate,mname,
#                 CASE WHEN ptype IN ('KL00','SL00','SL0C','KV00') THEN '格拉新' 
#                      WHEN ptype IN ('KWCL','KWCA') THEN 'CCK'
#                      ELSE '1' END AS IS_KL
#                 FROM (
#                     select a.chkno, a.code, b.dest,c.pgramg,c.gramg,c.weigh,c.ptype,a.bdate,a.mname,
#                         ROW_NUMBER() OVER (
#                             PARTITION BY a.chkno, c.ptype, c.gramg, c.pgramg, c.weigh 
#                             ORDER BY a.code
#                         ) AS rn
#                     from adqumk a
#                     inner join adcode b on b.code = a.code and b.pgid='QUMK'
#                     inner join adrecycle c on a.chkno=c.chkno
#                     inner join (
#                         select chkno from adrecycle 
#                         where bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
#                         and mname = '"""+ str(MachineCode) +"""'
#                         and weigh > 0 and status = 'B' and reason <> '紙頭紙尾' and status1 is null
#                     ) adrecycle_2 on adrecycle_2.chkno = a.chkno
#                     where 1=1
#                     and a.mname = '"""+ str(MachineCode) +"""'
#                 ) t
#                 WHERE t.rn = 1   
#             ) t
#             group by t.bdate,t.mname, t.IS_KL
#         ) n on t.bdate = n.bdate and t.mname = n.mname and t.IS_KL = n.IS_KL        

#         """       
#         query = conn.execute(text(sql))
#         df_result_W_quality = pd.DataFrame([dict(i) for i in query])  

#         df_result_W_quality['s5'] = df_result_W_quality['s5'].astype(float)
#         df_result_W_quality['s6'] = df_result_W_quality['s6'].astype(float)

#     return df_result_W_quality

# def find_W_amwind(stime, etime, MachineCode):
#     if stime == etime:
#         stime_t = stime
#         etime_t = str((datetime.datetime.strptime(etime, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'))
#     else:
#         stime_t = stime
#         etime_t = etime

#     stime_t_1 = str((datetime.datetime.strptime(stime, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d'))
    
#     stime_t_month = str((datetime.datetime.strptime(stime, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d'))

#     with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:            
#         sql =   """
#         select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
#                             c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
#                             (case when a.patch='S' then a.blenth-a.plenth-t.olenth else a.blenth+a.plenth end) as blenth,
#                             (case when a.patch='S' then a.barea-a.parea-t.oarea else a.barea+a.parea end) as barea,
#                             (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
#                             (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
#                         FROM  amwind a 
#                         INNER JOIN ampaper b ON a.ptype = b.ptype 
#                         Left JOIN amrunt c ON a.runno = c.runno
#                         left join (
#                             select 
#                                 mname, 
#                                 relno, 
#                                 sum(olenth) as olenth, 
#                                 convert(decimal(12,3),sum(olenth)*width/1000) as oarea 
#                             from (
#                                 select a.mname, a.y_mk, a.relno, a.winsno, a.runno, a.bdate, a.olenth, 
#                                 case when b.width<100 then b.width*25.4 else b.width end as 'width' 
#                                 from adwind a
#                                 left join amwind b on a.relno = b.relno 
#                                 where 1=1
#                                 --and a.mname='WB' 
#                                 and a.y_mk >= year(getdate())-8 
#                                 and a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""'
#                                 and a.mname= '"""+ str(MachineCode) +"""'
#                                 group by a.mname, a.y_mk, a.relno, a.winsno, a.runno, a.bdate, a.olenth, b.width
#                             ) o
#                             group by mname, relno, width
#                         ) t on t.relno = a.relno                                
#                         WHERE  a.bdate between '"""+ str(stime_t_1) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""'
#                         and a.flag = 'Y'
#                         GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk,t.olenth,t.oarea
#                         ORDER BY  a.pdate, a.relno
#         """       
#         query = conn.execute(text(sql))
#         df_result = pd.DataFrame([dict(i) for i in query])

#         sql =   """
#             SELECT bdate,ptype,sum(width) AS width,count(*) as winsno
#             FROM
#             (
#                 SELECT bdate,relno,winsno,sum(width) AS width,MAX(ptype) AS ptype
#                 FROM
#                 (                    
#                     select 
#                         a.bdate,a.relno,a.winno,a.swinno,a.ptype,a.pclass,a.pgramg,a.width,a.lenth,a.weigh,a.splice,a.prod,a.roll,a.olenth,a.winsno
#                     from adwind a 
#                     where a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and a.mname = '"""+ str(MachineCode) +"""' AND prod != '6'
#                     AND relno IN
#                     (
#                         select distinct relno
#                         from
#                         (
#                         select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
#                                             c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
#                                             (case when a.patch='S' then a.blenth-a.plenth else a.blenth+a.plenth end) as blenth,
#                                             (case when a.patch='S' then a.barea-a.parea else a.barea+a.parea end) as barea,
#                                             (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
#                                             (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
#                                         FROM  amwind a 
#                                         INNER JOIN ampaper b ON a.ptype = b.ptype 
#                                         Left JOIN amrunt c ON a.runno = c.runno  
#                                         WHERE  a.bdate between '"""+ str(stime_t_1) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""'
#                                         GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk    
#                           ) t
#                     )
#                 ) m 
#                 group by bdate,relno,winsno
#             ) n 
#             group by bdate,ptype
#         """       
#         query = conn.execute(text(sql))
#         df_result_width = pd.DataFrame([dict(i) for i in query]) 

#         sql =   """
#             SELECT bdate,ptype,sum(weigh) AS weigh,count(*) as winsno
#             FROM
#             (
#                 SELECT bdate,relno,winsno,sum(weigh) AS weigh,MAX(ptype) AS ptype
#                 FROM
#                 (                    
#                     select 
#                         a.bdate,a.relno,a.winno,a.swinno,a.ptype,a.pclass,a.pgramg,a.width,a.lenth,a.weigh,a.splice,a.prod,a.roll,a.olenth,a.winsno
#                     from adwind a 
#                     where a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' and a.mname = '"""+ str(MachineCode) +"""'
#                     AND relno IN
#                     (
#                         select distinct relno
#                         from
#                         (
#                         select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
#                                             c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
#                                             (case when a.patch='S' then a.blenth-a.plenth else a.blenth+a.plenth end) as blenth,
#                                             (case when a.patch='S' then a.barea-a.parea else a.barea+a.parea end) as barea,
#                                             (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
#                                             (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
#                                         FROM  amwind a 
#                                         INNER JOIN ampaper b ON a.ptype = b.ptype 
#                                         Left JOIN amrunt c ON a.runno = c.runno  
#                                         WHERE  a.bdate between '"""+ str(stime_t_1) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""'
#                                         GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk    
#                           ) t
#                     )
#                 ) m 
#                 group by bdate,relno,winsno
#             ) n 
#             group by bdate,ptype
#         """       
#         query = conn.execute(text(sql))
#         df_result_weigh = pd.DataFrame([dict(i) for i in query])

#         sql =   """
#                 SELECT bdate,relno,winsno,lenth,MAX(ptype) AS ptype
#                 FROM
#                 (
#                     select 
#                         a.bdate,a.relno,a.winno,a.swinno,a.ptype,a.pclass,a.pgramg,a.width,a.lenth,a.weigh,a.splice,a.prod,a.roll,a.olenth,a.winsno
#                     from adwind a 
#                     where a.bdate between '"""+ str(stime_t_month) +"""' and '"""+ str(etime_t) +"""' and a.mname = '"""+ str(MachineCode) +"""'
#                     AND relno IN
#                     (
#                         select distinct relno
#                         from
#                         (
#                         select a.relno,a.sno,a.runno,a.ptype,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,
#                                             c.pgramg AS sgramg,a.pdate,a.shft,a.width,a.lenth,sum(a.weigh) as weigh,a.flag,a.musr,
#                                             (case when a.patch='S' then a.blenth-a.plenth else a.blenth+a.plenth end) as blenth,
#                                             (case when a.patch='S' then a.barea-a.parea else a.barea+a.parea end) as barea,
#                                             (case when a.patch='S' then '有退紙' when a.patch='C' then '有接紙' else '' end) as patch,
#                                             (case when a.ptype=c.ptype and c.ptype not like '%NCR%' then '' when c.ptype like '%NCR%' then isnull((select top(1) '' from adrunt where runno =c.runno and y_mk=c.y_mk and ptype =a.ptype),'DIFF') else 'DIFF' end) as srunno 
#                                         FROM  amwind a 
#                                         INNER JOIN ampaper b ON a.ptype = b.ptype 
#                                         Left JOIN amrunt c ON a.runno = c.runno  
#                                         WHERE  a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime_t) +"""' and a.y_mk > year(getdate())-8 and a.mname= '"""+ str(MachineCode) +"""' AND a.flag = 'Y'
#                                         GROUP BY a.relno,a.sno,a.runno,a.ptype,a.musr,b.chsnm,a.gramg,a.pgramg,a.winset,a.speed,a.warea,a.ptime,c.pgramg,a.pdate,a.shft,a.width,a.lenth,a.flag,patch,blenth,barea,plenth,parea,c.ptype,c.runno,c.y_mk    
#                           ) t
#                     )
#                 ) m 
#                 group by bdate,relno,winsno,lenth
#         """       
#         query = conn.execute(text(sql))
#         df_result_lenth = pd.DataFrame([dict(i) for i in query])                

#     df_result_width = df_result_width.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result_weigh = df_result_weigh.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#     df_result_lenth = df_result_lenth.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')                      

#     df_result_lenth = df_result_lenth.groupby(['bdate','relno','winsno','ptype','class'])\
#         .agg(lenth=('lenth','max')).reset_index() 

#     print('df_result')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result)
#     print('df_result_width')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_width)         
#     print('df_result_weigh')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_weigh)         
#     print('df_result_lenth')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_lenth)               

#     df_result_width_groupby = df_result_width.groupby(['bdate','class'])\
#         .agg(width=('width','sum'),winsno=('winsno','sum'))\
#         .reset_index()

#     df_result_weigh_groupby = df_result_weigh.groupby(['bdate','class'])\
#         .agg(weigh2=('weigh','sum'),winsno=('winsno','sum'))\
#         .reset_index()

#     df_result_lenth_groupby = df_result_lenth.groupby(['bdate','class'])\
#         .agg(lenth2=('lenth','sum'),winsno=('winsno','sum'))\
#         .reset_index() 

#     print('df_result_width_groupby')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_width_groupby)         
#     print('df_result_weigh_groupby')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_weigh_groupby)         
#     print('df_result_lenth_groupby')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_lenth_groupby.sort_values(by=['bdate','class','winsno','lenth2']))                

#     df_result_lenth_Cross_day_relno = df_result_lenth.groupby(['relno','bdate']).size().reset_index().groupby(['relno']).size()

#     print('df_result_lenth_Cross_day_relno')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_lenth_Cross_day_relno)            

#     df_result_lenth_Cross_day_relno = df_result_lenth_Cross_day_relno[df_result_lenth_Cross_day_relno>1].reset_index()

#     print('df_result_lenth_Cross_day_relno')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_lenth_Cross_day_relno)  

#     df_result_lenth_Cross_day = df_result_lenth[df_result_lenth['relno'].isin(list(df_result_lenth_Cross_day_relno['relno']))]\
#     .groupby(['bdate','relno'])['lenth'].sum().reset_index()
#     df_result_lenth_Cross_day.rename(columns={'lenth':'lenth2'},inplace=True)
#     df_result_lenth_Cross_day['bdate'] = pd.to_datetime(df_result_lenth_Cross_day['bdate']).dt.date.astype(object) 

#     print('df_result_lenth_Cross_day')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_lenth_Cross_day)
        
#     df_result_lenth_Cross_day = df_result_lenth_Cross_day[df_result_lenth_Cross_day['bdate']==\
#                                                           datetime.datetime.strptime(stime, '%Y-%m-%d').date()].\
#                                                           reset_index(drop=True)
#     df_result_lenth_Cross_day = df_result_lenth_Cross_day.loc[:,['relno','lenth2']]
    
#     print('df_result_lenth_Cross_day')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_lenth_Cross_day)    

#     df_result = df_result.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')

#     df_result["bdate"] = (df_result["pdate"] - pd.Timedelta(hours=8)).dt.date  # 減 8 小時並擷取日期  

#     df_result = df_result.merge(df_result_lenth_Cross_day,on=['relno'],how='left')
#     df_result['blenth'] = np.where(
#                 (df_result['lenth2'].notna()) & (df_result['lenth2'] != 0),
#                 df_result['lenth2'],
#                 df_result['blenth']
#             )      
    
#     df_result = df_result[(df_result['bdate']==datetime.datetime.strptime(stime, '%Y-%m-%d').date()) |\
#                           (~df_result['lenth2'].isna())].reset_index(drop=True)
    
#     df_result["bdate"] = datetime.datetime.strptime(stime, '%Y-%m-%d').date()
    
#     df_result['lenth'] = np.where(
#         df_result['lenth'] <= df_result['blenth'],
#         df_result['lenth'],
#         df_result['blenth']
#     )    
    
#     print('df_result(modify blenth)')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result)
        
#     df_result_groupby = df_result.groupby(['bdate','class'])\
#         .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),blenth=('blenth','sum'),winset=('winset','sum'))\
#         .reset_index()        

#     df_result_groupby['weigh'] = df_result_groupby['weigh'].astype(float)
#     df_result_groupby['bdate'] = pd.to_datetime(df_result_groupby['bdate'])
    
#     print('df_result_groupby')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_groupby)     

#     if stime == etime:
#         df_result_groupby['bdate'] = df_result_groupby['bdate'].min()
#         df_result_groupby = df_result_groupby.groupby(['bdate','class'])\
#             .agg(weigh=('weigh','sum'),lenth=('lenth','sum'),blenth=('blenth','sum'),winset=('winset','sum'))\
#             .reset_index()
#         df_result_groupby = df_result_groupby.merge(df_result_width_groupby.loc[:,['bdate','class','width','winsno']],
#                                                     on = ['bdate','class'],
#                                                     how='outer')                
#     else:
#         df_result_groupby = df_result_groupby.merge(df_result_width_groupby.loc[:,['bdate','class','width','winsno']],
#                                                     on = ['bdate','class'],
#                                                     how='left')                 

#     df_result_groupby = df_result_groupby.merge(df_result_weigh_groupby.loc[:,['bdate','class','weigh2']],
#                                                 on = ['bdate','class'],
#                                                 how='left')
#     df_result_groupby = df_result_groupby.merge(df_result_lenth_groupby.loc[:,['bdate','class','lenth2']],
#                                                 on = ['bdate','class'],
#                                                 how='left')        
        
#     print('df_result_groupby')
#     with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#         display(df_result_groupby)     

#     df_result_groupby['lenth'] = np.where(
#                 df_result_groupby['lenth2']<=df_result_groupby['lenth'],
#                 df_result_groupby['lenth2'],
#                 df_result_groupby['lenth']
#             )                       

#     df_result_groupby['width'] = df_result_groupby['width'].astype(float)
#     df_result_groupby['winsno'] = df_result_groupby['winsno'].astype(float)
#     df_result_groupby['weigh'] = df_result_groupby['weigh2'].copy().astype(float)

#     return df_result_groupby

# def find_W_quality_reason(stime, etime, MachineCode):
#     with df_SERVER_SRVAD1['create_engine'][0].connect() as conn:            
#         sql =   """          
#             SELECT bdate, ptype, dest,sum(weigh) as weigh
#             FROM
#             (
#                 SELECT chkno,code,dest,pgramg,gramg,weigh,ptype,bdate
#                 FROM (
#                     select a.chkno, a.code, b.dest,c.pgramg,c.gramg,c.weigh,c.ptype,a.bdate,
#                         ROW_NUMBER() OVER (
#                             PARTITION BY a.chkno, c.ptype, c.gramg, c.pgramg, c.weigh 
#                             ORDER BY a.code
#                         ) AS rn
#                     from adqumk a
#                     inner join adcode b on b.code = a.code and b.pgid='QUMK'
#                     inner join adrecycle c on a.chkno=c.chkno
#                     inner join (
#                         select chkno from adrecycle 
#                         where bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
#                         and mname = '"""+ str(MachineCode) +"""'
#                         and weigh > 0 and status = 'B' and reason <> '紙頭紙尾' and status1 is null
#                     ) adrecycle_2 on adrecycle_2.chkno = a.chkno
#                     where 1=1
#                     and a.mname = '"""+ str(MachineCode) +"""'
#                     and a.bdate between '"""+ str(stime) +"""' and '"""+ str(etime) +"""' 
#                 ) t
#                 WHERE t.rn = 1                    
#             ) t
#             group by bdate, ptype, dest
#             order by bdate, ptype, dest                
#         """
#         query = conn.execute(text(sql))
#         df_result = pd.DataFrame([dict(i) for i in query])   

#     return df_result

# def find_W_Summary(stime, etime, df_Ampaper_category):

#     start_date = datetime.datetime.strptime(stime, '%Y-%m-%d')
#     end_date = datetime.datetime.strptime(etime, '%Y-%m-%d')

#     current_date = start_date

#     df_result_W_t = pd.DataFrame()
#     df_result_W_quality_reason_t = pd.DataFrame()

#     while current_date <= end_date:

#         date_str = current_date.strftime('%Y-%m-%d')

#         MachineCode = 'WA'

#         df_result_WA_quality = find_W_quality(date_str, date_str, MachineCode)
#         df_result_WA_quality = df_result_WA_quality.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#         df_result_WA_quality = df_result_WA_quality.groupby(['bdate','class'])\
#             .agg(tl=('tl','sum'),pht=('pht','sum'),s5=('s5','sum'),s6=('s6','sum'))\
#             .reset_index()
#         df_result_WA_quality['bdate'] = pd.to_datetime(df_result_WA_quality['bdate'])

#         print('df_result_WA_quality')
#         with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#             display(df_result_WA_quality)

#         df_result_WA_quality_reason = find_W_quality_reason(date_str, date_str, MachineCode)

#         print('df_result_WA_quality_reason')
#         with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#             display(df_result_WA_quality_reason)

#         df_result_WA = find_W_amwind(date_str, date_str, MachineCode)

#         print('df_result_WA')
#         with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#             display(df_result_WA)                

#         df_result_WA = df_result_WA.merge(df_result_WA_quality,on = ['bdate','class'],how='left')

#         MachineCode = 'WB'

#         df_result_WB_quality = find_W_quality(date_str, date_str, MachineCode)               
#         df_result_WB_quality = df_result_WB_quality.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#         df_result_WB_quality = df_result_WB_quality.groupby(['bdate','class'])\
#             .agg(tl=('tl','sum'),pht=('pht','sum'),s5=('s5','sum'),s6=('s6','sum'))\
#             .reset_index()
#         df_result_WB_quality['bdate'] = pd.to_datetime(df_result_WB_quality['bdate'])

#         print('df_result_WB_quality')
#         with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#             display(df_result_WB_quality)                

#         df_result_WB_quality_reason = find_W_quality_reason(date_str, date_str, MachineCode)

#         print('df_result_WB_quality_reason')
#         with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#             display(df_result_WB_quality_reason)                

#         df_result_WB = find_W_amwind(date_str, date_str, MachineCode)

#         print('df_result_WB')
#         with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#             display(df_result_WB)

#         df_result_WB = df_result_WB.merge(df_result_WB_quality,on = ['bdate','class'],how='left')

#         df_result_W_quality_reason = pd.concat([df_result_WA_quality_reason,df_result_WB_quality_reason]).reset_index(drop=True)
#         df_result_W_quality_reason = df_result_W_quality_reason.groupby(['bdate','ptype','dest'])['weigh'].sum().reset_index()

#         if not df_result_W_quality_reason.empty:
#             df_result_W_quality_reason = df_result_W_quality_reason.merge(df_Ampaper_category.loc[:,['class','ptype']],on = ['ptype'],how='left')
#             df_result_W_quality_reason = df_result_W_quality_reason.groupby(['bdate','class','dest'])['weigh'].sum().reset_index()
#             df_result_W_quality_reason = (
#                 df_result_W_quality_reason
#                 .groupby(['bdate','class'])
#                 .agg(
#                     reason_str=('dest', lambda x: ''.join(
#                         x + df_result_W_quality_reason.loc[x.index,'weigh'].round(3).astype(str) + 'T'
#                     )),
#                     weigh_sum=('weigh','sum')
#                 )
#                 .reset_index()
#             )
#             df_result_W_quality_reason.columns = ['bdate', 'class', 'df_result_W_reason_str','weigh_sum']
#             df_result_W_quality_reason['bdate'] = pd.to_datetime(df_result_W_quality_reason['bdate']).dt.date.astype(object)
#         else:
#             df_result_W_quality_reason = pd.DataFrame(columns=['bdate', 'class', 'df_result_W_reason_str','weigh_sum'])          

#         df_result_groupby = pd.concat([df_result_WA, df_result_WB], ignore_index=True).groupby(['bdate', 'class'], as_index=False)[['weigh', 'lenth', 'blenth','winset','tl','pht','s5','s6','width','winsno']].sum()

#         print('df_result_groupby')
#         with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#             display(df_result_groupby)                

#         df_result_groupby['weigh'] = df_result_groupby['weigh'] - df_result_groupby['s5'] - df_result_groupby['s6']
#         df_result_groupby['paper_head_tail_ton_rate'] = np.where(
#             (df_result_groupby['blenth'].notna()) & (df_result_groupby['blenth'] != 0),
#             round((df_result_groupby['lenth']) / df_result_groupby['blenth'] * 100, 2),
#             0
#         )


#         df_result_groupby['width_rate'] = np.where(
#             (df_result_groupby['width'].notna()) & (df_result_groupby['width'] != 0),
#             round((df_result_groupby['width'] / (df_result_groupby['winsno'] * 4930) *100), 2),
#             0
#         )

#         df_result_groupby['width_rate'] = np.where(df_result_groupby['width_rate']>100,100,df_result_groupby['width_rate'])


#         df_result_groupby['lenth_ton'] = (df_result_groupby['weigh'] / df_result_groupby['paper_head_tail_ton_rate'] * 100) - df_result_groupby['weigh'] + df_result_groupby['s5']
#         df_result_groupby['width_ton'] = (df_result_groupby['weigh'] / df_result_groupby['width_rate'] * 100) - df_result_groupby['weigh']


#         df_result_groupby['quality_ton'] = df_result_groupby['s5']
#         df_result_groupby['paper_head_tail_ton'] = df_result_groupby['lenth_ton'] - df_result_groupby['quality_ton']

#         df_result_groupby['lenth_rate'] = np.where(
#             ((df_result_groupby['weigh'] + df_result_groupby['lenth_ton']).notna()) & ((df_result_groupby['weigh'] + df_result_groupby['lenth_ton']) != 0),
#             round((df_result_groupby['weigh'] / (df_result_groupby['weigh'] + df_result_groupby['lenth_ton']) * 100), 2),
#             0
#         )

#         df_result_W = df_result_groupby.loc[:,['bdate','class','weigh','paper_head_tail_ton_rate','lenth_rate','width_rate',
#                                  'paper_head_tail_ton','lenth_ton','width_ton','quality_ton']]
#         df_result_W.columns = ['bdate','class','weigh_'+'W','paper_head_tail_ton_rate_'+'W','lenth_rate_'+'W','width_rate_'+'W',
#                                  'paper_head_tail_ton_'+'W','lenth_ton_'+'W','width_ton_'+'W','quality_ton_'+'W']
#         df_result_W['bdate'] = pd.to_datetime(df_result_W['bdate']).dt.date.astype(object)    

#         df_result_W_t = pd.concat([df_result_W_t,df_result_W],ignore_index=True)
#         df_result_W_quality_reason_t = pd.concat([df_result_W_quality_reason_t,df_result_W_quality_reason],ignore_index=True)

#         current_date += timedelta(days=1) 

#     return df_result_W_t,df_result_W_quality_reason_t

# df_result_W,df_result_W_quality_reason = find_W_Summary(stime, etime, df_Ampaper_category)

# df_keys = pd.concat([
#     df_result_R1[['bdate', 'class']],
#     df_result_C1[['bdate', 'class']],
#     df_result_EA[['bdate', 'class']],
#     df_result_EB[['bdate', 'class']],
#     df_result_EC[['bdate', 'class']],
#     df_result_ED[['bdate', 'class']],
#     df_result_W[['bdate', 'class']],
#     df_result_W_quality_reason[['bdate', 'class']]
# ], ignore_index=True).drop_duplicates().sort_values(by=['bdate', 'class'])

# # 2. 以所有出現過的 bdate/class 為主表，依序 left join 其他表
# df_result = df_keys \
#     .merge(df_result_R1, on=['bdate', 'class'], how='left') \
#     .merge(df_result_C1, on=['bdate', 'class'], how='left') \
#     .merge(df_result_EA, on=['bdate', 'class'], how='left') \
#     .merge(df_result_EB, on=['bdate', 'class'], how='left') \
#     .merge(df_result_EC, on=['bdate', 'class'], how='left') \
#     .merge(df_result_ED, on=['bdate', 'class'], how='left') \
#     .merge(df_result_W, on=['bdate', 'class'], how='left') \
#     .merge(df_result_W_quality_reason, on=['bdate', 'class'], how='left')        

# df_result['defective_reasons_ED'] = '紙頭紙尾'    
# df_result = df_result[df_result['class']==Product_Category]

# mask = ~np.isclose(df_result['quality_ton_W'], df_result['weigh_sum'])
# df_result.loc[mask, 'quality_ton_W'] = df_result.loc[mask, 'weigh_sum']        
# df_result.drop(columns=['weigh_sum'], inplace=True)

# df_result_summary = df_result.replace([np.inf, -np.inf], np.nan).fillna(0)\
#                     .groupby(['class']).sum(numeric_only=True).reset_index()

# for l in ['R1','C1','EA','EB','EC','ED']:
#     col_def = 'defective_quantity_' + l
#     col_weigh = 'weigh_' + l
#     col_rate = 'lenth_rate_' + l            

#     if col_def not in df_result_summary.columns:
#         df_result_summary[col_def] = np.nan
#     else:
#         df_result_summary[col_def] = df_result_summary[col_def].round(1)
#     if col_weigh not in df_result_summary.columns:
#         df_result_summary[col_weigh] = np.nan
#     else:
#         df_result_summary[col_weigh] = df_result_summary[col_weigh].round(3)

#     total = df_result_summary[col_def].fillna(0) + df_result_summary[col_weigh].fillna(0)
#     with_nonzero = (total != 0)

#     if len(df_result) == 1:
#         df_result_summary[col_rate] = np.where(
#             with_nonzero,
#             df_result[col_rate],
#             np.nan
#         )                
#     else:
#         df_result_summary[col_rate] = np.where(
#             with_nonzero,
#             (df_result_summary[col_weigh].fillna(0) / total).round(4) * 100,
#             np.nan
#         )

# df_result_summary['paper_head_tail_ton_rate_W'] = np.where(
#         ((df_result_summary['weigh_W'] + df_result_summary['paper_head_tail_ton_W']).notna()) &\
#         ((df_result_summary['weigh_W'] + df_result_summary['paper_head_tail_ton_W']) != 0),
#         round(df_result_summary['weigh_W'] /\
#               (df_result_summary['weigh_W'] + df_result_summary['paper_head_tail_ton_W']) * 100, 2),
#         0
#     )    

# df_result_summary['lenth_rate_W'] = np.where(
#         ((df_result_summary['weigh_W'] + df_result_summary['lenth_ton_W']).notna()) &\
#         ((df_result_summary['weigh_W'] + df_result_summary['lenth_ton_W']) != 0),
#         round(df_result_summary['weigh_W'] /\
#               (df_result_summary['weigh_W'] + df_result_summary['lenth_ton_W']) * 100, 2),
#         0
#     )    

# df_result_summary['width_rate_W'] = np.where(
#         ((df_result_summary['weigh_W'] + df_result_summary['width_ton_W']).notna()) &\
#         ((df_result_summary['weigh_W'] + df_result_summary['width_ton_W']) != 0),
#         round(df_result_summary['weigh_W'] /\
#               (df_result_summary['weigh_W'] + df_result_summary['width_ton_W']) * 100, 2),
#         0
#     )    

# df_result_summary['bdate'] = '合計'

# defective_quantity_summary = df_result_summary[['defective_quantity_R1', 'defective_quantity_C1',
#                'defective_quantity_EA', 'defective_quantity_EB',
#                'defective_quantity_EC', 'defective_quantity_ED',
#                'lenth_ton_W', 'width_ton_W']].fillna(0).sum(axis=1)

# numerator = df_result_summary[['weigh_EA', 'weigh_EB', 'weigh_EC', 'weigh_ED']].fillna(0).sum(axis=1)
# denominator = (
#     df_result_summary[['weigh_EA', 'defective_quantity_EA',
#                        'weigh_EB', 'defective_quantity_EB',
#                        'weigh_EC', 'defective_quantity_EC',
#                        'weigh_ED', 'defective_quantity_ED']]
#     .fillna(0).sum(axis=1)
# )

# lenth_rate_summary = (
#     df_result_summary['width_rate_W'].fillna(0) *
#     df_result_summary['lenth_rate_R1'].fillna(0) *
#     df_result_summary['lenth_rate_C1'].fillna(0) *
#     (numerator / denominator.replace(0, np.nan)) *  # 防止除以 0
#     df_result_summary['lenth_rate_W'].fillna(0) / 1000000
# )        

# paper_head_tail_ton_summary = (
#     df_result_summary[['defective_quantity_R1', 'defective_quantity_C1',
#                        'defective_quantity_EA', 'defective_quantity_EB',
#                        'defective_quantity_EC', 'defective_quantity_ED',
#                        'paper_head_tail_ton_W', 'width_ton_W']]
#     .fillna(0).sum(axis=1)
# )        

# lenth_rate_summary_overall = (
#     df_result_summary['width_rate_W'].fillna(0) *
#     df_result_summary['lenth_rate_R1'].fillna(0) *
#     df_result_summary['lenth_rate_C1'].fillna(0) *
#     (numerator / denominator.replace(0, np.nan)) *
#     df_result_summary['paper_head_tail_ton_rate_W'].fillna(0) / 1000000
# )

# df_result = pd.concat([df_result,df_result_summary], ignore_index=True)

# for k in list(df_result.columns):
#     if k in ['weigh_R1','weigh_C1','weigh_EA','weigh_EB','weigh_EC','weigh_ED','weigh_W',
#              'paper_head_tail_ton_W','lenth_ton_W','width_ton_W','quality_ton_W']:
#         # 先轉成 float 再格式化到三位小數字串
#         df_result[k] = df_result[k].astype(float).map(lambda x: f"{x:.3f}" if pd.notnull(x) else None)
#     elif k in ['lenth_rate_R1','lenth_rate_C1','lenth_rate_EA','lenth_rate_EB','lenth_rate_EC','lenth_rate_ED',
#                'paper_head_tail_ton_rate_W','lenth_rate_W','width_rate_W']:
#         df_result[k] = df_result[k].astype(float).map(lambda x: f"{x:.2f}" if pd.notnull(x) else None)
#     else:
#         df_result[k] = df_result[k].apply(lambda x: str(x) if pd.notnull(x) else None)


# In[48]:


# with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
#     display(df_result)


# In[ ]:





# In[ ]:




