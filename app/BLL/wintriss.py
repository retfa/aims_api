import time
import pandas as pd
<<<<<<< HEAD
=======
# from icecream import ic
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
import base64
import os
import pyodbc
import numpy as np
<<<<<<< HEAD
import logging
=======
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from PIL import Image
import io

<<<<<<< HEAD
from DAL.srvmsdba1.FlawInspection.duptjobs import duptjobsDal
from utils.db_engine import get_session

logger = logging.getLogger("MES_API")


class wintrissBll:
    def __init__(self):
        try:
            self.session = get_session("SRVMSDBA1_FlawInspection")
            self.mnameMapper = {}            

        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
    def _init_dal(self, machine):
        if machine not in self.mnameMapper:
            if machine == "20":
                self.mnameMapper[machine] = duptjobsDal()
            # 其他機器可加 elif            
    def browse(self, data):
        machine = data.get('MachineName')
        if not machine:
            return None
        self._init_dal(machine)
        dal = self.mnameMapper.get(machine)
        return dal.query(data) if dal else None

    def getLength(self, data):
        machine = data.get('MachineName')
        if not machine:
            return None
        self._init_dal(machine)
        dal = self.mnameMapper.get(machine)
        return dal.currentLenth(data) if dal else None

    def ReadFromDb(self,data):
        session = self.Session()
=======
from app.DAL.srvmsdba1.FlawInspection.duptjobs import duptjobsDal


class wintrissBll:
    def browse(self, data):
        mnameMapper = {"20": duptjobsDal(), }
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

    def getLength(self, data):
        mnameMapper = {"20": duptjobsDal(), }
        dal = None
        if 'MachineName' in data and data['MachineName'] in mnameMapper:
            dal = mnameMapper[data['MachineName']]
        else:
            return None

        rst = dal.currentLenth(data)
        
        print("DAL result:", rst)

        return rst

    def ReadFromDb(self,data):
        # 建立 SQLAlchemy 引擎並連接到 SQL Server
        engine = create_engine("mssql+pyodbc://sa:yfyoljk%40@SRVMSDBA1.yfy.corp/FlawInspection?driver=ODBC+Driver+17+for+SQL+Server",)

        # 建立會話
        Session = sessionmaker(bind=engine)
        session = Session()
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

        # 自定義 SQL 查詢語句
        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME())
DECLARE @queryEndTime  datetime2 = SYSDATETIME()

SELECT @queryStartTime =DATEADD(hour, -2, Date),@queryEndTime =DATEADD(hour, 2, Date) FROM [SRVMSDBA1].[FlawInspection].[dbo].[duptjobs] 
WHERE JobID= :JobID

SELECT 
    flaw.dtTime ftaDtm
    ,flaw.klJobKey JobKey
    ,flaw.lFlawId FlawId
    ,flaw.pklFlawKey FlawKey
    ,flaw.dCD
    ,flaw.dMD
    ,flaw.dWidth
    ,flaw.dLength
    ,flaw.dArea

FROM [SRVMSDBA1].[FlawInspection].[dbo].[duptjobs] job
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw on job.klKey=flaw.klJobKey and job.SourceDB=flaw.SourceDB

WHERE JobID= :JobID
and job.Date between @queryStartTime and @queryEndTime
and flaw.dtTime between @queryStartTime and @queryEndTime
        """
# --and flaw.dCD between :RangeXStart and :RangeXEnd
# --and flaw.dMD between :RangeYStart and :RangeYEnd
# --order by flaw.pklFlawKey
        # 執行 SQL 查詢
        cond = []
        params = {}
        params['JobID'] = f"{data.ReelNo}"

<<<<<<< HEAD

=======
        # if data.station:
        #     cond.append("station = :station")
        #     params['station'] = f"{data.station}"

        # if data.production_line:
        #     cond.append("pm =  :pm")
        #     params['pm'] = f"{data.production_line}"

        # if data.name:
        #     cond.append("mname = :mname")
        #     params['mname'] = f"{data.name}"
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
        try:
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
            category = "污點"
            if idx > len(result_df)*0.66:
                 category = "破孔"
            elif idx > len(result_df)*0.33:
                category = "開口笑"

            results.append({
                "ftaDtm": row.ftaDtm.strftime('%Y-%m-%d %H:%M:%S'),
                "jobKey": row.JobKey,
                "flawId": row.FlawId,
                "flawKey": row.FlawKey,
                "categoryName": category,
                "x": row.dCD,
                "y": row.dMD,
                "width": row.dWidth,
                "length": row.dLength,
                "area": row.dArea,
                }),

        # 關閉會話
        session.close()
        # 使用範例：
        png_files_base64 = results
        return png_files_base64


class wintrissRealtimeBll:
<<<<<<< HEAD
    def __init__(self, folders):
        trace_msg = f'{self.__class__.__name__}'
        logging.info(trace_msg)
        try:
            self.session = get_session("SRVMESDBA1_FlawInspection")
            self.mnameMapper = {
                "20": None,
                "21": None
            }            

        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
=======
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
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
<<<<<<< HEAD
        session = self.Session()
=======
        # 建立 SQLAlchemy 引擎並連接到 SQL Server
        engine = create_engine("mssql+pyodbc://sa:yfyoljk%40@SRVMSDBA1.yfy.corp/FlawInspection?driver=ODBC+Driver+17+for+SQL+Server",)

        # 建立會話
        Session = sessionmaker(bind=engine)
        session = Session()
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

        # 自定義 SQL 查詢語句
        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME())
DECLARE @machineName varchar(max)='20'

SELECT @queryStartTime=pdate FROM [SRVAD1].[AMIS].[dbo].[amreel] 
WHERE mname=@machineName
ORDER BY pdate desc
OFFSET 0 ROW FETCH NEXT 1 ROW ONLY

SELECT
    flaw.dtTime ftaDtm
    ,flaw.pklFlawKey FlawKey
    ,flaw.klJobKey JobKey
    ,flaw.lFlawId FlawId
    ,flaw.dCD
    ,flaw.dMD
	,flaw.dWidth
	,flaw.dLength
	,flaw.dArea

FROM [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw
WHERE flaw.dtTime > @queryStartTime
order by flaw.dtTime desc
        """
