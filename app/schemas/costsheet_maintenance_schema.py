#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel
from typing import Optional

class CoatingWeightModel(BaseModel):
    Machine: str
    PN2: str
    PN4: str
    PaperGSM: int
    ProductGSM: int
    PN4BW: int
    TypePaperGSM: str
    TypeProductGSM: str
    OnMachineCoating: float
    OffMachineCoating1: float
    OffMachineCoating2: float
    TotalCoating: float
    TypeName: str
    BasePN4: str
    BasePaperGSM: int
    buser: str
    muser: str

    class Config:
        schema_extra = {
            "example": {
                "Machine": "M01",
                "PN2": "P1",
                "PN4": "P123",
                "PaperGSM": 80,
                "ProductGSM": 82,
                "PN4BW": 100,
                "TypePaperGSM": "TypeA",
                "TypeProductGSM": "TypeB",
                "OnMachineCoating": 2.5,
                "OffMachineCoating1": 1.0,
                "OffMachineCoating2": 0.5,
                "TotalCoating": 4.0,
                "TypeName": "A",
                "BasePN4": "B123",
                "BasePaperGSM": 80,
                "buser": "admin",
                "muser": "admin"
            }
        }

class CoatingWeightUpdateModel(BaseModel):
    Machine: Optional[str] = None
    PN2: Optional[str] = None
    PN4: Optional[str] = None
    PaperGSM: Optional[int] = None
    ProductGSM: Optional[int] = None
    PN4BW: Optional[int] = None
    TypePaperGSM: Optional[str] = None
    TypeProductGSM: Optional[str] = None
    OnMachineCoating: Optional[float] = None
    OffMachineCoating1: Optional[float] = None
    OffMachineCoating2: Optional[float] = None
    TotalCoating: Optional[float] = None
    TypeName: Optional[str] = None
    BasePN4: Optional[str] = None
    BasePaperGSM: Optional[int] = None
    buser: Optional[str] = None
    muser: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "Machine": "M01",
                "PN4": "UPDA",
                "TotalCoating": 5.0,
                "muser": "admin"
            }
        }

