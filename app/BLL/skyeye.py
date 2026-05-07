import json
from pathlib import Path
<<<<<<< HEAD
# import random
import shutil
# import time
import pandas as pd
import base64
import os
# import pyodbc
import numpy as np
import logging
from PIL import Image
import io
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from utils.db_engine import get_session
=======
import random
import shutil
import time
from flask import current_app
import pandas as pd
# from icecream import ic
import base64
import os
import pyodbc
import numpy as np
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker
from PIL import Image
import io

from app.common import get_connection_string
from app.utils.filepath import get_temproot_and_exe_folder

from urllib.parse import quote_plus as urlquote
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

logger = logging.getLogger("MES_API")

class SkyeyeBll:
    def __init__(self):
<<<<<<< HEAD
        try:
            self.session = get_session("SRVMSDBA2_SKYEYE")
        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")

    def ReadFromDb(self, data):
        
        skyeyeCategory = getattr(data, "SkyeyeCategory", [])
        skyeyeDefectName = []
        
        if hasattr(data, "Category") and data.Category:
            skyeyeDefectName = [
                item.split("_")[1] for item in data.Category if "_" in item
            ]
            
        # -----------------------
        # SQL 主體
        # -----------------------            
        sql_query = """
=======
        # 直接用你的固定連線方式
        server = "10.10.2.50"
        database = "GREENZONE"
        password = urlquote("Fta@2022")
        conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        self.engine = create_engine(
            conn_str,
            fast_executemany=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10
        )
        self.Session = sessionmaker(bind=self.engine)
    def ReadFromDb(self, data):
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')
        session = self.Session()

        # wintrissCategory_middle_small = ['中黑汙點', '小黑汙點', '中透明點', '小透明點', '中破孔', '小破孔']
        skyeyeCategory = getattr(data, "SkyeyeCategory", [])
        skyeyeDefectName = []
        if hasattr(data, "Category") and data.Category:
            skyeyeDefectName = [item.split("_")[1] for item in data.Category if "_" in item]

        sql_query = f"""
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME());
DECLARE @queryEndTime  datetime2 = SYSDATETIME();
DECLARE @jobKey int=0;

<<<<<<< HEAD
SELECT 
    @queryStartTime =DATEADD(hour, -2, Date),
    @queryEndTime =DATEADD(hour, 2, Date),
    @jobKey=klKey
=======
SELECT @queryStartTime =DATEADD(hour, -2, Date), @queryEndTime =DATEADD(hour, 2, Date),@jobKey=klKey
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs]
WHERE JobID= :JobID

SELECT
<<<<<<< HEAD
    job.[UUID],
    job.[dtTime],
    :JobID AS relno,
    job.[klKey] JobKey,
    job.[lFlawId] FlawId,
    flaw.[pklFlawKey] FlawKey,
    job.[DefectName],
    job.[dCD],
    job.[dMD],
    job.[dWidth],
    job.[dLength],
    job.[dArea],
    job.[TopLeftX],
    job.[TopLeftY],
    job.[BottomRightX],
    job.[BottomRightY],
    job.DefectNameCategory AS skyeyeCategory,
    job.[DefectNameDetail]
FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw 
    ON flaw.dtTime between @queryStartTime and @queryEndTime 
    AND job.klKey=flaw.klJobKey
    AND job.lFlawId=flaw.lFlawId
LEFT JOIN [srvmsdba1].[FlawInspection].[dbo].[duptjobs] njob 
    ON job.klKey=njob.klkey 
    AND DATEPART(year,job.dtTime)= DATEPART(year,njob.[Date])
LEFT JOIN [srvad1].[amis].[dbo].[amreel] reel 
    ON njob.JobID = reel.relno COLLATE Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS
"""

        # -----------------------
        # Query parameters
        # -----------------------
        params = {
            "JobID": data.ReelNo
        }
        # -----------------------
        # Query conditions
        # -----------------------        
        conditions = [
            "job.klKey = @jobKey",
            "job.dtTime BETWEEN @queryStartTime AND @queryEndTime",
            "job.dMD < reel.lenth"
        ]        

        # -----------------------
        # Wintriss category filter
        # ----------------------- 
        large = ['大黑汙點', '大透明點', '大破孔']
        medium = ['中黑汙點', '中透明點', '中破孔']
        small = ['小黑汙點', '小透明點', '小破孔']
        
        wintrissCategory_filtered = large + medium + small

        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in small]
            
        if wintrissCategory_filtered:
            values = ",".join(f"'{v}'" for v in wintrissCategory_filtered)
            conditions.append(f"job.DefectName NOT IN ({values})")

        # -----------------------
        # Skyeye category filter
        # -----------------------            
        if skyeyeCategory:
            values = ",".join(f"'{v}'" for v in skyeyeCategory)
            conditions.append(f"job.DefectNameCategory IN ({values})")

        if skyeyeDefectName:
            values = ",".join(f"'{v}'" for v in skyeyeDefectName)
            conditions.append(f"job.DefectNameDetail IN ({values})")

        # -----------------------
        # 組 WHERE
        # -----------------------            
        if conditions:
            where_clause = " AND ".join(conditions)
            sql_query = f"{sql_query} WHERE {where_clause} ORDER BY flaw.pklFlawKey"
            
        # -----------------------
        # Execute SQL
        # -----------------------            
        try:   
            
            with self.session() as session:
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)

        except OperationalError as e:
            logger.error(f"DB OperationalError: {e}")
            raise
        except Exception as e:
            logger.error(f"ReadFromDb error: {e}")
            raise

        results = [
            {
=======
    job.[UUID]
    ,job.[dtTime]
    ,:JobID relno
    ,job.[klKey] JobKey
    ,job.[lFlawId] FlawId
    ,flaw.[pklFlawKey] FlawKey
    ,job.[DefectName]
    ,job.[dCD]
    ,job.[dMD]
    ,job.[dWidth]
    ,job.[dLength]
    ,job.[dArea]
    ,job.[TopLeftX]
    ,job.[TopLeftY]
    ,job.[BottomRightX]
    ,job.[BottomRightY]
    ,job.DefectNameCategory AS skyeyeCategory
    ,job.[DefectNameDetail]
--    ,rec.[IsOK]
FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw on flaw.dtTime between @queryStartTime and @queryEndTime AND job.klKey=flaw.klJobKey and job.lFlawId=flaw.lFlawId
LEFT JOIN [srvmsdba1].[FlawInspection].[dbo].[duptjobs] njob on job.klKey=njob.klkey and DATEPART(year,job.dtTime)= DATEPART(year,njob.[Date])
LEFT JOIN [srvad1].[amis].[dbo].[amreel] reel on njob.JobID = reel.relno COLLATE Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS
        """
        # 執行 SQL 查詢
        cond = []
        cond.append("job.klKey= @jobKey")
        cond.append("job.dtTime between @queryStartTime and @queryEndTime")
        cond.append("job.dMD < reel.[lenth]")
        params = {}
        params['JobID'] = f"{data.ReelNo}"

        # if data.OnlyLarge == 'true':
        #     cond.append("job.DefectName NOT IN ({})".format(",".join("'{}'".format(wcategory) for wcategory in wintrissCategory_middle_small)))

        wintrissCategory_filtered = ['大黑汙點', '大透明點', '大破孔', '中黑汙點', '小黑汙點', '中透明點', '小透明點', '中破孔', '小破孔']
        wintrissCategory_large = ['大黑汙點', '大透明點', '大破孔']
        wintrissCategory_medium = ['中黑汙點', '中透明點', '中破孔']
        wintrissCategory_small = ['小黑汙點', '小透明點', '小破孔']
        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_small]
            
        if wintrissCategory_filtered:
            cond.append("job.DefectName NOT IN ({})".format(",".join("'{}'".format(wcategory) for wcategory in wintrissCategory_filtered)))

        if skyeyeCategory:
            cond.append("job.DefectNameCategory IN ({})".format(",".join("'{}'".format(category) for category in skyeyeCategory)))
            params['category'] = skyeyeCategory
        if skyeyeDefectName:
            cond.append("job.DefectNameDetail IN ({})".format(",".join("'{}'".format(defect) for defect in skyeyeDefectName)))
            params['category'] = skyeyeDefectName

        try:
            if cond:
                # 使用 AND 運算符將條件組合在一起
                where_clause = " AND ".join(cond)
                order_clause = "ORDER BY flaw.pklFlawKey"
                sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"
                # result = session.execute(text(sql_query), params)
            result_df = pd.read_sql(text(sql_query), session.bind, params=params)
            # ic(result_df)
                # rows = result.fetchall()
        except OperationalError as e:
            ic(e)
        except Exception as e:
            ic(e)
        results = []
        # 處理查詢結果
        for idx, row in result_df.iterrows():
            results.append({
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
                "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
                "jobKey": row.JobKey,
                "flawId": row.FlawId,
                "flawKey": row.FlawKey,
                "skyeyeCategory": row.skyeyeCategory,
                "categoryName": row.DefectNameDetail,
                "x": row.dCD,
                "y": row.dMD,
                "width": row.dWidth,
                "length": row.dLength,
                "area": row.dArea,
                "uuid": row.UUID,
                "isAlarm": False
<<<<<<< HEAD
            }
            for row in result_df.itertuples()
        ]

        return results
    
class SkyeyeCategoryBll:
    def __init__(self):
        try:
            self.session = get_session("SRVMSDBA2_SKYEYE")
            
            self.mnameMapper = {
                "20": FTA_PM20_skyeyeDal(),
                "21": FTA_PM21_skyeyeDal()
            }
        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
    
    def browse(self, data):
        # 自定義 SQL 查詢語句
        sql_query = """
SELECT
    [DefectCategory] primaryCategory,
    [DefectNameDetail] category,
    [isenabled] isEnabled,
    1 [order],
    symbol,
    color
FROM [SKYEYE].[dbo].[WINTRISS_DefectCode]
        """      

        try:
            with self.session() as session:
                result_df = pd.read_sql(text(sql_query), session.bind)
        except OperationalError as e:
            logger.error(f"DB OperationalError: {e}")
            result_df = pd.DataFrame()
        except Exception as e:
            logger.error(f"ReadFromDb error: {e}")
            result_df = pd.DataFrame()

        results = []
        defects = [
            {"name": "真死紋", "category": "死紋", "symbol": "square", "color": "Green"},
            {"name": "破邊", "category": "死紋", "symbol": "square", "color": "DarkCyan"},
            {"name": "紙邊", "category": "死紋", "symbol": "square", "color": "DarkCyan"},
            {"name": "脫水不良", "category": "死紋", "symbol": "square", "color": "Olive"},

            {"name": "一般汙點", "category": "汙點", "symbol": "triangle", "color": "DarkSlateGray"},
            {"name": "烘缸塗料屑", "category": "汙點", "symbol": "triangle", "color": "LightSlateGray"},
            {"name": "破紙夾入", "category": "汙點", "symbol": "triangle", "color": "Gray"},
            {"name": "破邊", "category": "汙點", "symbol": "triangle", "color": "Silver"},
            {"name": "蚊蟲", "category": "汙點", "symbol": "triangle", "color": "DimGray"},
            {"name": "開口笑", "category": "汙點", "symbol": "triangle", "color": "DarkGray"},

            {"name": "1-5D破孔", "category": "破孔", "symbol": "emptycircle", "color": "OrangeRed"},
            {"name": "1P破邊", "category": "破孔", "symbol": "emptycircle", "color": "Coral"},
            {"name": "毛刷破孔", "category": "破孔", "symbol": "emptycircle", "color": "Fuchsia"},
            {"name": "加溼後開口笑破孔", "category": "破孔", "symbol": "emptycircle", "color": "Purple"},
            {"name": "刮刀著污開口笑", "category": "破孔", "symbol": "emptycircle", "color": "DarkSalmon"},
            {"name": "塗後掃瞄器破孔", "category": "破孔", "symbol": "emptycircle", "color": "MediumOrchid"},
            {"name": "塗料屑破孔", "category": "破孔", "symbol": "emptycircle", "color": "RebeccaPurple"},
            {"name": "網部水針破邊", "category": "破孔", "symbol": "emptycircle", "color": "DarkRed"},
            {"name": "網部破孔", "category": "破孔", "symbol": "emptycircle", "color": "IndianRed"},
            {"name": "壓榨部破孔", "category": "破孔", "symbol": "emptycircle", "color": "DeepPink"},
            {"name": "濕端破孔", "category": "破孔", "symbol": "emptycircle", "color": "Red"},

            {"name": "一般透明點", "category": "透明點", "symbol": "emptydiamond", "color": "DodgerBlue"},
            {"name": "加溼水痕", "category": "透明點", "symbol": "emptydiamond", "color": "DarkCyan"},
            {"name": "油點", "category": "透明點", "symbol": "emptydiamond", "color": "CornflowerBlue"},
            {"name": "破邊", "category": "透明點", "symbol": "emptydiamond", "color": "CornflowerBlue"},
            {"name": "塗佈水痕", "category": "透明點", "symbol": "emptydiamond", "color": "DeepSkyBlue"},
            {"name": "塗料塗料屑", "category": "透明點", "symbol": "emptydiamond", "color": "DarkBlue"},
            {"name": "滴水點", "category": "透明點", "symbol": "emptydiamond", "color": "Blue"},
            {"name": "壓光卡料印痕", "category": "透明點", "symbol": "emptydiamond", "color": "Blue"},
        ]

        return result_df.to_dict(orient='records')
    
