#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel, Field
from typing import List

# === LengthItem ===
class LengthItem(BaseModel):
    LastPosition: float = Field(..., description="最後位置")


# === LengthResponse ===
class LengthResponse(BaseModel):
    Action: str = Field("", description="API action name")
    Content: List[LengthItem] = Field(..., description="資料內容")
    ExecutionTime: str = Field(..., description="執行時間(ms)")
    ExecutionDto: str = Field(..., description="目前時間")
    Length: int = Field(..., description="資料筆數")


# === API envelope ===
class FtaResponseLength(BaseModel):
    data: LengthResponse
    success: bool
    status_code: int