# --and flaw.dCD between :RangeXStart and :RangeXEnd
# --and flaw.dMD between :RangeYStart and :RangeYEnd
# --order by flaw.pklFlawKey
        # 執行 SQL 查詢
        cond = []
        params = {}
        # params['JobID'] = f"{data.ReelNo}"

        # if data.station:
        #     cond.append("station = :station")
        #     params['station'] = f"{data.station}"

        # if data.production_line:
        #     cond.append("pm =  :pm")
        #     params['pm'] = f"{data.production_line}"

        # if data.name:
        #     cond.append("mname = :mname")
        #     params['mname'] = f"{data.name}"
        try:
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
            category = "污點"
            if idx > len(result_df)*0.66:
                 category = "破孔"
            elif idx > len(result_df)*0.33:
                category = "開口笑"

            results.append({
                "ftaDtm": row.ftaDtm.strftime('%Y-%m-%d %H:%M:%S'),
                "jobKey": row.JobKey,
                "flawId": row.FlawId,
                "flawKey": row.FlawKey,
                "categoryName": category,
                "x": row.dCD,
                "y": row.dMD,
                "width": row.dWidth,
                "length": row.dLength,
                "area": row.dArea,
                }),

        # 關閉會話
        session.close()
        # 使用範例：
        png_files_base64 = results
        return png_files_base64


class wintrissReelBll:
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


class wintrissImageBll:
<<<<<<< HEAD
    def __init__(self, folders):
        trace_msg = f'{self.__class__.__name__}'
        logging.info(trace_msg)
        try:
            self.session = get_session("SRVMESDBA1_FlawInspection")
        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")
=======
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
    # def browse(self, data):
    #     mnameMapper = {"20": FTA_PM20_skyeye_reelDal(), "21": FTA_PM21_skyeye_reelDal()}
    #     dal = None
    #     if 'MachineName' in data and data['MachineName'] in mnameMapper:
    #         dal = mnameMapper[data['MachineName']]
    #     else:
    #         return None

    #     rst = dal.query(data)
    #     # ic(type(rst))
    #     for result in rst:
    #         # ic(type(result))
    #         # result['TagName'] = data['TagNameOrigin']
    #         pass
    #     return rst

    def ReadFromFileTest(self):
        def png_to_base64(directory, limit=10):
            try:
                file_count = 0
                results = []

                for root, dirs, files in os.walk(directory):
                    for idx, file in enumerate(files):
                        print(idx)
                        if file_count >= limit:
                            break
                        if file.lower().endswith('.png'):
                            file_path = os.path.join(root, file)
                            with open(file_path, 'rb') as f:
                                png_data = f.read()
                                base64_encoded = base64.b64encode(png_data).decode('utf-8')
                                results.append({'filename': file, 'base64': base64_encoded})
                            file_count += 1
                
                return results
            except Exception as e:
                msg = f'{self.__class__.__name__} |An error occurred: {str(e)}'
                ic(msg)
                return {'message': msg}, 500

        # 使用範例：
        # directory_path = r'\\10.10.3.12\d\DefectPic\生產三處\PM20\死紋\202406'
        # directory_path = r'D:\DefectPic\生產三處\PM20\死紋\202406'
        directory_path = r'C:\DefectPic\生產三處\PM20\死紋\202406'
        limit = 1000
        png_files_base64 = png_to_base64(directory_path, limit)
        return png_files_base64

    def ReadFromDbTest(self):