class SkyeyeImageBll:
    def __init__(self):
        try:
            self.session = get_session("SRVMSDBA2_SKYEYE")

        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
            
    def ReadFromDb(self, data):
=======
                # "reconfirmOk": row.IsOK,
                }),

        session.close()
        return results


class skyeyeRealtimeBll:
    def __init__(self):
        # 直接用你的固定連線方式
        server = "10.10.2.50"
        database = "GREENZONE"
        password = urlquote("Fta@2022")
        conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        self.engine = create_engine(
            conn_str,
            fast_executemany=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10
        )
        self.Session = sessionmaker(bind=self.engine)    
    def browse(self, data):
        mnameMapper = {"20": FTA_PM20_skyeyeDal(), "21": FTA_PM21_skyeyeDal()}
        dal = None
        if 'MachineName' in data and data['MachineName'] in mnameMapper:
            dal = mnameMapper[data['MachineName']]
        else:
            return None

        rst = dal.query(data)
        # ic(type(rst))
        for result in rst:
            # ic(type(result))
            # result['TagName'] = data['TagNameOrigin']
            pass
        return rst

    def ReadFromDb(self,data):
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')
        session = self.Session()

        # wintrissCategory_middle_small = ['中黑汙點', '小黑汙點', '中透明點', '小透明點', '中破孔', '小破孔']
        # wintrissCategory_all = ['大黑汙點', '大透明點', '大破孔', '中黑汙點', '小黑汙點', '中透明點', '小透明點', '中破孔', '小破孔']

        skyeyeCategory = getattr(data, "SkyeyeCategory", [])
        skyeyeDefectName = []
        if hasattr(data, "Category") and data.Category:
            skyeyeDefectName = [item.split("_")[1] for item in data.Category if "_" in item]

        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME())
DECLARE @machineName varchar(max)='20'

--SELECT @queryStartTime=pdate FROM [SRVAD1].[AMIS].[dbo].[amreel]
--WHERE mname=@machineName
--ORDER BY pdate desc
--OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

SELECT @queryStartTime= Date FROM [SRVMSDBA1].[FlawInspection].[dbo].[duptjobs] ORDER BY Date DESC
OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

SELECT
    job.[UUID]
    ,job.[dtTime]
    ,job.[klKey] JobKey
    ,job.[lFlawId] FlawId
    ,flaw.[pklFlawKey] FlawKey
    ,job.[DefectName]
    ,job.[dCD]
    ,job.[dMD]
    ,job.[dWidth]
    ,job.[dLength]
    ,job.[dArea]
    ,job.[TopLeftX]
    ,job.[TopLeftY]
    ,job.[BottomRightX]
    ,job.[BottomRightY]
    ,job.DefectNameCategory AS skyeyeCategory
    ,job.[DefectNameDetail]
--    ,rec.[IsOK]
FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
--LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result_Reconfirm] rec on job.UUID=rec.UUID
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw on flaw.dtTime >= @queryStartTime AND job.klKey=flaw.klJobKey AND job.lFlawId=flaw.lFlawId
        """
        # 執行 SQL 查詢
        cond = []
        params = {}
        cond.append("job.dtTime > @queryStartTime")

        # if data.OnlyLarge == 'true':
        #     cond.append("job.DefectName NOT IN ({})".format(",".join("'{}'".format(wcategory) for wcategory in wintrissCategory_middle_small)))

        wintrissCategory_filtered = ['大黑汙點', '大透明點', '大破孔', '中黑汙點', '小黑汙點', '中透明點', '小透明點', '中破孔', '小破孔']
        wintrissCategory_large = ['大黑汙點', '大透明點', '大破孔']
        wintrissCategory_medium = ['中黑汙點', '中透明點', '中破孔']
        wintrissCategory_small = ['小黑汙點', '小透明點', '小破孔']
        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_small]
        if wintrissCategory_filtered:
            cond.append("job.DefectName NOT IN ({})".format(",".join("'{}'".format(wcategory) for wcategory in wintrissCategory_filtered)))

        if skyeyeCategory:
            cond.append("job.DefectNameCategory IN ({})".format(",".join("'{}'".format(category) for category in skyeyeCategory)))
            params['category'] = skyeyeCategory

        if skyeyeDefectName:
            cond.append("job.DefectNameDetail IN ({})".format(",".join("'{}'".format(defect) for defect in skyeyeDefectName)))
            params['category'] = skyeyeDefectName

        try:
            # result = session.execute(text(sql_query), params)
            if cond:
                # 使用 AND 運算符將條件組合在一起
                where_clause = " AND ".join(cond)
                order_clause = "order by job.dtTime desc"
                sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"

            with session.begin():
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)
            # ic(result_df)
                # rows = result.fetchall()
        except OperationalError as e:
            ic(e)
        except Exception as e:
            ic(e)
        results = []

        # 處理查詢結果
        for idx, row in result_df.iterrows():
            results.append({
                "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
                "jobKey": row.JobKey,
                "flawId": row.FlawId,
                "flawKey": row.FlawKey,
                "skyeyeCategory": row.skyeyeCategory,
                "categoryName": row.DefectNameDetail,
                "x": row.dCD,
                "y": row.dMD,
                "width": row.dWidth,
                "length": row.dLength,
                "area": row.dArea,
                "uuid": row.UUID,
                # "reconfirmOk": row.IsOK,
                }),

        # 關閉會話
        session.close()
        # 使用範例：
        png_files_base64 = results
        return png_files_base64


class SkyeyeReelBll:
    def __init__(self):
        # 直接用你的固定連線方式
        server = "10.10.2.50"
        database = "GREENZONE"
        password = urlquote("Fta@2022")
        conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        self.engine = create_engine(
            conn_str,
            fast_executemany=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10
        )
        self.Session = sessionmaker(bind=self.engine)        
    def browse(self, data):
        mnameMapper = {"20": FTA_PM20_skyeye_reelDal(), "21": FTA_PM21_skyeye_reelDal()}
        dal = None
        if 'MachineName' in data and data['MachineName'] in mnameMapper:
            dal = mnameMapper[data['MachineName']]
        else:
            return None

        rst = dal.query(data)
        # ic(type(rst))
        for result in rst:
            # ic(type(result))
            # result['TagName'] = data['TagNameOrigin']
            pass
        return rst

    def ReadFromDb(self, data):
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')
        session = self.Session()

        # 自定義 SQL 查詢語句
        # 執行 DDL 查詢
        ddl_query = """
DECLARE @queryStartTime datetime2 = DATEADD(hour, -2, SYSDATETIME());
DECLARE @queryEndTime datetime2 = SYSDATETIME();
DECLARE @JobID varchar(max) = :JobID;

-- 計算查詢的開始和結束時間
SELECT @queryStartTime = DATEADD(hour, -2, MIN(Date)), 
       @queryEndTime = DATEADD(hour, 2, MAX(Date)) 
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))

-- 檢查並刪除全局臨時表
IF OBJECT_ID('tempdb..##jobKeys', 'U') IS NOT NULL
    DROP TABLE ##jobKeys;

IF OBJECT_ID('tempdb..##AllDefectNames', 'U') IS NOT NULL
    DROP TABLE ##AllDefectNames;

IF OBJECT_ID('tempdb..##JobDefectCombinations', 'U') IS NOT NULL
    DROP TABLE ##JobDefectCombinations;

-- 創建全局臨時表
CREATE TABLE ##jobKeys (klKey INT)
INSERT INTO ##jobKeys (klKey)
SELECT klKey 
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))

CREATE TABLE ##AllDefectNames (DefectNameDetail NVARCHAR(MAX))
INSERT INTO ##AllDefectNames (DefectNameDetail)
SELECT DefectCategory+'_'+DefectNameDetail
FROM [SKYEYE].[dbo].[WINTRISS_DefectCode]

CREATE TABLE ##JobDefectCombinations (JobID NVARCHAR(MAX), klKey INT, DefectNameDetail NVARCHAR(MAX))
INSERT INTO ##JobDefectCombinations (JobID, klKey, DefectNameDetail)
SELECT jobs.JobID, jobs.klKey, defect.DefectNameDetail
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] jobs
CROSS JOIN ##AllDefectNames defect
WHERE jobs.JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))
        """

        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(hour, -2, SYSDATETIME());
DECLARE @queryEndTime datetime2 = SYSDATETIME();
DECLARE @JobID varchar(max) = :JobID;

-- 計算查詢的開始和結束時間
SELECT @queryStartTime = DATEADD(hour, -2, MIN(Date)), 
       @queryEndTime = DATEADD(hour, 2, MAX(Date)) 
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))
AND Date >= Dateadd(YEAR,-1,GETDATE())

-- 動態生成 PIVOT 的列名
DECLARE @PivotColumns NVARCHAR(MAX)
SET @PivotColumns = STUFF((
    SELECT DISTINCT ',' + QUOTENAME(DefectNameDetail)
    FROM ##AllDefectNames
    FOR XML PATH(''), TYPE
).value('.', 'NVARCHAR(MAX)'), 1, 1, '')

-- 動態 SQL 查詢
DECLARE @PivotQuery NVARCHAR(MAX)
SET @PivotQuery = N'
SELECT JobID relno, ' + @PivotColumns + '
FROM (
    SELECT JobID, DefectNameDetail, Sum(DefectCount) DefectCount FROM (
        SELECT
            comb.JobID,
            comb.DefectNameDetail
            ,ISNULL(COUNT(job.DefectNameDetail), 0) AS DefectCount
            ,job.dMD
            ,MAX(reel.[lenth]) AS lenth
        FROM ##JobDefectCombinations comb
        LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
            ON comb.DefectNameDetail = CONCAT(job.DefectNameCategory, ''_'', job.DefectNameDetail)
            AND job.dtTime BETWEEN @queryStartTime AND @queryEndTime
            AND job.klKey = comb.klKey
        LEFT JOIN [srvad1].[amis].[dbo].[amreel] reel on comb.JobID = reel.relno COLLATE Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS
        GROUP BY
             comb.JobID
            ,comb.DefectNameDetail
            ,job.dMD
            ,reel.[lenth]
        ) src
        WHERE dMD IS NULL OR dMD<=lenth
        GROUP BY JobID,DefectNameDetail
    ) AS SourceTable
PIVOT (
    MAX(DefectCount)
    FOR DefectNameDetail IN (' + @PivotColumns + ')
) AS PivotTable
ORDER BY JobID
'

-- 執行動態 SQL
EXEC sp_executesql @PivotQuery, N'@queryStartTime datetime2, @queryEndTime datetime2', @queryStartTime, @queryEndTime
        """
        cleanup_query = """
        DROP TABLE ##jobKeys;
        DROP TABLE ##AllDefectNames;
        DROP TABLE ##JobDefectCombinations;
        """

        # 執行 SQL 查詢
        cond = []
        # cond.append("klKey= @jobKey")
        # cond.append("job.dtTime between @queryStartTime and @queryEndTime")
        params = {}
        params['JobID'] = f"{data.ReelNoCsv}"

        # function_array = getattr(filter, 'function_array', None)
        # if hasattr(data, "Category") and data.Category is not None and len(data.Category) > 0:
        #     cond.append("job.DefectNameDetail IN ({})".format(",".join("'{}'".format(category) for category in data.Category)))
        #     params['category'] = data.Category
        try:
            if cond:
                # 使用 AND 運算符將條件組合在一起
                where_clause = " AND ".join(cond)
                order_clause = "order by flaw.pklFlawKey"
                sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"
            with session.begin():
                session.execute(text(ddl_query), params=params)
            with session.begin():
                # result = session.execute(text(sql_query), params)
                # ic(result)
            #     rows = result.fetchall()
            # columns = result.keys()
            # result_df = pd.DataFrame(rows, columns=columns)
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)
                # ic(result_df)
        except OperationalError as e:
            ic(e)
        except Exception as e:
            ic(e)

        with session.begin():
            session.execute(text(cleanup_query))
        session.close()
        # 使用範例：
        result_dict_list_df = result_df.replace({np.nan: None}).to_dict(orient='records')
        return result_dict_list_df


