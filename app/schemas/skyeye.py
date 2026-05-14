#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from fastapi import Query

# === Defect ===   
class DefectItem(BaseModel):
    ftaDtm: str = Field(..., description="時間點")
    jobKey: int = Field(..., description="JobKey")
    flawId: Optional[int] = Field(..., description="Flaw ID")
    flawKey: Optional[int] = Field(..., description="Flaw Key")
    skyeyeCategory: str = Field(None, description="瑕疵分類名稱")
    categoryName: str = Field(None, description="瑕疵名稱")
    x: float = Field(..., description="X座標")
    y: float = Field(..., description="Y座標")
    width: float = Field(..., description="寬度(m)")
    length: float = Field(..., description="長度(m)")
    area: float = Field(..., description="面積(m^2)")
    uuid: str = Field(..., description="唯一碼")
    isAlarm: bool = Field(..., description="是否警示")

class DefectResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")  # 放第一個欄位
    Content: List[DefectItem] = Field(..., description="資料內容")
    ExecutionTime: str
    ExecutionDto: str
    Length: int

class FtaResponseDefect(BaseModel):
    data: DefectResponse
    success: bool
    status_code: int
        
# === DefectCategory ===   
class DefectCategoryItem(BaseModel):
    primaryCategory: str = Field(..., description="瑕疵主類")
    category: str = Field(..., description="瑕疵名稱")
    isEnabled: int = Field(..., description="是否預設")
    order: int = Field(..., description="排列順序")
    symbol: str = Field(..., description="圖形，可選值: circle, rect, roundRect, triangle, diamond, pin, arrow, none")
    color: str = Field(..., description="顏色，可接受 #RRGGBBAA, #RRGGBB 或 colorname")

class DefectCategoryResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")  # 放第一個欄位
    Content: List[DefectCategoryItem] = Field(..., description="資料內容")
    ExecutionTime: str
    ExecutionDto: str
    Length: int

class FtaResponseDefectCategory(BaseModel):
    data: DefectCategoryResponse
    success: bool
    status_code: int      
        
# === DefectImageItem ===        
class DefectImageRect(BaseModel):
    wintrissDefectName: str = Field(..., description="Wintriss瑕疵名稱")
    skyeyeCategory: str = Field(..., description="瑕疵分類名稱")
    defectName: str = Field(..., description="瑕疵名稱")
    topLeftX: float = Field(..., description="左上X座標")
    topLeftY: float = Field(..., description="左上Y座標")
    bottomRightX: float = Field(..., description="右下X座標")
    bottomRightY: float = Field(..., description="右下Y座標")

class DefectImageItem(BaseModel):
    ftaDtm: str = Field(..., description="時間點")
    fileName: str = Field(..., description="檔名")
    jobKey: int = Field("", description="JobKey")
    flawKey: Optional[int] = Field(None, description="Flaw Key")
    flawId: Optional[int] = Field(None, description="Flaw ID")
    x: float = Field(..., description="X座標")
    y: float = Field(..., description="Y座標")
    image: str = Field(..., description="影像字元")
    rect: List[DefectImageRect] = Field(..., description="瑕疵方框資訊")
    uuid: str = Field(..., description="唯一碼")
    reconfirmOk: Optional[int] = Field(None, description="唯一碼")
    reconfirmCategory: Optional[str] = Field(None, description="唯一碼")
    reconfirmDefect: Optional[str] = Field(None, description="唯一碼")
    reconfirmComment: Optional[str] = Field(None, description="唯一碼")    
    width: float = Field(..., description="寬度(m)")
    length: float = Field(..., description="長度(m)")
    area: float = Field(..., description="面積(m^2)")
    action: str = Field("", description="瑕疵處理方法")  # 放第一個欄位

class DefectImageResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")
    Content: List[DefectImageItem] = Field(..., description="資料內容")
    ExecutionTime: str = Field(..., description="執行時間 (ms)")
    ExecutionDto: str
    Length: int        
    

class FtaResponseDefectImage(BaseModel):
    data: DefectImageResponse
    success: bool
    status_code: int        
        
# === DefectImageRealtimeItem ===        
class DefectImageRealtimeRect(BaseModel):
    wintrissDefectName: str = Field(..., description="Wintriss瑕疵名稱")
    skyeyeCategory: str = Field(..., description="瑕疵分類名稱")
    defectName: str = Field(..., description="瑕疵名稱")
    topLeftX: float = Field(..., description="左上X座標")
    topLeftY: float = Field(..., description="左上Y座標")
    bottomRightX: float = Field(..., description="右下X座標")
    bottomRightY: float = Field(..., description="右下Y座標")

class DefectImageRealtimeItem(BaseModel):
    ftaDtm: str = Field(..., description="時間點")
    fileName: str = Field(..., description="檔名")
    jobKey: int = Field("", description="JobKey")
    flawKey: Optional[int] = Field(None, description="Flaw Key")
    flawId: Optional[int] = Field(None, description="Flaw ID")
    x: float = Field(..., description="X座標")
    y: float = Field(..., description="Y座標")
    image: str = Field(..., description="影像字元")
    rect: List[DefectImageRealtimeRect] = Field(..., description="瑕疵方框資訊")
    uuid: str = Field(..., description="唯一碼")
    reconfirmOk: Optional[int] = Field(None, description="唯一碼")
    reconfirmCategory: Optional[str] = Field(None, description="唯一碼")
    reconfirmDefect: Optional[str] = Field(None, description="唯一碼")
    reconfirmComment: Optional[str] = Field(None, description="唯一碼")    
    width: float = Field(..., description="寬度(m)")
    length: float = Field(..., description="長度(m)")
    area: float = Field(..., description="面積(m^2)")
    action: str = Field("", description="瑕疵處理方法")  # 放第一個欄位

class DefectImageRealtimeResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")
    Content: List[DefectImageRealtimeItem] = Field(..., description="資料內容")
    ExecutionTime: str = Field(..., description="執行時間 (ms)")
    ExecutionDto: str = Field(..., description="目前時間")
    Length: int

class FtaResponseDefectImageRealtime(BaseModel):
    data: DefectImageRealtimeResponse
    success: bool
    status_code: int  
        
# === Judge ===
class DefectJudgeRequest(BaseModel):
    MachineName: str = Field(..., description="機台名稱", example="20")
    Image: Dict[str, Any] = Field(..., description="影像資料")

class DefectJudgeResponse(BaseModel):
    Action: str = ""
    Content: Any
    ExecutionTime: str = Field(..., description="執行時間 (ms)")
    ExecutionDto: str = Field(..., description="目前時間")
    Length: int
    
class FtaResponseDefectJudge(BaseModel):
    data: DefectJudgeResponse
    success: bool
    status_code: int     
        
# === DefectReelStatisticsItem === 
class DefectReelStatisticsItem(BaseModel):
    relno: str = Field(..., description="紙捲號碼")
    model_config = ConfigDict(extra="allow")

class DefectReelStatisticsResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")
    Content: List[DefectReelStatisticsItem] = Field(..., description="資料內容")
    ExecutionTime: str = Field(..., description="執行時間 (ms)")
    ExecutionDto: str = Field(..., description="目前時間")

class FtaResponseDefectReelStatistics(BaseModel):
    data: DefectReelStatisticsResponse
    success: bool
    status_code: int       
        
# === DefectReelStatisticsRealtimeItem === 
class DefectReelStatisticsRealtimeItem(BaseModel):
    relno: str = Field(..., description="紙捲號碼")
    model_config = ConfigDict(extra="allow")

class DefectReelStatisticsRealtimeResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")
    Content: List[DefectReelStatisticsItem] = Field(..., description="資料內容")
    ExecutionTime: str = Field(..., description="執行時間 (ms)")
    ExecutionDto: str = Field(..., description="目前時間")
    Length: int

class FtaResponseDefectReelStatisticsRealtime(BaseModel):
    data: DefectReelStatisticsResponse
    success: bool
    status_code: int            
        
# === DefectReelRealtimeItem ===
class DefectReelRealtimeItem(BaseModel):
    ftaDtm: str = Field(..., description="時間點")
    jobKey: int = Field("", description="JobKey")
    flawId: Optional[int] = Field(None, description="Flaw ID")
    flawKey: Optional[int] = Field(None, description="Flaw Key")
    skyeyeCategory: str = Field(..., description="瑕疵分類名稱")
    categoryName: str = Field(..., description="瑕疵名稱")        
    x: float = Field(..., description="X座標")
    y: float = Field(..., description="Y座標")
    width: float = Field(..., description="寬度(m)")
    length: float = Field(..., description="長度(m)")
    area: float = Field(..., description="面積(m^2)")
    uuid: str = Field(..., description="唯一碼")

class DefectReelRealtimeResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")
    Content: List[DefectReelRealtimeItem] = Field(..., description="資料內容")
    ExecutionTime: str = Field(..., description="執行時間 (ms)")
    ExecutionDto: str = Field(..., description="目前時間")
    Length: int

class FtaResponseDefectReelRealtime(BaseModel):
    data: DefectReelRealtimeResponse
    success: bool
    status_code: int        

# === DefectRealtimeItem === 
class DefectRealtimeItem(BaseModel):
    ftaDtm: str = Field(..., description="時間點")
    jobKey: int = Field("", description="JobKey")
    flawId: Optional[int] = Field(None, description="Flaw ID")
    flawKey: Optional[int] = Field(None, description="Flaw Key")
    skyeyeCategory: str = Field(..., description="瑕疵分類名稱")
    categoryName: str = Field(..., description="瑕疵名稱")        
    x: float = Field(..., description="X座標")
    y: float = Field(..., description="Y座標")
    width: float = Field(..., description="寬度(m)")
    length: float = Field(..., description="長度(m)")
    area: float = Field(..., description="面積(m^2)")
    uuid: str = Field(..., description="唯一碼")
        

class DefectRealtimeResponse(BaseModel):
    Action: str = ""
    Content: List[DefectRealtimeItem] = Field(..., description="資料內容")
    ExecutionTime: str
    ExecutionDto: str = Field(..., description="目前時間")
    Length: int

class FtaResponseDefectRealtime(BaseModel):
    data: DefectRealtimeResponse
    success: bool
    status_code: int
        
# === RuleAlarm ===
class RuleAlarmItem(BaseModel):
    primaryCategory: str = Field(..., description="瑕疵主類")
    category: str = Field(..., description="瑕疵名稱")
    isEnabled: int = Field(..., description="是否預設")
    order: int = Field(..., description="排列順序")
    symbol: str = Field(..., description="圖形")
    color: str = Field(..., description="顏色")


class RuleAlarmResponse(BaseModel):
    Action: str = ""
    Content: List[RuleAlarmItem]
    ExecutionTime: str
    ExecutionDto: str = Field(..., description="目前時間")
    Length: int


class FtaResponseRuleAlarm(BaseModel):
    data: RuleAlarmResponse
    success: bool
    status_code: int

