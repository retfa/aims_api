from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class GetEnergyParams(BaseModel):
    date: str = Field(..., description="查詢日期 (格式: yyyy-mm-dd)", example="2026-04-18")

class PatchEnergyBody(BaseModel):
    sdate: datetime = Field(..., description="要修改的日期時間 (定位主鍵)", example="2026-04-18T07:02:00")

    # 所有可修改的能量欄位，均設為 Optional。
    c_8001000001: Optional[float] = Field(None, alias="8001000001", description="CFBC運轉時間(HR)")
    c_8003001001: Optional[float] = Field(None, alias="8003001001", description="煤炭量 COAL CONSUMPTION(m3)")
    c_8003001002: Optional[float] = Field(None, alias="8003001002", description="汙泥量")
    c_8003001003: Optional[float] = Field(None, alias="8003001003", description="石灰石量 LIMESTONE CONSUMPTION(m3)")
    c_8003001004: Optional[float] = Field(None, alias="8003001004", description="礦砂量 SAND CONSUMPTION(kg)")
    c_8003001005: Optional[float] = Field(None, alias="8003001005", description="重油量(CFBC)(KL)")
    c_8003001006: Optional[float] = Field(None, alias="8003001006", description="重油量(Oil Boiler)(KL)")
    c_8003001007: Optional[float] = Field(None, alias="8003001007", description="柴油量 DIESEL OIL CONSUMPTION(kg)")
    
    c_8003002001: Optional[float] = Field(None, alias="8003002001", description="清水量(T) fresh water consumption(m3)")
    c_8003002002: Optional[float] = Field(None, alias="8003002002", description="純水量(T) pure water consumption(m3)")
    c_8003002003: Optional[float] = Field(None, alias="8003002003", description="冷凝水量 condenser w consumption(m3)")
    
    c_8003004001: Optional[float] = Field(None, alias="8003004001", description="CFBC用汽量 CFBC USED STEAM")
    c_8003004002: Optional[float] = Field(None, alias="8003004002", description="鍋爐島用電量 CFBC USED POWER (KWh)")
    c_8003004003: Optional[float] = Field(None, alias="8003004003", description="汽機用汽量 TURBINE USED STEAM (T)")
    
    c_8004001001: Optional[float] = Field(None, alias="8004001001", description="CFBC產汽量 STEAM PRODUCTION(ton)")
    c_8004002001: Optional[float] = Field(None, alias="8004002001", description="CFBC產電量 POWER PRODUCTION(KWh)")
    
    c_8004004001D: Optional[float] = Field(None, alias="8004004001D", description="PM21用汽量 PM21-HOOD STEAM CONSUMPION")
    c_8004004002D: Optional[float] = Field(None, alias="8004004002D", description="PM20用汽量 PM20 STEAM CONSUMPION")
    c_8004004009D: Optional[float] = Field(None, alias="8004004009D", description="PM21 6D用汽量 PM21-HOOD STEAM CONSUMPION")
    c_8004004003D: Optional[float] = Field(None, alias="8004004003D", description="PM19用汽量 PM19 STEAM CONSUMPION")
    c_8004004004D: Optional[float] = Field(None, alias="8004004004D", description="PM18用汽量 PM18 STEAM CONSUMPION")
    
    c_8004004005D: Optional[float] = Field(None, alias="8004004005D", description="#1 OMC用汽量 OMC1 STEAM CONSUMPION")
    c_8004004006D: Optional[float] = Field(None, alias="8004004006D", description="#7 OMC7 用汽量 OMC7 STEAM CONSUMPION")
    c_8004004007D: Optional[float] = Field(None, alias="8004004007D", description="#2 NCR用汽量 NCR OMC2 STEAM CONSUMPION")
    
    c_8004005001: Optional[float] = Field(None, alias="8004005001", description="Blow 蒸汽量 blow STEAM CONSUMPION")
    c_8004005002: Optional[float] = Field(None, alias="8004005002", description="LOSS 蒸汽量 LOSS STEAM")
    
    c_8003003001: Optional[float] = Field(None, alias="8003003001", description="購電(尖峰) TOP- BUY POWER(KWh)")
    c_8003003002: Optional[float] = Field(None, alias="8003003002", description="購電(半尖峰) SEMI-TOP- BUY POWER(KWh)")
    c_8003003003: Optional[float] = Field(None, alias="8003003003", description="購電(離峰) OFF-TOP-BUY POWER(KWh)")
    
    c_8004003001: Optional[float] = Field(None, alias="8004003001", description="售電(尖峰) TOP-SELL POWER(KWh)")
    c_8004003002: Optional[float] = Field(None, alias="8004003002", description="售電(半尖峰) SEMI-TOP-SELL POWER(KWh)")
    c_8004003003: Optional[float] = Field(None, alias="8004003003", description="售電(離峰) OFF-TOP-SELL POWER(KWh)")
    c_8004003004: Optional[float] = Field(None, alias="8004003004", description="售電 SELL TPC POWER(KWh)")
    
    c_8004005003: Optional[float] = Field(None, alias="8004005003", description="製程用電 MILL PROCESS USED POWER(KWh)")

    class Config:
        populate_by_name = True