class SkyeyeReelRealtimeBll:
    def __init__(self):
        # 直接用你的固定連線方式
        server = "10.10.2.50"
        database = "GREENZONE"
        password = urlquote("Fta@2022")
        conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        self.engine = create_engine(
            conn_str,
            fast_executemany=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10
        )
        self.Session = sessionmaker(bind=self.engine)       
    def browse(self, data):
        mnameMapper = {"20": FTA_PM20_skyeye_reelDal(), "21": FTA_PM21_skyeye_reelDal()}
        dal = None
        if 'MachineName' in data and data['MachineName'] in mnameMapper:
            dal = mnameMapper[data['MachineName']]
        else:
            return None

        rst = dal.query(data)
        # ic(type(rst))
        for result in rst:
            # ic(type(result))
            # result['TagName'] = data['TagNameOrigin']
            pass
        return rst

    def ReadFromDb(self, data):
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')
        session = self.Session()

        # 自定義 SQL 查詢語句
        # 執行 DDL 查詢
        ddl_query = """
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME())
DECLARE @machineName varchar(max)='20'
DECLARE @JobID varchar(max) = :JobID;

SELECT @queryStartTime=pdate FROM [SRVAD1].[AMIS].[dbo].[amreel]
WHERE mname=@machineName
ORDER BY pdate desc
OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

-- 檢查並刪除全局臨時表
IF OBJECT_ID('tempdb..##jobKeys', 'U') IS NOT NULL
    DROP TABLE ##jobKeys;

IF OBJECT_ID('tempdb..##AllDefectNames', 'U') IS NOT NULL
    DROP TABLE ##AllDefectNames;

IF OBJECT_ID('tempdb..##JobDefectCombinations', 'U') IS NOT NULL
    DROP TABLE ##JobDefectCombinations;

-- 創建全局臨時表
CREATE TABLE ##jobKeys (klKey INT)
INSERT INTO ##jobKeys (klKey)
SELECT klKey 
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))

CREATE TABLE ##AllDefectNames (DefectNameDetail NVARCHAR(MAX))
INSERT INTO ##AllDefectNames (DefectNameDetail)
SELECT DISTINCT DefectNameDetail 
FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result]

CREATE TABLE ##JobDefectCombinations (JobID NVARCHAR(MAX), klKey INT, DefectNameDetail NVARCHAR(MAX))
INSERT INTO ##JobDefectCombinations (JobID, klKey, DefectNameDetail)
SELECT jobs.JobID, jobs.klKey, defect.DefectNameDetail
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] jobs
CROSS JOIN ##AllDefectNames defect
WHERE jobs.JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))
        """

        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(hour, -2, SYSDATETIME());
DECLARE @machineName varchar(max)='20'
DECLARE @JobID varchar(max) = :JobID;


-- 計算查詢的開始和結束時間
SELECT @queryStartTime=pdate FROM [SRVAD1].[AMIS].[dbo].[amreel]
WHERE mname=@machineName
ORDER BY pdate desc
OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

-- 動態生成 PIVOT 的列名
DECLARE @PivotColumns NVARCHAR(MAX)
SET @PivotColumns = STUFF((
    SELECT DISTINCT ',' + QUOTENAME(DefectNameDetail)
    FROM ##AllDefectNames
    FOR XML PATH(''), TYPE
).value('.', 'NVARCHAR(MAX)'), 1, 1, '')

-- 動態 SQL 查詢
DECLARE @PivotQuery NVARCHAR(MAX)
SET @PivotQuery = N'
SELECT JobID relno, ' + @PivotColumns + '
FROM (
    SELECT
        comb.JobID,
        comb.DefectNameDetail,
        ISNULL(COUNT(job.DefectNameDetail), 0) AS DefectCount
    FROM ##JobDefectCombinations comb
    LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
        ON job.DefectNameDetail = comb.DefectNameDetail
        AND job.klKey IN (SELECT klKey FROM ##jobKeys)
        AND job.dtTime > @queryStartTime
        AND job.klKey = comb.klKey
    LEFT JOIN [srvmsdba1].[FlawInspection].[dbo].[duptjobs] jobs
        ON job.klKey = jobs.klKey 
        AND jobs.Date > @queryStartTime
    GROUP BY comb.JobID, comb.DefectNameDetail
) AS SourceTable
PIVOT (
    MAX(DefectCount)
    FOR DefectNameDetail IN (' + @PivotColumns + ')
) AS PivotTable
ORDER BY JobID'

-- 執行動態 SQL
EXEC sp_executesql @PivotQuery, N'@queryStartTime datetime2, @queryStartTime, @queryEndTime
        """
        cleanup_query = """
        DROP TABLE ##jobKeys;
        DROP TABLE ##AllDefectNames;
        DROP TABLE ##JobDefectCombinations;
        """
        
        # 執行 SQL 查詢
        cond = []
        # cond.append("klKey= @jobKey")
        # cond.append("job.dtTime between @queryStartTime and @queryEndTime")
        params = {}
        params['JobID'] = getattr(data, "ReelNoCsv", None)

        # function_array = getattr(filter, 'function_array', None)
        # if hasattr(data, "Category") and data.Category is not None and len(data.Category) > 0:
        #     cond.append("job.DefectNameDetail IN ({})".format(",".join("'{}'".format(category) for category in data.Category)))
        #     params['category'] = data.Category
        try:
            if cond:
                # 使用 AND 運算符將條件組合在一起
                where_clause = " AND ".join(cond)
                order_clause = "order by flaw.pklFlawKey"
                sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"
            with session.begin():
                session.execute(text(ddl_query), params=params)
            with session.begin():
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)
                
        except OperationalError as e:
            logger.exception("Database OperationalError occurred")
            raise
        except Exception as e:
            logger.exception("Unexpected error occurred")
            raise


        with session.begin():
            session.execute(text(cleanup_query))
        session.close()
        # 使用範例：
        result_dict_list_df = result_df.to_dict(orient='records')
        return result_dict_list_df


class SkyeyeImageBll:
    def __init__(self):
        # 直接用你的固定連線方式
        server = "10.10.2.50"
        database = "GREENZONE"
        password = urlquote("Fta@2022")
        conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        self.engine = create_engine(
            conn_str,
            fast_executemany=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10
        )
        self.Session = sessionmaker(bind=self.engine)      
    def ReadFromDb(self, data):
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')
        session = self.Session()

>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
        skyeyeCategory = getattr(data, "SkyeyeCategory", [])
        skyeyeDefectName = []
        if hasattr(data, "Category") and data.Category:
            skyeyeDefectName = [item.split("_")[1] for item in data.Category if "_" in item]
            
        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME());
DECLARE @queryEndTime  datetime2 = SYSDATETIME();
DECLARE @jobKey int=0;

SELECT @queryStartTime =DATEADD(hour, -2, Date), @queryEndTime =DATEADD(hour, 2, Date),@jobKey=klKey
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs]
WHERE JobID= :JobID

SELECT
    job.[UUID]
    ,job.[FileName]
    ,job.[dtTime]
    --,job.[JobID]
    ,:JobID
    ,job.[klKey] JobKey
    ,job.[lFlawId] FlawId
    ,flaw.[pklFlawKey] FlawKey
    ,job.[DefectName]
    ,job.[dCD]
    ,job.[dMD]
    ,job.[dWidth]
    ,job.[dLength]
    ,job.[dArea]
    ,job.[TopLeftX]
    ,job.[TopLeftY]
    ,job.[BottomRightX]
    ,job.[BottomRightY]
    --,job.[ConfidenceScore]
    ,job.[DefectNameCategory] AS skyeyeCategory
    ,job.[DefectNameDetail]
    --,job.[bdtm]
    ,img.iImage
    ,rec.[IsOK] AS ReconfirmIsOK
    ,rec.[DefectNameCategory] AS ReconfirmCategry
    ,rec.[DefectNameDetail] AS ReconfirmDefectNameDetail
    ,rec.[Comment] AS ReconfirmComment
FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job WITH (NOLOCK)
LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result_Reconfirm] rec WITH (NOLOCK) on job.UUID=rec.UUID
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw WITH (NOLOCK) on flaw.dtTime between @queryStartTime and @queryEndTime AND job.klKey=flaw.klJobKey and job.lFlawId=flaw.lFlawId
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptimage] img WITH (NOLOCK) on img.flawtime between @queryStartTime and @queryEndTime AND flaw.pklFlawKey=img.klFlawKey
        """
<<<<<<< HEAD
        # -----------------------
        # Query parameters
        # -----------------------
        params = {
            "JobID": data.ReelNo
        }
        # -----------------------
        # Query conditions
        # -----------------------        
        conditions = [
            "klKey= @jobKey",
            "job.dtTime between @queryStartTime and @queryEndTime"
        ]                

        # 動態加入 X / Y 範圍條件
        range_conditions = {
            "dCD": ("RangeXStart", "RangeXEnd"),
            "dMD": ("RangeYStart", "RangeYEnd")
        }

        for col, (start_attr, end_attr) in range_conditions.items():
            start_val = getattr(data, start_attr)
            end_val = getattr(data, end_attr)
            if start_val is not None and end_val is not None:
                conditions.append(f"job.{col} between :{start_attr} and :{end_attr}")
                params[start_attr] = start_val
                params[end_attr] = end_val

        # -----------------------
        # Wintriss category filter
        # ----------------------- 
        large = ['大黑汙點', '大透明點', '大破孔']
        medium = ['中黑汙點', '中透明點', '中破孔']
        small = ['小黑汙點', '小透明點', '小破孔']
        
        wintrissCategory_filtered = large + medium + small

        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in small]
            
        if wintrissCategory_filtered:
            values = ",".join(f"'{v}'" for v in wintrissCategory_filtered)
            conditions.append(f"job.DefectName NOT IN ({values})")

        # -----------------------
        # Skyeye category filter
        # -----------------------            
        if skyeyeCategory:
            values = ",".join(f"'{v}'" for v in skyeyeCategory)
            conditions.append(f"job.DefectNameCategory IN ({values})")

        if skyeyeDefectName:
            values = ",".join(f"'{v}'" for v in skyeyeDefectName)
            conditions.append(f"job.DefectNameDetail IN ({values})")
            

        # -----------------------
        # 組 WHERE
        # -----------------------            
        if conditions:
            where_clause = " AND ".join(conditions)
            order_clause = "ORDER BY job.dtTime DESC"
            sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"            
            
        # -----------------------
        # Execute SQL
        # -----------------------            
        try:   
            
            with self.session() as session:
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)

        except OperationalError as e:
            logger.error(f"DB OperationalError: {e}")
            raise
        except Exception as e:
            logger.error(f"ReadFromDb error: {e}")
            raise

        def blob_to_base64(blob_bytes: bytes) -> Optional[str]:
            if not blob_bytes:
                return None
            width = blob_bytes[0] + blob_bytes[1] * 256
            height = blob_bytes[4] + blob_bytes[5] * 256
            if width == 0 or height == 0:
                return None

            pixel_data = np.frombuffer(blob_bytes, dtype=np.uint8, offset=8).reshape((height, width))
            bmp_img = Image.fromarray(pixel_data, mode='L')

            with io.BytesIO() as buf:
                bmp_img.save(buf, format='PNG')
                return base64.b64encode(buf.getvalue()).decode('utf-8')

        def row_to_dict(row):
            img_base64 = blob_to_base64(row.iImage)
            if not img_base64:
                return None

            return {
                "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
                "fileName": row.FileName,
                "jobKey": row.JobKey,
                "flawKey": row.FlawKey,
                "flawId": row.FlawId,
                "x": row.dCD,
                "y": row.dMD,
                "image": f"data:image/png;base64,{img_base64}",
                "rect": [{
                    "wintrissDefectName": row.DefectName,
                    "skyeyeCategory": row.skyeyeCategory,
                    "defectName": row.DefectNameDetail,
                    "topLeftX": row.TopLeftX,
                    "topLeftY": row.TopLeftY,
                    "bottomRightX": row.BottomRightX,
                    "bottomRightY": row.BottomRightY
                }],
                "uuid": row.UUID,
                "reconfirmOk": row.ReconfirmIsOK,
                "reconfirmCategory": row.ReconfirmCategry,
                "reconfirmDefect": row.ReconfirmDefectNameDetail,
                "reconfirmComment": row.ReconfirmComment,
                "width": row.dWidth,
                "length": row.dLength,
                "area": row.dArea
            }

        results = [row_to_dict(row) for _, row in result_df.iterrows() if row_to_dict(row)]

        return results

#     def ReadFromDbUuid(self, data):
#         session = self.session()
        
#         job_id = getattr(data, "ReelNo", [])
#         sql_query = f"""
# DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME());
# DECLARE @queryEndTime  datetime2 = SYSDATETIME();
# DECLARE @jobKey int=0;

# SELECT @queryStartTime =DATEADD(hour, -2, Date), @queryEndTime =DATEADD(hour, 2, Date),@jobKey=klKey
# FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs]
# WHERE JobID= :JobID

# SELECT
#     job.[UUID]
#     ,job.[FileName]
#     ,job.[dtTime]
#     --,job.[JobID]
#     ,:JobID
#     ,job.[klKey] JobKey
#     ,job.[lFlawId] FlawId
#     ,flaw.[pklFlawKey] FlawKey
#     ,job.[DefectName]
#     ,job.[dCD]
#     ,job.[dMD]
#     ,job.[dWidth]
#     ,job.[dLength]
#     ,job.[dArea]
#     ,job.[TopLeftX]
#     ,job.[TopLeftY]
#     ,job.[BottomRightX]
#     ,job.[BottomRightY]
#     --,job.[ConfidenceScore]
#     ,job.[DefectNameCategory] AS skyeyeCategory
#     ,job.[DefectNameDetail]
#     --,job.[bdtm]
#     ,img.iImage
#     ,rec.[IsOK] AS ReconfirmIsOK
#     ,rec.[DefectNameCategory] AS ReconfirmCategry
#     ,rec.[DefectNameDetail] AS ReconfirmDefectNameDetail
#     ,rec.[Comment] AS ReconfirmComment
# FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job WITH (NOLOCK)
# LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result_Reconfirm] rec WITH (NOLOCK) on job.UUID=rec.UUID
# LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw WITH (NOLOCK) on flaw.dtTime between @queryStartTime and @queryEndTime AND job.klKey=flaw.klJobKey and job.lFlawId=flaw.lFlawId
# LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptimage] img WITH (NOLOCK) on img.flawtime between @queryStartTime and @queryEndTime AND flaw.pklFlawKey=img.klFlawKey
#         """

