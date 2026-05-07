#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel, Field
from typing import Optional, List

# 主表
class OutputListMModel(BaseModel):
    Sn: Optional[int] = None
    HistorianPK: Optional[str] = None
    Name: Optional[str] = None
    Cname: str = Field(..., description="中文名稱，不可為空")
    Description: Optional[str] = None
    Code: Optional[str] = None
    System: Optional[str] = None
    Dept_ID: Optional[str] = None
    MachineCode: Optional[str] = None
    Area: Optional[str] = None
    AreaSequence: Optional[int] = None
    Subarea: Optional[str] = None
    SubreaSequence: Optional[int] = None
    Category: Optional[str] = None
    IsEnabled: Optional[bool] = True
    PublishedDate: Optional[str] = None
    CreatedBy: Optional[int] = None
    CreatedDate: Optional[str] = None
    ModifiedBy: Optional[int] = None
    ModifiedDate: Optional[str] = None
    IsDeprecated: Optional[bool] = False

# 明細表
class OutputListMesModel(BaseModel):
    MasterSn: Optional[int] = None
    Server: Optional[str] = None
    Database: Optional[str] = None
    Schema: Optional[str] = None
    Table: Optional[str] = None
    Column: Optional[str] = None
    RowTagName: Optional[str] = None
    QueryMode: Optional[str] = None
    DataType: Optional[str] = None
    Description: Optional[str] = None
    Length: Optional[int] = None
    IsIndex: Optional[bool] = False
    IsAllowNull: Optional[bool] = True
    DefaultValue: Optional[str] = None
    CreatedBy: Optional[int] = None
    CreatedDate: Optional[str] = None
    ModifiedBy: Optional[int] = None
    ModifiedDate: Optional[str] = None

class OutputListWspGalaxyModel(BaseModel):
    MasterSn: Optional[int] = None
    Instance: Optional[str] = None
    Attribute: Optional[str] = None
    IoReference: Optional[str] = None
    DataType: Optional[str] = None
    HhAlarm: Optional[float] = None
    HAlarm: Optional[float] = None
    LAlarm: Optional[float] = None
    LLAlarm: Optional[float] = None
    Historian: Optional[str] = None
    MesScript: Optional[str] = None
    IntegralCoefficient: Optional[float] = None
    AccessLevel: Optional[int] = None
    CreatedBy: Optional[int] = None
    CreatedDate: Optional[str] = None
    ModifiedBy: Optional[int] = None
    ModifiedDate: Optional[str] = None

class OutputListWspDeviceModel(BaseModel):
    MasterSn: Optional[int] = None
    EU_RAW: Optional[float] = None
    ItemReference: Optional[str] = None
    ScanTime: Optional[int] = None
    Protocol: Optional[str] = None
    DataSourceIp: Optional[str] = None
    CreatedBy: Optional[int] = None
    CreatedDate: Optional[str] = None
    ModifiedBy: Optional[int] = None
    ModifiedDate: Optional[str] = None

class OutputListEmdModel(BaseModel):
    MasterSn: Optional[int] = None
    IoList: Optional[str] = None
    ItemReference: Optional[str] = None
    DataType: Optional[str] = None
    Unit: Optional[str] = None
    RangeMinimum: Optional[float] = None
    RangeMaximum: Optional[float] = None
    CreatedBy: Optional[int] = None
    CreatedDate: Optional[str] = None
    ModifiedBy: Optional[int] = None
    ModifiedDate: Optional[str] = None

# POST model
class OutputListPostModel(BaseModel):
    m: OutputListMModel
    mes: Optional[List[OutputListMesModel]] = []
    wspgalaxy: Optional[List[OutputListWspGalaxyModel]] = []
    wspdevice: Optional[List[OutputListWspDeviceModel]] = []
    emd: Optional[List[OutputListEmdModel]] = []

