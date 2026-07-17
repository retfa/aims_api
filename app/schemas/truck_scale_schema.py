from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ItemNameEnum(str, Enum):
    fiber = "fiber"
    coal = "coal"
    sludge = "sludge"

class GetTruckScalePayloads(BaseModel):
    category: Optional[str] = Field(None, description="分類篩選", example="CategoryA")

class PostTruckScalePayload(BaseModel):
    category: ItemNameEnum = Field(..., description="分類", example="fiber")
    item_name: str = Field(..., description="原物料名稱", example="纖維A")
    item_code: str = Field(..., description="項目代碼", example="CodeA")
    company: Optional[str] = Field(None, description="公司")
    company_code: Optional[str] = Field(None, description="公司代碼")
    description: Optional[str] = Field(None, description="說明")
    category_order: int = Field(0, description="排序")

class PutTruckScalePayload(BaseModel):
    id: int = Field(..., description="ID")
    category: Optional[ItemNameEnum] = Field(None, description="分類", example="fiber")
    item_name: Optional[str] = Field(None, description="原物料名稱", example="纖維A")
    item_code: Optional[str] = Field(None, description="項目代碼")
    company: Optional[str] = Field(None, description="公司")
    company_code: Optional[str] = Field(None, description="公司代碼")
    description: Optional[str] = Field(None, description="說明")
    category_order: Optional[int] = Field(None, description="排序")

class DeleteTruckScalePayload(BaseModel):
    id: int = Field(..., description="要刪除的ID")