#         uuid_list: list[str] = data.Uuid if isinstance(data.Uuid, list) else [data.Uuid]
#         uuid_params = {f"uuid_{i}": uuid for i, uuid in enumerate(uuid_list)}
#         uuid_placeholders = ", ".join([f":uuid_{i}" for i in range(len(uuid_list))])
#         uuid_where = f"WHERE job.UUID IN ({uuid_placeholders})"

#         full_query = f"""
#         {sql_query}
#         {uuid_where}
#         ORDER BY flaw.pklFlawKey
#         """
#         try:
#             result_df = pd.read_sql(text(full_query), session.bind, params=uuid_params | {'JobID': job_id})
#         except OperationalError as e:
#             ic(e)
#         except Exception as e:
#             ic(e)
#         results = []

#         def blob_to_base64(a):
#             width = a[0] + a[1] * 256
#             height = a[4] + a[5] * 256

#             if width == 0 or height == 0:
#                 return None

#             # 使用 NumPy 建立像素數據陣列
#             pixel_data = np.frombuffer(a, dtype=np.uint8, offset=8).reshape((height, width))

#             # 將像素數據轉換為 PIL.Image 對象
#             bmp_show_img = Image.fromarray(pixel_data, mode='L')

#             # 使用內存中的字節數據
#             with io.BytesIO() as img_byte_array:
#                 bmp_show_img.save(img_byte_array, format='PNG')
#                 img_byte_array.seek(0)  # 重設游標到起點
#                 img_byte_array = img_byte_array.read()

#             # 將字節數據編碼為 base64
#             base64_string = base64.b64encode(img_byte_array).decode('utf-8')

#             return base64_string

# # 處理查詢結果
#         for idx, row in result_df.iterrows():
#             blob_data = row.iImage
#             base64_string = blob_to_base64(blob_data)

#             if base64_string:
#                 results.append({
#                     "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
#                     "fileName": row.FileName,
#                     "jobKey": row.JobKey,
#                     "flawKey": row.FlawKey,
#                     "flawId": row.FlawId,
#                     "x": row.dCD,
#                     "y": row.dMD,
#                     'image': f"data:image/png;base64,{base64_string}",
#                     "rect": [
#                         {
#                             "wintrissDefectName": f"{row.DefectName}",
#                             "skyeyeCategory": f"{row.skyeyeCategory}",
#                             "defectName": f"{row.DefectNameDetail}",
#                             "topLeftX": f"{row.TopLeftX}",
#                             "topLeftY": f"{row.TopLeftY}",
#                             "bottomRightX": f"{row.BottomRightX}",
#                             "bottomRightY": f"{row.BottomRightY}"
#                         }
#                     ],
#                     "uuid": row.UUID,
#                     "reconfirmOk": row.ReconfirmIsOK,
#                     "reconfirmCategory": row.ReconfirmCategry,
#                     "reconfirmDefect": row.ReconfirmDefectNameDetail,
#                     "reconfirmComment": row.ReconfirmComment,
#                     "width": row.dWidth,
#                     "length": row.dLength,
#                     "area": row.dArea,
#                     }),

#         # 關閉會話
#         session.close()
#         # 使用範例：
#         png_files_base64 = results
#         return png_files_base64
    
class SkyeyeImageRealtimeBll:
    def __init__(self):
        try:
            self.session = get_session("SRVMSDBA2_SKYEYE")

        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
            
    def ReadFromDb(self, data):
=======

        cond = []
        cond.append("klKey= @jobKey")
        cond.append("job.dtTime between @queryStartTime and @queryEndTime")
        params = {}
        params['JobID'] = f"{data.ReelNo}"

        if data.RangeXStart is not None and data.RangeXEnd is not None:
            cond.append("job.dCD between :RangeXStart and :RangeXEnd")
            params['RangeXStart'] = f"{data.RangeXStart}"
            params['RangeXEnd'] = f"{data.RangeXEnd}"

        if data.RangeYStart is not None and data.RangeYEnd is not None:
            cond.append("job.dMD between :RangeYStart and :RangeYEnd")
            params['RangeYStart'] = f"{data.RangeYStart}"
            params['RangeYEnd'] = f"{data.RangeYEnd}"

        wintrissCategory_filtered = ['大黑汙點', '大透明點', '大破孔', '中黑汙點', '小黑汙點', '中透明點', '小透明點', '中破孔', '小破孔']
        wintrissCategory_large = ['大黑汙點', '大透明點', '大破孔']
        wintrissCategory_medium = ['中黑汙點', '中透明點', '中破孔']
        wintrissCategory_small = ['小黑汙點', '小透明點', '小破孔']
        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_small]
        if wintrissCategory_filtered:
            cond.append("job.DefectName NOT IN ({})".format(",".join("'{}'".format(wcategory) for wcategory in wintrissCategory_filtered)))
            
        if skyeyeCategory:
            cond.append("job.DefectNameCategory IN ({})".format(",".join("'{}'".format(category) for category in skyeyeCategory)))
            params['category'] = skyeyeCategory

        if skyeyeDefectName:
            cond.append("job.DefectNameDetail IN ({})".format(",".join("'{}'".format(defect) for defect in skyeyeDefectName)))
            params['category'] = skyeyeDefectName

        try:
            if cond:
                where_clause = " AND ".join(cond)
                order_clause = "order by flaw.pklFlawKey"
                sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"
            result_df = pd.read_sql(text(sql_query), session.bind, params=params)
        except OperationalError as e:
            ic(e)
        except Exception as e:
            ic(e)
        results = []

        def blob_to_base64_disk(a):
            width = a[0] + a[1] * 256
            height = a[4] + a[5] * 256

            if width == 0 or height == 0:
                return None

            # 使用 NumPy 建立像素數據陣列
            pixel_data = np.frombuffer(a, dtype=np.uint8, offset=8).reshape((height, width))

            # 將像素數據轉換為 PIL.Image 對象
            bmp_show_img = Image.fromarray(pixel_data, mode='L')

            # 將圖像保存為內存中的字節數據
            img_byte_array = io.BytesIO()
            bmp_show_img.save(img_byte_array, format='PNG')
            img_byte_array = img_byte_array.getvalue()

            # 將字節數據編碼為 base64
            base64_string = base64.b64encode(img_byte_array).decode('utf-8')

            return base64_string      

        def blob_to_base64(a):
            width = a[0] + a[1] * 256
            height = a[4] + a[5] * 256

            if width == 0 or height == 0:
                return None

            # 使用 NumPy 建立像素數據陣列
            pixel_data = np.frombuffer(a, dtype=np.uint8, offset=8).reshape((height, width))

            # 將像素數據轉換為 PIL.Image 對象
            bmp_show_img = Image.fromarray(pixel_data, mode='L')

            # 使用內存中的字節數據
            with io.BytesIO() as img_byte_array:
                bmp_show_img.save(img_byte_array, format='PNG')
                img_byte_array.seek(0)  # 重設游標到起點
                img_byte_array = img_byte_array.read()

            # 將字節數據編碼為 base64
            base64_string = base64.b64encode(img_byte_array).decode('utf-8')

            return base64_string

        # 處理查詢結果
        for idx, row in result_df.iterrows():
            blob_data = row.iImage
            base64_string = blob_to_base64(blob_data)

            if base64_string:
                results.append({
                    "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
                    "fileName": row.FileName,
                    "jobKey": row.JobKey,
                    "flawKey": row.FlawKey,
                    "flawId": row.FlawId,
                    "x": row.dCD,
                    "y": row.dMD,
                    'image': f"data:image/png;base64,{base64_string}",
                    "rect": [
                        {
                            "wintrissDefectName": f"{row.DefectName}",
                            "skyeyeCategory": f"{row.skyeyeCategory}",
                            "defectName": f"{row.DefectNameDetail}",
                            "topLeftX": f"{row.TopLeftX}",
                            "topLeftY": f"{row.TopLeftY}",
                            "bottomRightX": f"{row.BottomRightX}",
                            "bottomRightY": f"{row.BottomRightY}"
                        }
                    ],
                    "uuid": row.UUID,
                    "reconfirmOk": row.ReconfirmIsOK,
                    "reconfirmCategory": row.ReconfirmCategry,
                    "reconfirmDefect": row.ReconfirmDefectNameDetail,
                    "reconfirmComment": row.ReconfirmComment,
                    "width": row.dWidth,
                    "length": row.dLength,
                    "area": row.dArea,
                    }),

        # 關閉會話
        session.close()
        # 使用範例：
        png_files_base64 = results
        return png_files_base64

    def ReadFromDbUuid(self, data):
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')
        session = self.Session()
        
        job_id = getattr(data, "ReelNo", [])
        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME());
DECLARE @queryEndTime  datetime2 = SYSDATETIME();
DECLARE @jobKey int=0;

SELECT @queryStartTime =DATEADD(hour, -2, Date), @queryEndTime =DATEADD(hour, 2, Date),@jobKey=klKey
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs]
WHERE JobID= :JobID

SELECT
    job.[UUID]
    ,job.[FileName]
    ,job.[dtTime]
    --,job.[JobID]
    ,:JobID
    ,job.[klKey] JobKey
    ,job.[lFlawId] FlawId
    ,flaw.[pklFlawKey] FlawKey
    ,job.[DefectName]
    ,job.[dCD]
    ,job.[dMD]
    ,job.[dWidth]
    ,job.[dLength]
    ,job.[dArea]
    ,job.[TopLeftX]
    ,job.[TopLeftY]
    ,job.[BottomRightX]
    ,job.[BottomRightY]
    --,job.[ConfidenceScore]
    ,job.[DefectNameCategory] AS skyeyeCategory
    ,job.[DefectNameDetail]
    --,job.[bdtm]
    ,img.iImage
    ,rec.[IsOK] AS ReconfirmIsOK
    ,rec.[DefectNameCategory] AS ReconfirmCategry
    ,rec.[DefectNameDetail] AS ReconfirmDefectNameDetail
    ,rec.[Comment] AS ReconfirmComment
FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job WITH (NOLOCK)
LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result_Reconfirm] rec WITH (NOLOCK) on job.UUID=rec.UUID
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw WITH (NOLOCK) on flaw.dtTime between @queryStartTime and @queryEndTime AND job.klKey=flaw.klJobKey and job.lFlawId=flaw.lFlawId
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptimage] img WITH (NOLOCK) on img.flawtime between @queryStartTime and @queryEndTime AND flaw.pklFlawKey=img.klFlawKey
        """

        uuid_list: list[str] = data.Uuid if isinstance(data.Uuid, list) else [data.Uuid]
        uuid_params = {f"uuid_{i}": uuid for i, uuid in enumerate(uuid_list)}
        uuid_placeholders = ", ".join([f":uuid_{i}" for i in range(len(uuid_list))])
        uuid_where = f"WHERE job.UUID IN ({uuid_placeholders})"

        full_query = f"""
        {sql_query}
        {uuid_where}
        ORDER BY flaw.pklFlawKey
        """
        try:
            result_df = pd.read_sql(text(full_query), session.bind, params=uuid_params | {'JobID': job_id})
        except OperationalError as e:
            ic(e)
        except Exception as e:
            ic(e)
        results = []

        def blob_to_base64(a):
            width = a[0] + a[1] * 256
            height = a[4] + a[5] * 256

            if width == 0 or height == 0:
                return None

            # 使用 NumPy 建立像素數據陣列
            pixel_data = np.frombuffer(a, dtype=np.uint8, offset=8).reshape((height, width))

            # 將像素數據轉換為 PIL.Image 對象
            bmp_show_img = Image.fromarray(pixel_data, mode='L')

            # 使用內存中的字節數據
            with io.BytesIO() as img_byte_array:
                bmp_show_img.save(img_byte_array, format='PNG')
                img_byte_array.seek(0)  # 重設游標到起點
                img_byte_array = img_byte_array.read()

            # 將字節數據編碼為 base64
            base64_string = base64.b64encode(img_byte_array).decode('utf-8')

            return base64_string

# 處理查詢結果
        for idx, row in result_df.iterrows():
            blob_data = row.iImage
            base64_string = blob_to_base64(blob_data)

            if base64_string:
                results.append({
                    "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
                    "fileName": row.FileName,
                    "jobKey": row.JobKey,
                    "flawKey": row.FlawKey,
                    "flawId": row.FlawId,
                    "x": row.dCD,
                    "y": row.dMD,
                    'image': f"data:image/png;base64,{base64_string}",
                    "rect": [
                        {
                            "wintrissDefectName": f"{row.DefectName}",
                            "skyeyeCategory": f"{row.skyeyeCategory}",
                            "defectName": f"{row.DefectNameDetail}",
                            "topLeftX": f"{row.TopLeftX}",
                            "topLeftY": f"{row.TopLeftY}",
                            "bottomRightX": f"{row.BottomRightX}",
                            "bottomRightY": f"{row.BottomRightY}"
                        }
                    ],
                    "uuid": row.UUID,
                    "reconfirmOk": row.ReconfirmIsOK,
                    "reconfirmCategory": row.ReconfirmCategry,
                    "reconfirmDefect": row.ReconfirmDefectNameDetail,
                    "reconfirmComment": row.ReconfirmComment,
                    "width": row.dWidth,
                    "length": row.dLength,
                    "area": row.dArea,
                    }),

        # 關閉會話
        session.close()
        # 使用範例：
        png_files_base64 = results
        return png_files_base64

class SkyeyeImageRealtimeBll:
    def __init__(self):
        # 直接用你的固定連線方式
        server = "10.10.2.50"
        database = "GREENZONE"
        password = urlquote("Fta@2022")
        conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        self.engine = create_engine(
            conn_str,
            fast_executemany=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10
        )
        self.Session = sessionmaker(bind=self.engine)      
    def ReadFromDb(self, data):
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')
        session = self.Session()
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

        skyeyeCategory = getattr(data, "SkyeyeCategory", [])
        skyeyeDefectName = []
        if hasattr(data, "Category") and data.Category:
            skyeyeDefectName = [item.split("_")[1] for item in data.Category if "_" in item]        
        
<<<<<<< HEAD
        sql_query = """
