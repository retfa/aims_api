#!/usr/bin/env python
# coding: utf-8



from pydantic import BaseModel, Field
from typing import List,Optional
from datetime import datetime

class MESBaseQuery(BaseModel):
    stime: Optional[str]
    etime: Optional[str]
    mname: Optional[str]  
        
class MESAmreelGroupByPtimeQuery(BaseModel):
    stime: Optional[str]
    etime: Optional[str]
    mname: Optional[str]
    MachineCode: Optional[str]  
        
class AmpaperCategoryQuery(BaseModel):
    date_from: Optional[str]
    date_to: Optional[str]
    machine_name: Optional[str]
    mode: Optional[str]
    year_month_from: Optional[str]

class DefectReportQuery(BaseModel):
    yearMonthFrom: Optional[str]
    yearMonthTo: Optional[str]
    machineName: Optional[str]

class YieldDailyReportQuery(BaseModel):
    date_from: Optional[str]
    date_to: Optional[str]
    machine_name: Optional[str]
    category: Optional[str]

class RelnoProductionHistoryQuery(BaseModel):
    relno: Optional[str]        
        
class VehiclesPatchBody(BaseModel):
    cp_wt:  Optional[float] = None
    fac_wt: Optional[float] = None
    pay_wt: Optional[float] = None
    # 日後擴充加這裡
    # note:     Optional[str] = None
    # order_no: Optional[str] = None        
        
class WeighTicketKey(BaseModel):
    station_name: str
    weigh_date: str
    serial_no: int
        
class ScaleWeighPatchBody(BaseModel):
    vehicle_schedule_id: int
    link_ids: List[WeighTicketKey] = []
    unlink_ids: List[WeighTicketKey] = []

    class Config:
        schema_extra = {
            "example": {
              "vehicle_schedule_id": 5,
              "link_ids": [
                {
                  "station_name": "三號地磅",
                  "weigh_date": "2026-05-01",
                  "serial_no": 4
                }
              ],
              "unlink_ids": [
                {
                  "station_name": "六號地磅",
                  "weigh_date": "2026-05-01",
                  "serial_no": 1
                }
              ]
            }
        }


class PostBlanket(BaseModel):
    mname: str = Field(..., description="機台名稱", example="20")
    Change_Date: datetime = Field(..., description="更換日期", example="2024-01-01T00:00:00")
    Equipment_Code: str = Field(..., description="換毯資料", example="A")


class DeleteBlanket(BaseModel):
    mname: str = Field(..., description="機台名稱", example="20")
    Change_Date: datetime = Field(..., description="更換日期", example="2024-01-01T00:00:00")
    Equipment_Code: str = Field(..., description="換毯資料", example="A")


class PutBlanket(BaseModel):
    mname: str = Field(..., description="機台名稱", example="20")
    Change_Date: datetime = Field(..., description="更換日期", example="2024-01-01T00:00:00")
    Equipment_Code: str = Field(..., description="換毯資料", example="A")
    New_Change_Date: datetime = Field(..., description="新更換日期", example="2024-01-02T00:00:00")
    New_Equipment_Code: str = Field(..., description="新換毯資料", example="A")