<<<<<<< HEAD
        session = self.Session()
=======
        # 建立 SQLAlchemy 引擎並連接到 SQL Server
        engine = create_engine("mssql+pyodbc://sa:yfyoljk%40@SRVMSDBA1.yfy.corp/AIMSFTAX?driver=ODBC+Driver+17+for+SQL+Server",)

        # 建立會話
        Session = sessionmaker(bind=engine)
        session = Session()
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
        limit = 400

        # 自定義 SQL 查詢語句
        sql_query = f"""
SELECT TOP ({limit}) flaw.pklFlawKey,flaw.klJobKey,img.iImage
FROM [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw
JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptimage] img on flaw.pklFlawKey=img.klFlawKey
where flaw.lFlawClassType=7 and flaw.SourceDB='WebDB4'
--order by flaw.pklFlawKey
        """

        # 執行 SQL 查詢
        result = session.execute(text(sql_query))
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
        for idx, row in enumerate(result):
            print(idx)
            blob_data = row.iImage
            base64_string = blob_to_base64(blob_data)

            if base64_string:
                results.append({'base64': base64_string})

        # 關閉會話
        session.close()
        # 使用範例：
        png_files_base64 = results
        return png_files_base64

    def ReadFromDb(self,data):
<<<<<<< HEAD
        session = self.Session()
=======
        # 建立 SQLAlchemy 引擎並連接到 SQL Server
        engine = create_engine("mssql+pyodbc://sa:yfyoljk%40@SRVMSDBA1.yfy.corp/FlawInspection?driver=ODBC+Driver+17+for+SQL+Server",)

        # 建立會話
        Session = sessionmaker(bind=engine)
        session = Session()
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

        # 自定義 SQL 查詢語句
        sql_query = f"""
DECLARE @queryStartTime datetime2 = DATEADD(year, -1, SYSDATETIME())
DECLARE @queryEndTime  datetime2 = SYSDATETIME()

SELECT @queryStartTime =DATEADD(hour, -2, Date),@queryEndTime =DATEADD(hour, 2, Date) FROM [FlawInspection].[dbo].[duptjobs] 
WHERE JobID= :JobID

SELECT 
    flaw.pklFlawKey FlawKey
    ,flaw.klJobKey JobKey
    ,flaw.lFlawId FlawId
    ,flaw.dCD
    ,flaw.dMD
    ,flaw.dWidth
    ,flaw.dLength
    ,flaw.dArea
    ,flaw.dtTime
    ,img.iImage
FROM [FlawInspection].[dbo].[duptjobs] job
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptflaw] flaw on job.klKey=flaw.klJobKey and job.SourceDB=flaw.SourceDB
LEFT JOIN [srvbahdba1].[FlawInspection].[dbo].[raw_duptimage] img on flaw.pklFlawKey=img.klFlawKey
WHERE JobID= :JobID
and job.Date between @queryStartTime and @queryEndTime
and flaw.dtTime between @queryStartTime and @queryEndTime
and img.flawtime between @queryStartTime and @queryEndTime
and flaw.dCD between :RangeXStart and :RangeXEnd
and flaw.dMD between :RangeYStart and :RangeYEnd
--order by flaw.pklFlawKey
        """
        # 執行 SQL 查詢
        cond = []
        params = {}
        params['JobID'] = f"{data.ReelNo}"
        params['RangeXStart'] = f"{data.RangeXStart}"
        params['RangeXEnd'] = f"{data.RangeXEnd}"
        params['RangeYStart'] = f"{data.RangeYStart}"
        params['RangeYEnd'] = f"{data.RangeYEnd}"
        # if data.station:
        #     cond.append("station = :station")
        #     params['station'] = f"{data.station}"

        # if data.production_line:
        #     cond.append("pm =  :pm")
        #     params['pm'] = f"{data.production_line}"

        # if data.name:
        #     cond.append("mname = :mname")
        #     params['mname'] = f"{data.name}"
        try:
                # result = session.execute(text(sql_query), params)
            result_df = pd.read_sql(text(sql_query), session.bind, params=params)
            # ic(result_df)
                # rows = result.fetchall()
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
                    "jobKey": row.JobKey,
                    "flawId": row.FlawId,
                    "flawKey": row.FlawKey,
                    "x": row.dCD,
                    "y": row.dMD,
                    "width": row.dWidth,
                    "length": row.dLength,
                    "area": row.dArea,
                    'image': f"data:image/png;base64,{base64_string}",
                    "rect": [
                        {
                        "defectName": f"破{idx}號",
                        "topLeftX": 10,
                        "topLeftY": 10,
                        "bottomRightX": 20,
                        "bottomRightY": 20
                        }
                    ]
                    }),

        # 關閉會話
        session.close()
        # 使用範例：
        png_files_base64 = results
        return png_files_base64