=======
        sql_query = f"""
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME());
DECLARE @queryEndTime  datetime2 = SYSDATETIME();
DECLARE @jobKey int=0;
DECLARE @machineName varchar(max)='20'

SELECT @queryStartTime=pdate FROM [SRVAD1].[AMIS].[dbo].[amreel]
WHERE mname=@machineName
ORDER BY pdate desc
OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

SELECT * FROM (
    SELECT
        job.[UUID]
        ,job.[FileName]
        ,job.[dtTime]
        ,job.[klKey] JobKey
        ,job.[lFlawId] FlawId
        ,flaw.[pklFlawKey] FlawKey
        ,job.[DefectName]
        ,job.[dCD]
        ,job.[dMD]
        ,job.[dWidth]
        ,job.[dLength]
        ,job.[dArea]
        ,job.[TopLeftX]
        ,job.[TopLeftY]
        ,job.[BottomRightX]
        ,job.[BottomRightY]
        ,job.[DefectNameCategory] AS skyeyeCategory
        ,job.[DefectNameDetail]
        ,img.iImage
        ,rec.[IsOK] AS ReconfirmIsOK
        ,rec.[DefectNameCategory] AS ReconfirmCategry
        ,rec.[DefectNameDetail] AS ReconfirmDefectNameDetail
        ,rec.[Comment] AS ReconfirmComment
    FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
    LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result_Reconfirm] rec on job.UUID=rec.UUID
    LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw on flaw.dtTime between @queryStartTime and @queryEndTime AND job.klKey=flaw.klJobKey and job.lFlawId=flaw.lFlawId
    LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptimage] img on img.flawtime between @queryStartTime and @queryEndTime AND flaw.pklFlawKey=img.klFlawKey
    WHERE job.dtTime >= @queryStartTime
) p
        """
<<<<<<< HEAD
        # -----------------------
        # Query parameters
        # -----------------------
        params = {}
        # -----------------------
        # Query conditions
        # -----------------------        
        conditions = []                

        # 動態加入 X / Y 範圍條件
        range_conditions = {
            "dCD": ("RangeXStart", "RangeXEnd"),
            "dMD": ("RangeYStart", "RangeYEnd")
        }

        for col, (start_attr, end_attr) in range_conditions.items():
            start_val = getattr(data, start_attr)
            end_val = getattr(data, end_attr)
            if start_val is not None and end_val is not None:
                conditions.append(f"job.{col} between :{start_attr} and :{end_attr}")
                params[start_attr] = start_val
                params[end_attr] = end_val

        # -----------------------
        # Wintriss category filter
        # ----------------------- 
        large = ['大黑汙點', '大透明點', '大破孔']
        medium = ['中黑汙點', '中透明點', '中破孔']
        small = ['小黑汙點', '小透明點', '小破孔']
        
        wintrissCategory_filtered = large + medium + small

        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in small]
            
        if wintrissCategory_filtered:
            values = ",".join(f"'{v}'" for v in wintrissCategory_filtered)
            conditions.append(f"p.DefectName NOT IN ({values})")

        # -----------------------
        # Skyeye category filter
        # -----------------------            
        if skyeyeCategory:
            values = ",".join(f"'{v}'" for v in skyeyeCategory)
            conditions.append(f"p.DefectNameCategory IN ({values})")

        if skyeyeDefectName:
            values = ",".join(f"'{v}'" for v in skyeyeDefectName)
            conditions.append(f"p.DefectNameDetail IN ({values})")
            
        # -----------------------
        # 組 WHERE
        # -----------------------            
        if conditions:
            where_clause = " AND ".join(conditions)
            order_clause = "ORDER BY FlawKey"
            sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"             

        # -----------------------
        # Execute SQL
        # -----------------------            
        try:   
            
            with self.session() as session:
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)

        except OperationalError as e:
            logger.error(f"DB OperationalError: {e}")
            raise
        except Exception as e:
            logger.error(f"ReadFromDb error: {e}")
            raise

        def blob_to_base64(blob_bytes: bytes) -> Optional[str]:
            if not blob_bytes:
                return None
            width = blob_bytes[0] + blob_bytes[1] * 256
            height = blob_bytes[4] + blob_bytes[5] * 256
            if width == 0 or height == 0:
                return None

            pixel_data = np.frombuffer(blob_bytes, dtype=np.uint8, offset=8).reshape((height, width))
            bmp_img = Image.fromarray(pixel_data, mode='L')

            with io.BytesIO() as buf:
                bmp_img.save(buf, format='PNG')
                return base64.b64encode(buf.getvalue()).decode('utf-8')

        def row_to_dict(row):
            img_base64 = blob_to_base64(row.iImage)
            if not img_base64:
                return None

            return {
                "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
                "fileName": row.FileName,
                "jobKey": row.JobKey,
                "flawKey": row.FlawKey,
                "flawId": row.FlawId,
                "x": row.dCD,
                "y": row.dMD,
                "image": f"data:image/png;base64,{img_base64}",
                "rect": [{
                    "wintrissDefectName": row.DefectName,
                    "skyeyeCategory": row.skyeyeCategory,
                    "defectName": row.DefectNameDetail,
                    "topLeftX": row.TopLeftX,
                    "topLeftY": row.TopLeftY,
                    "bottomRightX": row.BottomRightX,
                    "bottomRightY": row.BottomRightY
                }],
                "uuid": row.UUID,
                "reconfirmOk": row.ReconfirmIsOK,
                "reconfirmCategory": row.ReconfirmCategry,
                "reconfirmDefect": row.ReconfirmDefectNameDetail,
                "reconfirmComment": row.ReconfirmComment,
                "width": row.dWidth,
                "length": row.dLength,
                "area": row.dArea
            }

        results = [row_to_dict(row) for _, row in result_df.iterrows() if row_to_dict(row)]

        return results
    
class SkyeyeJudgeBll:
    def __init__(self):
        try:
            self.session = get_session("SRVMSDBA2_SKYEYE")

        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
    
    def copy_image_to_retrainning_folder(self, data, destinationfolderpath):
        image = json.loads(data.Image)
        sourcefolderpath = ""
        if data.MachineName == "18":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產二處\PM18"
        elif data.MachineName == "19":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產二處\PM19"
        elif data.MachineName == "20":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產三處\PM20"
        elif data.MachineName == "21":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產一處\PM21"
        else:
            raise ValueError(f"Unknown machineName: {data.MachineName}")

        file_prefix = image['fileName'][:6]  # 取 fileName 前六個字元
        sourcefolderpath = fr"{sourcefolderpath}\{image['skyeyeCategoryOriginal']}\{file_prefix}"
        sourcefolderpath = sourcefolderpath.replace('汙', '污')
        fullfilename = fr"{sourcefolderpath}\{image['fileName']}"

        # 檢查來源檔案和目的地資料夾是否存在
        if os.path.isfile(fullfilename) and os.path.isdir(destinationfolderpath):
            # 如果條件成立，複製檔案
            try:
                shutil.copy(fullfilename, destinationfolderpath)
                logger.info(f"檔案已成功複製到 {destinationfolderpath}")
            except Exception as e:
                logger.info(f"複製檔案時發生錯誤: {e}")
        else:
            if not os.path.isfile(fullfilename):
                logger.info(f"來源檔案不存在: {fullfilename}")
            if not os.path.isdir(destinationfolderpath):
                logger.info(f"目的地資料夾不存在: {destinationfolderpath}")

    def copy_json_to_retrainning_folder(self, image, destinationfolderpath):
# datasetname
# 『死紋』填入：DeathLines_temporary
# 『污點』填入：Stain_temporary
# 『透明點』填入：Transparent_temporary
# 『破孔』填入：BrokenHole_temporary
        category = image['skyeyeCategory']

        if category == "汙點":
            datasetname = r"Stain_temporary"
        elif category == "破孔":
            datasetname = r"BrokenHole_temporary"
        elif category == "透明點":
            datasetname = r"Transparent_temporary"
        elif category == "死紋":
            datasetname = r"DeathLines_temporary"
        else:
            raise ValueError(f"Unknown skyeyeCategory: {category}")
        obj = {
                "ai_image": image["fileName"],
                "datasetname": datasetname,
                "image_type": "",
                "predict_type": "DETECT_AND_CLASSIFY",
                "product": "",
                "remark": {
                    "equipment": image.get("machineName", "20")
                },
                "result": []
            }

        for rect in image['rect']:
# class
# 若為『一般汙點、破紙夾入』請填入：汙點_合併
# 若為『毛刷破孔、塗後掃描器破孔』請填入：毛刷_塗後掃描器破孔
# 若不屬於該類別內的分類，請填入：無此分類
            defect = image['skyeyeDefect']

            if defect == "一般汙點" or defect == "破紙夾入":
                className = r"汙點_合併"
            elif defect == "毛刷破孔" or defect == "塗後掃描器破孔":
                className = r"毛刷_塗後掃描器破孔"
            elif defect == "無法判定":
                className = r"無此分類"
            else:
                className = defect
            obj_result = {
                "bbox": [rect["topLeftX"], rect["topLeftY"], rect["bottomRightX"], rect["bottomRightY"]],
                "class": className
            }
            obj["result"].append(obj_result)
        fullfilename = fr"{destinationfolderpath}\{Path(image['fileName']).with_suffix('.json')}"
        Path(fullfilename).write_text(json.dumps(obj, ensure_ascii=False, indent=4), encoding="utf-8")

    def add(self, data):
        image = json.loads(data.Image)

        if image["skyeyeCategoryOriginal"] == image["skyeyeCategory"]:
            destinationfolderpath = r"\\10.10.24.191\equipment_images"
        else:
            destinationfolderpath = rf"\\10.10.24.191\images\Wintrriss_Misjudgment\{image['skyeyeCategory']}"
            pass

        try:
            self.copy_image_to_retrainning_folder(data, destinationfolderpath)
            self.copy_json_to_retrainning_folder(image, destinationfolderpath)
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            logging.debug(msg)
            return {'message': msg}, 500

        sql_query = """
        INSERT INTO [SKYEYE].[dbo].[WINTRISS_PM20_Result_Reconfirm] 
        (UUID, IsOK, busr, mname, DefectNameCategory, DefectNameDetail, Comment) 
        values (:uuid, :isOk, :busr, :mname, :defectCategory, :defectNameDetail, :comment)
        """
        
        comment = image.get("reconfirmComment")
        if comment is None:
            comment = "None"        

        params = {
            "uuid": image['uuid'],
            "isOk": image['reconfirmOk'],
            "busr": data.current_login_id,
            "mname": data.MachineName,
            "defectCategory": image['skyeyeCategory'],
            "defectNameDetail": image['skyeyeDefect'],
            "comment": comment
        }

        try:
            with self.session() as session:
                result = session.execute(text(sql_query), params=params)
                session.commit()

            return result.rowcount
        except SQLAlchemyError as e:
            if '2627' in str(e.orig):  # 檢查是否為主鍵重複錯誤 (SQL Error Code 2627)
                msg = f'{self.__class__.__name__} | Primary key violation: {str(e)}'
                logging.debug(msg)
                return {'message': 'Primary key already exists, duplicate entry.'}, 400
            
            msg = f'{self.__class__.__name__} | Integrity error: {str(e)}'
            logging.debug(msg)
            return {'message': msg}, 500
        except Exception as e:
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            logging.debug(msg)
            return {'message': msg}, 500

    
