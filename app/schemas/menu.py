#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pydantic import BaseModel, Field
from typing import Any, Optional, List

# === Menu Request ===
class MenuRequest(BaseModel):
    node: int = Field(..., description="節點編號")

# === FTA Result ===
class FtaResultItem(BaseModel):
    # 如果 data 是結構化資料，可以在這裡定義
    # 這裡先用 Any 表示通用資料
    content: Any = Field(..., description="資料內容")

class FtaResponse(BaseModel):
    Action: str = Field("", description="操作名稱，可空")  # 放第一個欄位
    Content: List[FtaResultItem] = Field(..., description="資料內容清單")
    ExecutionTime: float = Field(..., description="執行時間(s)")
    ExecutionDto: str = Field(..., description="執行時間字串")
    Length: int = Field(..., description="資料筆數")

class FtaResponseWrapper(BaseModel):
    data: FtaResponse
    status_code: int = Field(200, description="HTTP 狀態碼")        
    success: bool = Field(..., description="操作是否成功")

