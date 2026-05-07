#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Literal
import logging

from schemas.skyeye import FtaResponseDefect, FtaResponseDefectCategory, FtaResponseDefectImage,                               FtaResponseDefectImageRealtime,                               FtaResponseDefectJudge,                               FtaResponseDefectReelStatistics,                               FtaResponseDefectReelStatisticsRealtime,                               FtaResponseDefectReelRealtime,                               FtaResponseDefectRealtime,                               FtaResponseRuleAlarm

from schemas.skyeye import DefectJudgeRequest

from dependencies.auth import get_current_user
from services.skyeye import SkyeyeService
from fta_response import FtaResult

from core.security import verify_jwt

router = APIRouter(
    prefix="/skyeye",
    tags=["SkyEye"],
    dependencies=[Depends(verify_jwt)]
)

logger = logging.getLogger("MES_API")

@router.get("/defect", response_model=FtaResponseDefect,
    summary=" ")
def get_defect(
    MachineName: str = Query(..., description="機台名稱", example="20"),
    ReelNo: str = Query(...,description="紙捲號碼", example="T6030301"),
    SkyeyeCategoryCsv: str = Query(None,description="瑕疵類別Csv"),
    CategoryCsv: str = Query(None,description="瑕疵類別Csv"),
    ShowLarge: bool = Query(None,description="秀Wintriss大瑕疵", example="true, false"),
    ShowMedium: bool = Query(None,description="秀Wintriss中瑕疵", example="true, false"),
    ShowSmall: bool = Query(None,description="秀Wintriss小瑕疵", example="true, false"),
    ExportFormat: str = Query(None,description="輸出類別// json(default), tablejson"),
    user=Depends(get_current_user)
):
    """
    查詢機台指定紙捲號碼的瑕疵
    
輸出 data.Content

```json
[
    {
        "uuid":"",
        "jobKey":"",
        "flawId":"",
        "flawKey":"",
        "ftaDtm": "時間點",
        "skyeyeCategory":"skyeye瑕疵類別",
        "categoryName":"瑕疵名稱",
        "x":"x座標",
        "y":"y座標",
        "width":"寬(m)",
        "length":"長(m)",
        "area":"面積(m^2)",
    }
]
    """
    try:
        # 組成 dict 傳給 Service（不要用 SimpleNamespace）
        data  = {
            "MachineName": MachineName,
            "ReelNo": ReelNo,
            "SkyeyeCategoryCsv": SkyeyeCategoryCsv,
            "CategoryCsv": CategoryCsv,
            "ShowLarge": ShowLarge,
            "ShowMedium": ShowMedium,
            "ShowSmall": ShowSmall,
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }

        logger.info(
            "Get defect",
            extra={"User": user["FTAId"], "ReelNo": ReelNo}
        )

        content, execution_time = SkyeyeService.get_defect(data)
        
        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()

    except Exception as e:
        logger.exception(f"get_defect failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()
    
@router.get("/defect/category",
    summary=" ",
    description="""
查詢機台瑕疵分類清單  

輸出 data.Content

```json
[
  {
    "primaryCategory": "瑕疵主類",
    "defectName": "瑕疵名稱",
    "order": "排列順序",
    "isEnabled": "是否預設",
    "symbol":"圖形", //circle, rect, roundRect, triangle, diamond, pin, arrow, none
    "color":"顏色", //#RRGGBBAA, #RRGGBB, colorname
  }
]
""",
response_model=FtaResponseDefectCategory
)
def get_defect_category(
    MachineName: str = Query(..., description="機台名稱", example="20"),
    ExportFormat: str = Query(None, description="輸出類別 // json(default), tablejson"),
    user=Depends(get_current_user)
):
    try:
        data = {
            "MachineName": MachineName,
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }

        logger.info(
            "Get defect category",
            extra={"MachineName": MachineName, "User": user["FTAId"]}
        )    

        content, execution_time = SkyeyeService.get_defect_category(data)
    
        if ExportFormat != "tablejson":
            # 將 True/False 轉成 1/0
            for item in content:
                item['isEnabled'] = int(item['isEnabled'])    

        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()

    except Exception as e:
        logger.exception(f"get_defect_category failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()
    
    
@router.get("/defect/image", response_model=FtaResponseDefectImage,
    summary=" ")
def get_defect_image(
    MachineName: str = Query(..., description="機台名稱"),
    ReelNo: str = Query(..., description="紙捲號碼"),
    CategoryCsv: str = Query(None, description="瑕疵類別Csv"),
    ShowLarge: bool = Query(None, description="秀Wintriss大瑕疵", example="true, false"),
    ShowMedium: bool = Query(None, description="秀Wintriss中瑕疵", example="true, false"),
    ShowSmall: bool = Query(None, description="秀Wintriss小瑕疵", example="true, false"),
    RangeXStart: float = Query(None, description="X區間起"),
    RangeXEnd: float = Query(None, description="X區間迄"),
    RangeYStart: float = Query(None, description="Y區間起"),
    RangeYEnd: float = Query(None, description="Y區間迄"),
    ExportFormat: str = Query(None, description="輸出類別// json(default), tablejson"),
    user=Depends(get_current_user)
):
    """
    查詢瑕疵影像及識別資訊
    
輸出 data.Content

```json
[
    {
        "ftaDtm": "時間點",
        "fileName": "檔名"
        "jobKey":"",
        "flawId":,
        "flawKey":,
        "x":"x座標",
        "y":"y座標",
        "width":"寬(m)",
        "length":"長(m)",
        "area":"面積(m^2)",
        "rect":{
            "wintrissDefectName": "Wintriss瑕疵名稱",
            "categoryName": "瑕疵名稱",
            "topLeftX":"左上點X座標",
            "topLeftY":"左上點Y座標",
            "bottomRightX":"右下點X座標",
            "bottomRightY":"右下點Y座標",
        }
    }
]
    """
    try:
        data = {
            "MachineName": MachineName,
            "ReelNo": ReelNo,
            "CategoryCsv": CategoryCsv,
            "ShowLarge": ShowLarge,
            "ShowMedium": ShowMedium,
            "ShowSmall": ShowSmall,
            "RangeXStart": RangeXStart,
            "RangeXEnd": RangeXEnd,
            "RangeYStart": RangeYStart,
            "RangeYEnd": RangeYEnd,
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }

        logger.info(f"Get defect_image for user {user['FTAId']}")
        
        content, execution_time = SkyeyeService.get_defect_image(data)
        
        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
    except Exception as e:
        logger.exception(f"get_defect_image failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()

# @router.get("/defect/image/uuid",response_model=FtaResponseDefectImage,
#     summary=" "
# )
# def get_defect_image_by_uuid(
#     MachineName: str = Query(..., description="機台名稱"),
#     ReelNo: str = Query(..., description="紙捲號碼"),
#     Uuid: List[str] = Query(..., description="UUID 陣列，可多次指定 ?Uuid=abc&Uuid=def"),
#     ExportFormat: Literal["json", "tablejson"] = Query(None, description="輸出格式 json | tablejson"),
#     user=Depends(get_current_user)
# ):
#     """
#     查詢瑕疵影像及識別資訊
    
# 輸出 data.Content

# ```json
# [
#     {
#         "ftaDtm": "時間點",
#         "fileName": "檔名"
#         "jobKey":"",
#         "flawId":,
#         "flawKey":,
#         "x":"x座標",
#         "y":"y座標",
#         "width":"寬(m)",
#         "length":"長(m)",
#         "area":"面積(m^2)",
#         "rect":{
#             "wintrissDefectName": "Wintriss瑕疵名稱",
#             "categoryName": "瑕疵名稱",
#             "topLeftX":"左上點X座標",
#             "topLeftY":"左上點Y座標",
#             "bottomRightX":"右下點X座標",
#             "bottomRightY":"右下點Y座標",
#         }
#     }
# ]
#     """

#     try:
#         data = {
#             "MachineName": MachineName,
#             "ReelNo": ReelNo,
#             "Uuid": Uuid,          # FastAPI 會自動解析 multi query 成 list
#             "ExportFormat": ExportFormat,
#             "current_login_id": user["FTAId"]
#         }

#         logger.info(f"Get defect_image_by_uuid for user {user['FTAId']}")
        
#         content, execution_time = SkyeyeService.get_defect_image_by_uuid(data)
        
#         if ExportFormat == "tablejson":
#             # tablejson 直接回傳 JSONResponse，不走 Pydantic
#             return JSONResponse(
#                 content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
#             )

#         # json 模式，走 Pydantic 驗證
#         return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
#     except Exception as e:
#         logger.exception(f"get_defect_image_by_uuid failed: {e}")
#         return FtaResult([], 0, False, export_format="json").to_dict()        

    
@router.get("/defect/image_realtime",response_model=FtaResponseDefectImageRealtime,
    summary=" "
)
def get_defect_image_realtime(
    MachineName: str = Query(..., description="機台名稱"),
    CategoryCsv: str = Query(None, description="瑕疵類別Csv"),
    ShowLarge: bool = Query(None, description="秀Wintriss大瑕疵", example="true, false"),
    ShowMedium: bool = Query(None, description="秀Wintriss中瑕疵", example="true, false"),
    ShowSmall: bool = Query(None, description="秀Wintriss小瑕疵", example="true, false"),
    RangeXStart: float = Query(None, description="X區間起"),
    RangeXEnd: float = Query(None, description="X區間迄"),
    RangeYStart: float = Query(None, description="Y區間起"),
    RangeYEnd: float = Query(None, description="Y區間迄"),
    ExportFormat: str = Query(None, description="輸出類別// json(default), tablejson"),
    user=Depends(get_current_user)    
):
    """
    查詢瑕疵影像及識別資訊
    
輸出 data.Content

```json
[
    {
        "ftaDtm": "時間點",
        "fileName": "檔名"
        "jobKey":"",
        "flawId":,
        "flawKey":,
        "x":"x座標",
        "y":"y座標",
        "width":"寬(m)",
        "length":"長(m)",
        "area":"面積(m^2)",
        "rect":{
            "wintrissDefectName": "Wintriss瑕疵名稱",
            "categoryName": "瑕疵名稱",
            "topLeftX":"左上點X座標",
            "topLeftY":"左上點Y座標",
            "bottomRightX":"右下點X座標",
            "bottomRightY":"右下點Y座標",
        }
    }
]
    """

    try:
        data = {
            "MachineName": MachineName,
            "CategoryCsv": CategoryCsv,
            "ShowLarge": ShowLarge,
            "ShowMedium": ShowMedium,
            "ShowSmall": ShowSmall,
            "RangeXStart": RangeXStart,
            "RangeXEnd": RangeXEnd,
            "RangeYStart": RangeYStart,
            "RangeYEnd": RangeYEnd,            
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }

        logger.info(f"Get defect_image_realtime for user {user['FTAId']}")
    
        content, execution_time = SkyeyeService.get_defect_image_realtime(data)
        
        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
    except Exception as e:
        logger.exception(f"get_defect_image_realtime failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()       
    

@router.post(
    "/defect/judge",
    response_model=FtaResponseDefectJudge,
    summary=" "
)
def add_defect_judge(
    MachineName: str = Query(..., description="機台名稱"),
    Image : str = Query(..., description="影像資料"),
    user=Depends(get_current_user)
):
    """
    判定圖片結果
    """

    try:
        data = {
            "MachineName": MachineName,
            "Image": Image,
            "current_login_id": user["FTAId"]
        }

        logger.info(f"Defect judge by user {user['FTAId']}")
    
        content, execution_time = SkyeyeService.add_defect_judge(data)

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
    except Exception as e:
        logger.exception(f"add_defect_judge failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()         
    
@router.get("/defect/reel_statistics", response_model=FtaResponseDefectReelStatistics,
    summary=" ")
def get_defect_reel_statistics(
    MachineName: str = Query(..., description="機台名稱"),
    ReelNoCsv: str = Query(..., description="紙捲號碼CSV"),
    CategoryCsv: str = Query(None, description="瑕疵分類 CSV"),
    ExportFormat: str = Query(None, description="輸出類別// json(default), tablejson"),
    user=Depends(get_current_user)
):
    """
    查詢機台指定紙捲號碼的瑕疵統計值
    
輸出 data.Content

```json
[
    {
        "relno": "紙捲號碼",
        "污點":int,
        "破孔":int,
        ...
        ...
    }
]
    """
    try:
        data = {
            "MachineName": MachineName,
            "ReelNoCsv": ReelNoCsv,
            "CategoryCsv": CategoryCsv,
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }

        logger.info(f"Get defect_reel_statistics for user {user['FTAId']}")
        content, execution_time = SkyeyeService.get_defect_reel_statistics(data)
        
        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
    except Exception as e:
        logger.exception(f"get_defect_reel_statistics failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()        
    
# @router.get("/defect/reel_statistics_realtime", response_model=FtaResponseDefectReelStatisticsRealtime,
#     summary=" ")
# def get_defect_reel_statistics_realtime(
#     MachineName: str = Query(..., description="機台名稱"),
#     CategoryCsv: str = Query(None, description="瑕疵類別Csv"),
#     ExportFormat: str = Query(None, description="輸出類別// json(default), tablejson"),
#     user=Depends(get_current_user)
# ):
#     """
#     查詢機台指定紙捲號碼的即時瑕疵統計
    
# 輸出 data.Content

# ```json
# [
#     {
#         "relno": "紙捲號碼",
#         "污點":int,
#         "破孔":int,
#         ...
#         ...
#     }
# ]
#     """
#     try:
#         data = {
#             "MachineName": MachineName,
#             "CategoryCsv": CategoryCsv,
#             "ExportFormat": ExportFormat,
#             "current_login_id": user["FTAId"]
#         }

#         logger.info(f"Get defect_reel_statistics_realtime for user {user['FTAId']}")
#         content, execution_time = SkyeyeService.get_defect_reel_realtime(data)
       
#         if ExportFormat == "tablejson":
#             # tablejson 直接回傳 JSONResponse，不走 Pydantic
#             return JSONResponse(
#                 content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
#             )

#         # json 模式，走 Pydantic 驗證
#         return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
#     except Exception as e:
#         logger.exception(f"get_defect_reel_statistics_realtime failed: {e}")
#         return FtaResult([], 0, False, export_format="json").to_dict()      

@router.get("/defect_realtime", response_model=FtaResponseDefectRealtime,
    summary=" ")
def get_defect_realtime(
    MachineName: str = Query(..., description="機台名稱",example=20),
    CategoryCsv: str = Query(None, description="瑕疵類別Csv"),
    ShowLarge: bool = Query(None, description="秀Wintriss大瑕疵", example="true, false"),
    ShowMedium: bool = Query(None, description="秀Wintriss中瑕疵", example="true, false"),
    ShowSmall: bool = Query(None, description="秀Wintriss小瑕疵", example="true, false"),
    ExportFormat: str = Query(None, description="輸出類別// json(default), tablejson"),
    user=Depends(get_current_user)
):
    """
    查詢機台即時的瑕疵
    
輸出 data.Content

```json
[
    {
        "uuid":"",
        "jobKey":"",
        "flawId":"",
        "flawKey":"",
        "ftaDtm": "時間點",
        "skyeyeCategory":"skyeye瑕疵類別",
        "categoryName":"瑕疵名稱",
        "x":"x座標",
        "y":"y座標",
        "width":"寬(m)",
        "length":"長(m)",
        "area":"面積(m^2)",
    }
]
    """
    try:
        data = {
            "MachineName": MachineName,
            "CategoryCsv": CategoryCsv,
            "ShowLarge": ShowLarge,
            "ShowMedium": ShowMedium,
            "ShowSmall": ShowSmall,
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }

        logger.info(f"Get defect_realtime for user {user['FTAId']}")

        content, execution_time = SkyeyeService.get_defect_realtime(data)
       
        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
    except Exception as e:
        logger.exception(f"get_defect_realtime failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()          
    
    
    
@router.get(
    "/rulealarm",
    response_model=FtaResponseRuleAlarm,
    summary=" "
)
def get_rule_alarm(
    MachineName: str = Query(..., description="機台名稱",example=20),
    ExportFormat: str = Query(None, description="輸出格式 json | tablejson"),
    user=Depends(get_current_user)
):
    """
    查詢機台瑕疵分類清單
    
輸出 data.Content

```json
[
    {
        "primaryCategory": "瑕疵主類",
        "defectName": "瑕疵名稱",
        "order":"排列順序",
        "isEnabled":"是否預設",
        "symbol":"圖形", //circle, rect, roundRect, triangle, diamond, pin, arrow, none
        "color":"顏色", //#RRGGBBAA, #RRGGBB, colorname
    }
]
    """

    try:
        data = {
            "ExportFormat": ExportFormat,
            "current_login_id": user["FTAId"]
        }

        logger.info(f"Get rulealarm by user {user['FTAId']}")
    
        content, execution_time = SkyeyeService.get_rule_alarm(data)
       
        if ExportFormat == "tablejson":
            # tablejson 直接回傳 JSONResponse，不走 Pydantic
            return JSONResponse(
                content=FtaResult(content, execution_time, True, export_format="tablejson").to_dict()
            )

        # json 模式，走 Pydantic 驗證
        return FtaResult(content, execution_time, True, export_format="json").to_dict()
        
    except Exception as e:
        logger.exception(f"get_rule_alarm failed: {e}")
        return FtaResult([], 0, False, export_format="json").to_dict()         