class SkyeyeReelBll:
    def __init__(self):
        try:
            self.session = get_session("SRVMSDBA2_SKYEYE")
            self.mnameMapper = {
                "20": None,
                "21": None
            }
        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
  
    def browse(self, data):
        machine = getattr(data, "MachineName", None)
        if not machine:
            return None
        
        # 懶初始化 DAL
        if self.mnameMapper.get(machine) is None:
            try:
                if machine == "20":
                    self.mnameMapper[machine] = FTA_PM20_skyeyeDal()
                elif machine == "21":
                    self.mnameMapper[machine] = FTA_PM21_skyeyeDal()
            except NameError:
                logger.warning(f"DAL for Machine {machine} is not defined.")
                return None        

        dal = self.mnameMapper.get(machine)
        return dal.query(data) if dal else None

    def ReadFromDb(self, data):
        session = self.session()
        ddl_query = """
DECLARE @queryStartTime datetime2 = DATEADD(hour, -2, SYSDATETIME());
DECLARE @queryEndTime datetime2 = SYSDATETIME();
DECLARE @JobID varchar(max) = :JobID;

-- 計算查詢的開始和結束時間
SELECT @queryStartTime = DATEADD(hour, -2, MIN(Date)), 
       @queryEndTime = DATEADD(hour, 2, MAX(Date)) 
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))

-- 刪除局部臨時表
IF OBJECT_ID('tempdb..##jobKeys', 'U') IS NOT NULL DROP TABLE ##jobKeys;
IF OBJECT_ID('tempdb..##AllDefectNames', 'U') IS NOT NULL DROP TABLE ##AllDefectNames;
IF OBJECT_ID('tempdb..##JobDefectCombinations', 'U') IS NOT NULL DROP TABLE ##JobDefectCombinations;

-- 建立臨時表
CREATE TABLE ##jobKeys (klKey INT)
INSERT INTO ##jobKeys (klKey)
SELECT klKey 
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))

CREATE TABLE ##AllDefectNames (DefectNameDetail NVARCHAR(MAX))
INSERT INTO ##AllDefectNames (DefectNameDetail)
SELECT DefectCategory+'_'+DefectNameDetail
FROM [SKYEYE].[dbo].[WINTRISS_DefectCode]

CREATE TABLE ##JobDefectCombinations (JobID NVARCHAR(MAX), klKey INT, DefectNameDetail NVARCHAR(MAX))
INSERT INTO ##JobDefectCombinations (JobID, klKey, DefectNameDetail)
SELECT jobs.JobID, jobs.klKey, defect.DefectNameDetail
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] jobs
CROSS JOIN ##AllDefectNames defect
WHERE jobs.JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))
        """

        sql_query = """
-- 動態生成 PIVOT 的列名
DECLARE @PivotColumns NVARCHAR(MAX)
SET @PivotColumns = STUFF((
    SELECT DISTINCT ',' + QUOTENAME(DefectNameDetail)
    FROM ##AllDefectNames
    FOR XML PATH(''), TYPE
).value('.', 'NVARCHAR(MAX)'), 1, 1, '')

DECLARE @queryStartTime datetime2 = DATEADD(hour, -2, SYSDATETIME());
DECLARE @queryEndTime datetime2 = SYSDATETIME();
DECLARE @JobID varchar(max) = :JobID;

-- 計算查詢的開始和結束時間
SELECT @queryStartTime = DATEADD(hour, -2, MIN(Date)), 
       @queryEndTime = DATEADD(hour, 2, MAX(Date)) 
FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))
AND Date >= Dateadd(YEAR,-1,GETDATE())


-- 動態 SQL 查詢
DECLARE @PivotQuery NVARCHAR(MAX)
SET @PivotQuery = N'
SELECT JobID relno, ' + @PivotColumns + '
FROM (
    SELECT JobID, DefectNameDetail, Sum(DefectCount) DefectCount FROM (
        SELECT
            comb.JobID,
            comb.DefectNameDetail
            ,ISNULL(COUNT(job.DefectNameDetail), 0) AS DefectCount
            ,job.dMD
            ,MAX(reel.[lenth]) AS lenth
        FROM ##JobDefectCombinations comb
        LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
            ON comb.DefectNameDetail = CONCAT(job.DefectNameCategory, ''_'', job.DefectNameDetail)
            AND job.dtTime BETWEEN @queryStartTime AND @queryEndTime
            AND job.klKey = comb.klKey
        LEFT JOIN [srvad1].[amis].[dbo].[amreel] reel on comb.JobID = reel.relno COLLATE Chinese_Traditional_Bopomofo_100_CS_AS_KS_WS
        GROUP BY comb.JobID ,comb.DefectNameDetail ,job.dMD ,reel.[lenth]
        ) src
        WHERE dMD IS NULL OR dMD<=lenth
        GROUP BY JobID, DefectNameDetail
    ) AS SourceTable
PIVOT (
    MAX(DefectCount)
    FOR DefectNameDetail IN (' + @PivotColumns + ')
) AS PivotTable
ORDER BY JobID
'

-- 執行動態 SQL
EXEC sp_executesql @PivotQuery, N'@queryStartTime datetime2, @queryEndTime datetime2', @queryStartTime, @queryEndTime
        """
        cleanup_query = """
        DROP TABLE ##jobKeys;
        DROP TABLE ##AllDefectNames;
        DROP TABLE ##JobDefectCombinations;
        """
        
        # -----------------------
        # Query parameters
        # -----------------------
        params = {
            "JobID": data.ReelNoCsv
        }
        # -----------------------
        # Query conditions
        # -----------------------        
        conditions = []  
        
        # -----------------------
        # 組 WHERE
        # -----------------------            
        if conditions:
            where_clause = " AND ".join(conditions)
            order_clause = "ORDER BY job.dtTime DESC"
            sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"            
            
        # -----------------------
        # Execute SQL
        # -----------------------             

        try:
            with session.begin():
                session.execute(text(ddl_query), params=params)
            with session.begin():
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)
        except OperationalError as e:
            logger.error(f"DB OperationalError: {e}")
            raise
        except Exception as e:
            logger.error(f"ReadFromDb error: {e}")
            raise
        finally:
            try:
                with session.begin():
                    session.execute(text(cleanup_query))
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
            session.close()            
        
        result_dict_list_df = result_df.replace({np.nan: None}).to_dict(orient='records')
        return result_dict_list_df    
    
# class SkyeyeReelRealtimeBll:
#     def __init__(self):
#         try:
#             conn_info = load_connection_info("SRVMSDBA2_SKYEYE")
#             server = conn_info["server"]
#             database = conn_info["database"]
#             username = conn_info["username"]
#             password = conn_info["password"]

#             conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
#             self.engine = create_engine(
#                 conn_str,
#                 fast_executemany=True,
#                 pool_pre_ping=True,
#                 pool_recycle=1800,
#                 pool_size=5,
#                 max_overflow=10
#             )
#             self.session = sessionmaker(bind=self.engine)
#         except Exception as e:
#             msg = f'skyeye.py | An error occurred: {str(e)}'
#             logging.error(msg)

#     def browse(self, data):
#         mnameMapper = {"20": FTA_PM20_skyeye_reelDal(), "21": FTA_PM21_skyeye_reelDal()}
#         dal = None
#         if 'MachineName' in data and data['MachineName'] in mnameMapper:
#             dal = mnameMapper[data['MachineName']]
#         else:
#             return None

#         rst = dal.query(data)
#         # ic(type(rst))
#         for result in rst:
#             # ic(type(result))
#             # result['TagName'] = data['TagNameOrigin']
#             pass
#         return rst

#     def ReadFromDb(self, data):
#         session = self.session()

#         # 自定義 SQL 查詢語句
#         # 執行 DDL 查詢
#         ddl_query = """
# DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME())
# DECLARE @machineName varchar(max)='20'
# DECLARE @JobID varchar(max) = :JobID;

# SELECT @queryStartTime=pdate FROM [SRVAD1].[AMIS].[dbo].[amreel]
# WHERE mname=@machineName
# ORDER BY pdate desc
# OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

# -- 檢查並刪除全局臨時表
# IF OBJECT_ID('tempdb..##jobKeys', 'U') IS NOT NULL
#     DROP TABLE ##jobKeys;

# IF OBJECT_ID('tempdb..##AllDefectNames', 'U') IS NOT NULL
#     DROP TABLE ##AllDefectNames;

# IF OBJECT_ID('tempdb..##JobDefectCombinations', 'U') IS NOT NULL
#     DROP TABLE ##JobDefectCombinations;

# -- 創建全局臨時表
# CREATE TABLE ##jobKeys (klKey INT)
# INSERT INTO ##jobKeys (klKey)
# SELECT klKey 
# FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] 
# WHERE JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))

# CREATE TABLE ##AllDefectNames (DefectNameDetail NVARCHAR(MAX))
# INSERT INTO ##AllDefectNames (DefectNameDetail)
# SELECT DISTINCT DefectNameDetail 
# FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result]

# CREATE TABLE ##JobDefectCombinations (JobID NVARCHAR(MAX), klKey INT, DefectNameDetail NVARCHAR(MAX))
# INSERT INTO ##JobDefectCombinations (JobID, klKey, DefectNameDetail)
# SELECT jobs.JobID, jobs.klKey, defect.DefectNameDetail
# FROM [srvmsdba1].[FlawInspection].[dbo].[duptjobs] jobs
# CROSS JOIN ##AllDefectNames defect
# WHERE jobs.JobID IN (SELECT value FROM STRING_SPLIT(@JobID, ','))
#         """

#         sql_query = f"""
# DECLARE @queryStartTime datetime2 = DATEADD(hour, -2, SYSDATETIME());
# DECLARE @machineName varchar(max)='20'
# DECLARE @JobID varchar(max) = :JobID;


# -- 計算查詢的開始和結束時間
# SELECT @queryStartTime=pdate FROM [SRVAD1].[AMIS].[dbo].[amreel]
# WHERE mname=@machineName
# ORDER BY pdate desc
# OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

# -- 動態生成 PIVOT 的列名
# DECLARE @PivotColumns NVARCHAR(MAX)
# SET @PivotColumns = STUFF((
#     SELECT DISTINCT ',' + QUOTENAME(DefectNameDetail)
#     FROM ##AllDefectNames
#     FOR XML PATH(''), TYPE
# ).value('.', 'NVARCHAR(MAX)'), 1, 1, '')

# -- 動態 SQL 查詢
# DECLARE @PivotQuery NVARCHAR(MAX)
# SET @PivotQuery = N'
# SELECT JobID relno, ' + @PivotColumns + '
# FROM (
#     SELECT
#         comb.JobID,
#         comb.DefectNameDetail,
#         ISNULL(COUNT(job.DefectNameDetail), 0) AS DefectCount
#     FROM ##JobDefectCombinations comb
#     LEFT JOIN [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
#         ON job.DefectNameDetail = comb.DefectNameDetail
#         AND job.klKey IN (SELECT klKey FROM ##jobKeys)
#         AND job.dtTime > @queryStartTime
#         AND job.klKey = comb.klKey
#     LEFT JOIN [srvmsdba1].[FlawInspection].[dbo].[duptjobs] jobs
#         ON job.klKey = jobs.klKey 
#         AND jobs.Date > @queryStartTime
#     GROUP BY comb.JobID, comb.DefectNameDetail
# ) AS SourceTable
# PIVOT (
#     MAX(DefectCount)
#     FOR DefectNameDetail IN (' + @PivotColumns + ')
# ) AS PivotTable
# ORDER BY JobID'

# -- 執行動態 SQL
# EXEC sp_executesql @PivotQuery, N'@queryStartTime datetime2, @queryStartTime, @queryEndTime
#         """
#         cleanup_query = """
#         DROP TABLE ##jobKeys;
#         DROP TABLE ##AllDefectNames;
#         DROP TABLE ##JobDefectCombinations;
#         """
        
#         # 執行 SQL 查詢
#         cond = []
#         # cond.append("klKey= @jobKey")
#         # cond.append("job.dtTime between @queryStartTime and @queryEndTime")
#         params = {}
#         params['JobID'] = getattr(data, "ReelNoCsv", None)

#         # function_array = getattr(filter, 'function_array', None)
#         # if hasattr(data, "Category") and data.Category is not None and len(data.Category) > 0:
#         #     cond.append("job.DefectNameDetail IN ({})".format(",".join("'{}'".format(category) for category in data.Category)))
#         #     params['category'] = data.Category
#         try:
#             if cond:
#                 # 使用 AND 運算符將條件組合在一起
#                 where_clause = " AND ".join(cond)
#                 order_clause = "order by flaw.pklFlawKey"
#                 sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"
#             with session.begin():
#                 session.execute(text(ddl_query), params=params)
#             with session.begin():
#                 result_df = pd.read_sql(text(sql_query), session.bind, params=params)
                
#         except OperationalError as e:
#             logger.exception("Database OperationalError occurred")
#             raise
#         except Exception as e:
#             logger.exception("Unexpected error occurred")
#             raise


#         with session.begin():
#             session.execute(text(cleanup_query))
#         session.close()
#         # 使用範例：
#         result_dict_list_df = result_df.to_dict(orient='records')
#         return result_dict_list_df
        
            
    
class skyeyeRealtimeBll:
    def __init__(self):
        try:
            self.session = get_session("SRVMSDBA2_SKYEYE")
            
            self.mnameMapper = {
                "20": None,
                "21": None
            }
        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")

    def browse(self, data):

        machine = getattr(data, "MachineName", None)
        if not machine:
            return None
        
        # 懶初始化 DAL
        if self.mnameMapper.get(machine) is None:
            try:
                if machine == "20":
                    self.mnameMapper[machine] = FTA_PM20_skyeyeDal()
                elif machine == "21":
                    self.mnameMapper[machine] = FTA_PM21_skyeyeDal()
            except NameError:
                logger.warning(f"DAL for Machine {machine} is not defined.")
                return None        

        dal = self.mnameMapper.get(machine)
        return dal.query(data) if dal else None

    def ReadFromDb(self,data):
        skyeyeCategory = getattr(data, "SkyeyeCategory", [])
        skyeyeDefectName = []
        
        if hasattr(data, "Category") and data.Category:
            skyeyeDefectName = [
                item.split("_")[1] for item in data.Category if "_" in item
            ]

        sql_query = """
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME());
DECLARE @machineName varchar(max)='20';

SELECT @queryStartTime= Date 
FROM [SRVMSDBA1].[FlawInspection].[dbo].[duptjobs] 
ORDER BY Date DESC
OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

SELECT
    job.[UUID],
    job.[dtTime],
    job.[klKey] JobKey,
    job.[lFlawId] FlawId,
    flaw.[pklFlawKey] FlawKey,
    job.[DefectName],
    job.[dCD],
    job.[dMD],
    job.[dWidth],
    job.[dLength],
    job.[dArea],
    job.[TopLeftX],
    job.[TopLeftY],
    job.[BottomRightX],
    job.[BottomRightY],
    job.DefectNameCategory AS skyeyeCategory,
    job.[DefectNameDetail]
FROM [SKYEYE].[dbo].[WINTRISS_PM20_Result] job
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw 
ON flaw.dtTime >= @queryStartTime
AND job.klKey=flaw.klJobKey 
AND job.lFlawId=flaw.lFlawId
"""
        
        # -----------------------
        # Query parameters
        # -----------------------
        params = {}
        # -----------------------
        # Query conditions
        # -----------------------        
        conditions = [
            "job.dtTime > @queryStartTime"
        ]        

        # -----------------------
        # Wintriss category filter
        # ----------------------- 
        large = ['大黑汙點', '大透明點', '大破孔']
        medium = ['中黑汙點', '中透明點', '中破孔']
        small = ['小黑汙點', '小透明點', '小破孔']
        
        wintrissCategory_filtered = large + medium + small

        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [c for c in wintrissCategory_filtered if c not in small]
            
        if wintrissCategory_filtered:
            values = ",".join(f"'{v}'" for v in wintrissCategory_filtered)
            conditions.append(f"job.DefectName NOT IN ({values})")

        # -----------------------
        # Skyeye category filter
        # -----------------------            
        if skyeyeCategory:
            values = ",".join(f"'{v}'" for v in skyeyeCategory)
            conditions.append(f"job.DefectNameCategory IN ({values})")

        if skyeyeDefectName:
            values = ",".join(f"'{v}'" for v in skyeyeDefectName)
            conditions.append(f"job.DefectNameDetail IN ({values})")

        # -----------------------
        # 組 WHERE
        # -----------------------            
        if conditions:
            where_clause = " AND ".join(conditions)
            order_clause = "ORDER BY job.dtTime DESC"
            sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"            
            
        # -----------------------
        # Execute SQL
        # -----------------------            
        try:   
            
            with self.session() as session:
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)

        except OperationalError as e:
            logger.error(f"DB OperationalError: {e}")
            raise
        except Exception as e:
            logger.error(f"ReadFromDb error: {e}")
            raise

        results = [
            {
                "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S') if row.dtTime else None,
                "jobKey": row.JobKey,
                "flawId": row.FlawId,
                "flawKey": row.FlawKey,
                "skyeyeCategory": row.skyeyeCategory,
                "categoryName": row.DefectNameDetail,
                "x": row.dCD,
                "y": row.dMD,
                "width": row.dWidth,
                "length": row.dLength,
                "area": row.dArea,
                "uuid": row.UUID
            }
            for row in result_df.itertuples()
        ]
        
        return results


class SkyeyeRuleAlarmBll:
    def browse(self, data):
=======
        # 執行 SQL 查詢
        cond = []
        # cond.append("klKey= @jobKey")
        # cond.append("job.dtTime >= @queryStartTime")
        params = {}
        # params['JobID'] = f"{data.ReelNo}"

        if getattr(data, "RangeXStart", False) and getattr(data, "RangeXEnd", False):
            cond.append("dCD between :RangeXStart and :RangeXEnd")
            params['RangeXStart'] = f"{data.RangeXStart}"
            params['RangeXEnd'] = f"{data.RangeXEnd}"
            
        if getattr(data, "RangeYStart", False) and getattr(data, "RangeYEnd", False):
            cond.append("dMD between :RangeYStart and :RangeYEnd")
            params['RangeYStart'] = f"{data.RangeYStart}"
            params['RangeYEnd'] = f"{data.RangeYEnd}"

        wintrissCategory_filtered = ['大黑汙點', '大透明點', '大破孔', '中黑汙點', '小黑汙點', '中透明點', '小透明點', '中破孔', '小破孔']
        wintrissCategory_large = ['大黑汙點', '大透明點', '大破孔']
        wintrissCategory_medium = ['中黑汙點', '中透明點', '中破孔']
        wintrissCategory_small = ['小黑汙點', '小透明點', '小破孔']
        if getattr(data, "ShowLarge", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_large]
        if getattr(data, "ShowMedium", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_medium]
        if getattr(data, "ShowSmall", False):
            wintrissCategory_filtered = [item for item in wintrissCategory_filtered if item not in wintrissCategory_small]
        if wintrissCategory_filtered:
            cond.append("DefectName NOT IN ({})".format(",".join("'{}'".format(wcategory) for wcategory in wintrissCategory_filtered)))

        if skyeyeCategory:
            cond.append("skyeyeCategory IN ({})".format(",".join("'{}'".format(category) for category in skyeyeCategory)))
            params['category'] = skyeyeCategory

        if skyeyeDefectName:
            cond.append("DefectNameDetail IN ({})".format(",".join("'{}'".format(defect) for defect in skyeyeDefectName)))
            params['category'] = skyeyeDefectName

        try:
            if cond:
                where_clause = " AND ".join(cond)
                order_clause = "order by FlawKey"
                sql_query = f"{sql_query} WHERE {where_clause} {order_clause}"
            result_df = pd.read_sql(text(sql_query), session.bind, params=params)
        except OperationalError as e:
            ic(e)
        except Exception as e:
            ic(e)
        results = []

        def blob_to_base64_disk(a):
            width = a[0] + a[1] * 256
            height = a[4] + a[5] * 256

            if width == 0 or height == 0:
                return None

            # 使用 NumPy 建立像素數據陣列
            pixel_data = np.frombuffer(a, dtype=np.uint8, offset=8).reshape((height, width))

            # 將像素數據轉換為 PIL.Image 對象
            bmp_show_img = Image.fromarray(pixel_data, mode='L')

            # 將圖像保存為內存中的字節數據
            img_byte_array = io.BytesIO()
            bmp_show_img.save(img_byte_array, format='PNG')
            img_byte_array = img_byte_array.getvalue()

            # 將字節數據編碼為 base64
            base64_string = base64.b64encode(img_byte_array).decode('utf-8')

            return base64_string      

        def blob_to_base64(a):
            width = a[0] + a[1] * 256
            height = a[4] + a[5] * 256

            if width == 0 or height == 0:
                return None

            # 使用 NumPy 建立像素數據陣列
            pixel_data = np.frombuffer(a, dtype=np.uint8, offset=8).reshape((height, width))

            # 將像素數據轉換為 PIL.Image 對象
            bmp_show_img = Image.fromarray(pixel_data, mode='L')

            # 使用內存中的字節數據
            with io.BytesIO() as img_byte_array:
                bmp_show_img.save(img_byte_array, format='PNG')
                img_byte_array.seek(0)  # 重設游標到起點
                img_byte_array = img_byte_array.read()

            # 將字節數據編碼為 base64
            base64_string = base64.b64encode(img_byte_array).decode('utf-8')

            return base64_string

        # 處理查詢結果
        for idx, row in result_df.iterrows():
            blob_data = row.iImage
            base64_string = blob_to_base64(blob_data)

            if base64_string:
                results.append({
                    "ftaDtm": row.dtTime.strftime('%Y-%m-%d %H:%M:%S'),
                    "fileName": row.FileName,
                    "jobKey": row.JobKey,
                    "flawKey": row.FlawKey,
                    "flawId": row.FlawId,
                    "x": row.dCD,
                    "y": row.dMD,
                    'image': f"data:image/png;base64,{base64_string}",
                    "rect": [
                        {
                            "wintrissDefectName": f"{row.DefectName}",
                            "skyeyeCategory": f"{row.skyeyeCategory}",
                            "defectName": f"{row.DefectNameDetail}",
                            "topLeftX": f"{row.TopLeftX}",
                            "topLeftY": f"{row.TopLeftY}",
                            "bottomRightX": f"{row.BottomRightX}",
                            "bottomRightY": f"{row.BottomRightY}"
                        }
                    ],
                    "uuid": row.UUID,
                    "reconfirmOk": row.ReconfirmIsOK,
                    "reconfirmCategory": row.ReconfirmCategry,
                    "reconfirmDefect": row.ReconfirmDefectNameDetail,
                    "reconfirmComment": row.ReconfirmComment,
                    "width": row.dWidth,
                    "length": row.dLength,
                    "area": row.dArea,
                    }),

        # 關閉會話
        session.close()
        # 使用範例：
        return results


class SkyeyeCategoryBll:
    def __init__(self):
        # 直接用你的固定連線方式
        server = "10.10.2.50"
        database = "GREENZONE"
        password = urlquote("Fta@2022")
        conn_str = f"mssql+pyodbc://sa:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        self.engine = create_engine(
            conn_str,
            fast_executemany=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10
        )
        self.Session = sessionmaker(bind=self.engine)    
    
    def browse(self, data):
        
        temp_root, exe_folder = get_temproot_and_exe_folder()
        json_path = os.path.join(temp_root, 'connections.json')
#         logging.info(f'json_path: {json_path}')

        session = self.Session()

        # 自定義 SQL 查詢語句
        sql_query = f"""
SELECT
    [DefectCategory] primaryCategory,
    [DefectNameDetail] category,
    [isenabled] isEnabled,
    1 [order],
    symbol,
    color
FROM [SKYEYE].[dbo].[WINTRISS_DefectCode]
        """
        # 執行 SQL 查詢
        cond = []
        params = {}

        try:
            where_clause = ""
            if cond and len(cond) > 0:
                # 使用 AND 運算符將條件組合在一起
                where_clause = "WHERE " + " AND ".join(cond)
            order_clause = ""
            sql_query = f"{sql_query} {where_clause} {order_clause}"

            with self.Session() as session:
                result_df = pd.read_sql(text(sql_query), session.bind, params=params)
        except OperationalError as e:
            logger.error(f"OperationalError: {e}")
            result_df = pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            result_df = pd.DataFrame()

        results = []
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
        defects = [
            {"name": "真死紋", "category": "死紋", "symbol": "square", "color": "Green"},
            {"name": "破邊", "category": "死紋", "symbol": "square", "color": "DarkCyan"},
            {"name": "紙邊", "category": "死紋", "symbol": "square", "color": "DarkCyan"},
            {"name": "脫水不良", "category": "死紋", "symbol": "square", "color": "Olive"},

            {"name": "一般汙點", "category": "汙點", "symbol": "triangle", "color": "DarkSlateGray"},
            {"name": "烘缸塗料屑", "category": "汙點", "symbol": "triangle", "color": "LightSlateGray"},
            {"name": "破紙夾入", "category": "汙點", "symbol": "triangle", "color": "Gray"},
            {"name": "破邊", "category": "汙點", "symbol": "triangle", "color": "Silver"},
            {"name": "蚊蟲", "category": "汙點", "symbol": "triangle", "color": "DimGray"},
            {"name": "開口笑", "category": "汙點", "symbol": "triangle", "color": "DarkGray"},

            {"name": "1-5D破孔", "category": "破孔", "symbol": "emptycircle", "color": "OrangeRed"},
            {"name": "1P破邊", "category": "破孔", "symbol": "emptycircle", "color": "Coral"},
            {"name": "毛刷破孔", "category": "破孔", "symbol": "emptycircle", "color": "Fuchsia"},
            {"name": "加溼後開口笑破孔", "category": "破孔", "symbol": "emptycircle", "color": "Purple"},
            {"name": "刮刀著污開口笑", "category": "破孔", "symbol": "emptycircle", "color": "DarkSalmon"},
            {"name": "塗後掃瞄器破孔", "category": "破孔", "symbol": "emptycircle", "color": "MediumOrchid"},
            {"name": "塗料屑破孔", "category": "破孔", "symbol": "emptycircle", "color": "RebeccaPurple"},
            {"name": "網部水針破邊", "category": "破孔", "symbol": "emptycircle", "color": "DarkRed"},
            {"name": "網部破孔", "category": "破孔", "symbol": "emptycircle", "color": "IndianRed"},
            {"name": "壓榨部破孔", "category": "破孔", "symbol": "emptycircle", "color": "DeepPink"},
            {"name": "濕端破孔", "category": "破孔", "symbol": "emptycircle", "color": "Red"},

            {"name": "一般透明點", "category": "透明點", "symbol": "emptydiamond", "color": "DodgerBlue"},
            {"name": "加溼水痕", "category": "透明點", "symbol": "emptydiamond", "color": "DarkCyan"},
            {"name": "油點", "category": "透明點", "symbol": "emptydiamond", "color": "CornflowerBlue"},
            {"name": "破邊", "category": "透明點", "symbol": "emptydiamond", "color": "CornflowerBlue"},
            {"name": "塗佈水痕", "category": "透明點", "symbol": "emptydiamond", "color": "DeepSkyBlue"},
            {"name": "塗料塗料屑", "category": "透明點", "symbol": "emptydiamond", "color": "DarkBlue"},
            {"name": "滴水點", "category": "透明點", "symbol": "emptydiamond", "color": "Blue"},
            {"name": "壓光卡料印痕", "category": "透明點", "symbol": "emptydiamond", "color": "Blue"},
        ]

<<<<<<< HEAD
        results = []
=======
        # 使用範例：
        results = result_df.to_dict(orient='records')
        return results


class SkyeyeJudgeBll:
    def copy_image_to_retrainning_folder(self, data, destinationfolderpath):
        image = json.loads(data.Image)
        sourcefolderpath = ""
        if data.MachineName == "18":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產二處\PM18"
        elif data.MachineName == "19":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產二處\PM19"
        elif data.MachineName == "20":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產三處\PM20"
        elif data.MachineName == "21":
            sourcefolderpath = r"\\10.10.3.12\d\DefectPic\生產一處\PM21"
        else:
            raise ValueError(f"Unknown machineName: {data.MachineName}")

        file_prefix = image['fileName'][:6]  # 取 fileName 前六個字元
        sourcefolderpath = fr"{sourcefolderpath}\{image['skyeyeCategoryOriginal']}\{file_prefix}"
        sourcefolderpath = sourcefolderpath.replace('汙', '污')
        fullfilename = fr"{sourcefolderpath}\{image['fileName']}"

        # 檢查來源檔案和目的地資料夾是否存在
        if os.path.isfile(fullfilename) and os.path.isdir(destinationfolderpath):
            # 如果條件成立，複製檔案
            try:
                shutil.copy(fullfilename, destinationfolderpath)
                print(f"檔案已成功複製到 {destinationfolderpath}")
            except Exception as e:
                print(f"複製檔案時發生錯誤: {e}")
        else:
            if not os.path.isfile(fullfilename):
                print(f"來源檔案不存在: {fullfilename}")
            if not os.path.isdir(destinationfolderpath):
                print(f"目的地資料夾不存在: {destinationfolderpath}")

    def copy_json_to_retrainning_folder(self, image, destinationfolderpath):
# datasetname
# 『死紋』填入：DeathLines_temporary
# 『污點』填入：Stain_temporary
# 『透明點』填入：Transparent_temporary
# 『破孔』填入：BrokenHole_temporary
        category = image['skyeyeCategory']

        if category == "汙點":
            datasetname = r"Stain_temporary"
        elif category == "破孔":
            datasetname = r"BrokenHole_temporary"
        elif category == "透明點":
            datasetname = r"Transparent_temporary"
        elif category == "死紋":
            datasetname = r"DeathLines_temporary"
        else:
            raise ValueError(f"Unknown skyeyeCategory: {category}")
        obj = {
                "ai_image": image["fileName"],
                "datasetname": datasetname,
                "image_type": "",
                "predict_type": "DETECT_AND_CLASSIFY",
                "product": "",
                "remark": {
                    "equipment": "20"
                },
                "result": []
            }

        for rect in image['rect']:
# class
# 若為『一般汙點、破紙夾入』請填入：汙點_合併
# 若為『毛刷破孔、塗後掃描器破孔』請填入：毛刷_塗後掃描器破孔
# 若不屬於該類別內的分類，請填入：無此分類
            defect = image['skyeyeDefect']

            if defect == "一般汙點" or defect == "破紙夾入":
                className = r"汙點_合併"
            elif defect == "毛刷破孔" or defect == "塗後掃描器破孔":
                className = r"毛刷_塗後掃描器破孔"
            elif defect == "無法判定":
                className = r"無此分類"
            else:
                className = defect
            obj_result = {
                "bbox": [rect["topLeftX"], rect["topLeftY"], rect["bottomRightX"], rect["bottomRightY"]],
                "class": className
            }
            obj["result"].append(obj_result)
        fullfilename = fr"{destinationfolderpath}\{Path(image['fileName']).with_suffix('.json')}"
        Path(fullfilename).write_text(json.dumps(obj, ensure_ascii=False, indent=4), encoding="utf-8")

    def add(self, data):
        json_path = os.path.join(current_app.config['folders']['temproot'], 'connections.json')

        cs_name = 'SRVMSBA2_SKYEYE'
        connection_string = get_connection_string(json_path, cs_name)
        engine = create_engine(connection_string, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        image = json.loads(data.Image)
        # destinationfolderpath = r"\\srvafp1.yfy.corp\Home\資管組\public\test"
        if image["skyeyeCategoryOriginal"] == image["skyeyeCategory"]:
            destinationfolderpath = r"\\10.10.24.191\equipment_images"
        else:
            destinationfolderpath = rf"\\10.10.24.191\images\Wintrriss_Misjudgment\{image['skyeyeCategory']}"
            pass

        try:
            self.copy_image_to_retrainning_folder(data, destinationfolderpath)
            self.copy_json_to_retrainning_folder(image, destinationfolderpath)
        except Exception as e:
            ic(e)
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)
            return {'message': msg}, 500

        sql_query = """
INSERT INTO [SKYEYE].[dbo].[WINTRISS_PM20_Result_Reconfirm] (UUID, IsOK, busr, mname, DefectNameCategory, DefectNameDetail, Comment) values (:uuid, :isOk, :busr, :mname, :defectCategory, :defectNameDetail, :comment)
        """
        # 執行 SQL 查詢
        cond = []
        # cond.append("klKey= @jobKey")
        # cond.append("job.dtTime between @queryStartTime and @queryEndTime")
        params = {}
        params['uuid'] = f"{image['uuid']}"
        params['isOk'] = f"{image['reconfirmOk']}"
        params['busr'] = f"{data.current_login_id}"
        params['mname'] = f"{data.MachineName}"
        params['defectCategory'] = f"{image['skyeyeCategory']}"
        params['defectNameDetail'] = f"{image['skyeyeDefect']}"
        # params['defectName'] = f"{image['wintrissDefectName']}"
        # params['DefectNameDetail_original'] = f"{image['skyeyeDefect']}"
        params['comment'] = f"{image['reconfirmComment']}"

        try:
            # where_clause = ""
            # if cond and len(cond) > 0:
            #     # 使用 AND 運算符將條件組合在一起
            #     where_clause = "WHERE " + " AND ".join(cond)
            # order_clause = ""
            sql_query = f"{sql_query}"
            result = session.execute(text(sql_query), params=params)
            session.commit()

            return result.rowcount
        except SQLAlchemyError as e:
            ic(e)
            if '2627' in str(e.orig):  # 檢查是否為主鍵重複錯誤 (SQL Error Code 2627)
                msg = f'{self.__class__.__name__} | Primary key violation: {str(e)}'
                print(msg)
                logging.debug(msg)
                return {'message': 'Primary key already exists, duplicate entry.'}, 400
            else:
                ic(e)
                msg = f'{self.__class__.__name__} | Integrity error: {str(e)}'
                print(msg)
                logging.debug(msg)
                return {'message': msg}, 500
        except Exception as e:
            ic(e)
            msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
            print(msg)
            logging.debug(msg)
            return {'message': msg}, 500
        finally:
            session.close()
        # results = result_df.to_dict(orient='records')


class SkyeyeRuleAlarmBll:
    def browse(self, data):
        json_path = os.path.join(current_app.config['folders']['temproot'], 'connections.json')
        logging.info(f'json_path: {json_path}')
        cs_name = 'SRVMSBA2_SKYEYE'
        connection_string = get_connection_string(json_path, cs_name)
        engine = create_engine(connection_string, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 自定義 SQL 查詢語句
        sql_query = f"""
SELECT
    *
FROM [SKYEYE].[dbo].[XXXXXXXXXX]
        """
        # 執行 SQL 查詢
        cond = []
        params = {}

        if hasattr(data, "Category") and data.Category is not None and len(data.Category) > 0:
            cond.append("DefectNameDetail IN ({})".format(",".join("'{}'".format(category) for category in data.Category)))
            params['category'] = data.Category

        try:
            where_clause = ""
            if cond and len(cond) > 0:
                # 使用 AND 運算符將條件組合在一起
                where_clause = "WHERE " + " AND ".join(cond)
            order_clause = ""
            sql_query = f"{sql_query} {where_clause} {order_clause}"

            # result_df = pd.read_sql(text(sql_query), session.bind, params=params)
        except OperationalError as e:
            ic(e)
        except Exception as e:
            ic(e)

        results = []
        # color = ["red", "green", "blue", "pink", "orange"]
        # symbol = ["circle", "rect", "roundRect", "triangle", "diamond", "pin", "arrow", "none"]
        defects = [
            {"name": "真死紋", "category": "死紋", "symbol": "square", "color": "Green"},
            {"name": "破邊", "category": "死紋", "symbol": "square", "color": "DarkCyan"},
            {"name": "紙邊", "category": "死紋", "symbol": "square", "color": "DarkCyan"},
            {"name": "脫水不良", "category": "死紋", "symbol": "square", "color": "Olive"},

            {"name": "一般汙點", "category": "汙點", "symbol": "triangle", "color": "DarkSlateGray"},
            {"name": "烘缸塗料屑", "category": "汙點", "symbol": "triangle", "color": "LightSlateGray"},
            {"name": "破紙夾入", "category": "汙點", "symbol": "triangle", "color": "Gray"},
            {"name": "破邊", "category": "汙點", "symbol": "triangle", "color": "Silver"},
            {"name": "蚊蟲", "category": "汙點", "symbol": "triangle", "color": "DimGray"},
            {"name": "開口笑", "category": "汙點", "symbol": "triangle", "color": "DarkGray"},

            {"name": "1-5D破孔", "category": "破孔", "symbol": "emptycircle", "color": "OrangeRed"},
            {"name": "1P破邊", "category": "破孔", "symbol": "emptycircle", "color": "Coral"},
            {"name": "毛刷破孔", "category": "破孔", "symbol": "emptycircle", "color": "Fuchsia"},
            {"name": "加溼後開口笑破孔", "category": "破孔", "symbol": "emptycircle", "color": "Purple"},
            {"name": "刮刀著污開口笑", "category": "破孔", "symbol": "emptycircle", "color": "DarkSalmon"},
            {"name": "塗後掃瞄器破孔", "category": "破孔", "symbol": "emptycircle", "color": "MediumOrchid"},
            {"name": "塗料屑破孔", "category": "破孔", "symbol": "emptycircle", "color": "RebeccaPurple"},
            {"name": "網部水針破邊", "category": "破孔", "symbol": "emptycircle", "color": "DarkRed"},
            {"name": "網部破孔", "category": "破孔", "symbol": "emptycircle", "color": "IndianRed"},
            {"name": "壓榨部破孔", "category": "破孔", "symbol": "emptycircle", "color": "DeepPink"},
            {"name": "濕端破孔", "category": "破孔", "symbol": "emptycircle", "color": "Red"},

            {"name": "一般透明點", "category": "透明點", "symbol": "emptydiamond", "color": "DodgerBlue"},
            {"name": "加溼水痕", "category": "透明點", "symbol": "emptydiamond", "color": "DarkCyan"},
            {"name": "油點", "category": "透明點", "symbol": "emptydiamond", "color": "CornflowerBlue"},
            {"name": "破邊", "category": "透明點", "symbol": "emptydiamond", "color": "CornflowerBlue"},
            {"name": "塗佈水痕", "category": "透明點", "symbol": "emptydiamond", "color": "DeepSkyBlue"},
            {"name": "塗料塗料屑", "category": "透明點", "symbol": "emptydiamond", "color": "DarkBlue"},
            {"name": "滴水點", "category": "透明點", "symbol": "emptydiamond", "color": "Blue"},
            {"name": "壓光卡料印痕", "category": "透明點", "symbol": "emptydiamond", "color": "Blue"},
        ]

        # for idx, row in result_df.iterrows():
        #     results.append({
        #         "primaryCategory": defectMapper.get(row.DefectNameDetail, "無分類"),
        #         "category": row.DefectNameDetail,
        #         "isEnabled": True,
        #         "order": 1,
        #         "symbol": symbolMapper.get(row.DefectNameDetail, "triangle"),
        #         "color": colorMapper.get(row.DefectNameDetail, "black"),
        #         }),
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
        for row in defects:
            results.append({
                "primaryCategory": row["category"],
                "category": row["name"],
                "isEnabled": True,
                "order": 1,
                "symbol": row["symbol"],
                "color": row["color"]
<<<<<<< HEAD
            })

=======
                }),
        session.close()
        # 使用範例：
        # results = result_df.to_dict(orient='records')
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
        return results