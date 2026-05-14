#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.costsheet_service import CostSheetService

from utils.async_utils import run_in_thread

router = APIRouter(prefix="/MES", tags=["CostSheet"])
service: CostSheetService = None

def get_service() -> CostSheetService:
    if service is None:
        raise RuntimeError("CostSheetService not initialized")
    return service

# -------- CostSheet API 範例 --------
@router.get("/product_cost_details",
        summary="查詢 會計 成本單",
        description="透過條件查詢 會計 成本單")
async def get_product_cost_details(
    stime: str = Query(None, alias="stime", description="起始年月，格式yyyymm"),
    etime: str = Query(None, alias="etime", description="結束年月，格式yyyymm"),
    mname: str = Query(None, alias="mname", description="格式 18、19、20、21"),
    Product_Category: str = Query(None, alias="category", description="格式 根據level 不同 值不同 預設是1 格式 格拉新、NCR"),
    Product_two_ptype: str = Query(None, alias="ptype_two", description="(可選)兩碼紙別 格式 KL、SL、KA"),
    two_month: str = Query(None, alias="two_month", description="(可選)格式 1 表示只顯示兩個月的資料 0 表示顯示三個月的資料 預設為 0"),
    level: str = Query(None, alias="level", description="(可選)格式 1 表示銷售類別 2 表示兩碼紙別 3 表示四碼紙別"),
    svc: CostSheetService = Depends(get_service)
):
    result = await run_in_thread(
        svc.product_cost_details, 
        stime, etime, mname, Product_Category, Product_two_ptype, two_month, level
    )    
#     result = svc.product_cost_details(stime, etime, mname, Product_Category, Product_two_ptype, two_month, level)
    return JSONResponse(content=result)

@router.post("/product_cost_details",
        summary="查詢 會計 成本單",
        description="請使用 GET 查詢 會計 成本單")
def post_product_cost_details():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/product_cost_equivalent",
        summary="查詢 會計 約當量與得率報表",
        description="透過條件查詢 會計 約當量與得率報表")
def get_product_cost_equivalent(
    stime: str = Query(None, alias="stime", description="起始年月，格式yyyymm"),
    etime: str = Query(None, alias="etime", description="結束年月，格式yyyymm"),
    mname: str = Query(None, alias="mname", description="格式 18、19、20、21"),
    Product_Category: str = Query(None, alias="category", description="銷售類別 格式 格拉新、NCR"),
    Product_two_ptype: str = Query(None, alias="ptype_two", description="(可選)兩碼紙別 格式 KL、SL、KA"),
    two_month: str = Query(None, alias="two_month", description="(可選)格式 1 表示只顯示兩個月的資料 0 表示顯示三個月的資料 預設為 0"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.product_cost_equivalent(stime, etime, mname, Product_Category, Product_two_ptype, two_month)
    return JSONResponse(content=result)

@router.post("/product_cost_equivalent",
        summary="查詢 會計 約當量與得率報表",
        description="請使用 GET 查詢 會計 約當量與得率報表")
def post_product_cost_equivalent():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/monthly_equivalent_production",
        summary="查詢 會計 約當產量報表",
        description="透過條件查詢 會計 約當產量報表")
def get_monthly_equivalent_production(
    year: str = Query(None, alias="year", description="年份，格式yyyy"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.monthly_equivalent_production(year)
    return JSONResponse(content=result)

@router.post("/monthly_equivalent_production",
        summary="查詢 會計 約當產量報表",
        description="請使用 GET 查詢 會計 約當產量報表")
def post_monthly_equivalent_production():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/monthly_ERP_inventory",
        summary="查詢 會計 入庫量月報表",
        description="透過條件查詢 會計 入庫量月報表")
def get_monthly_ERP_inventory(
    year: str = Query(None, alias="year", description="年份，格式yyyy"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.monthly_ERP_inventory(year)
    return JSONResponse(content=result)

@router.post("/monthly_ERP_inventory",
        summary="查詢 會計 入庫量月報表",
        description="請使用 GET 查詢 會計 入庫量月報表")
def post_monthly_ERP_inventory():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/monthly_yield_rate",
        summary="查詢 會計 月得率報表",
        description="透過條件查詢 會計 月得率報表")
def get_monthly_yield_rate(
    year: str = Query(None, alias="year", description="年份，格式yyyy"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.monthly_yield_rate(year)
    return JSONResponse(content=result)

@router.post("/monthly_yield_rate",
        summary="查詢 會計 月得率報表",
        description="請使用 GET 查詢 會計 月得率報表")
def post_monthly_yield_rate():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/erp-inventory",
        summary="查詢 入庫量報表",
        description="透過條件查詢 入庫量報表")
def get_ERP_inventory(
    stime: str = Query(None, alias="date_from", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(None, alias="date_to", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(None, alias="machine_name", description="格式 18、19、20、21"),
    month: str = Query(None, alias="month", description="可選: yyyy-mm"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.ERP_inventory(stime, etime, mname, month)
    return JSONResponse(content=result)

@router.post("/erp-inventory",
        summary="查詢 入庫量報表",
        description="請使用 GET 查詢 入庫量報表")
def post_ERP_inventory():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/End_work_in_process",
        summary="查詢 期末在產品報表",
        description="透過條件查詢 期末在產品報表")
def get_End_work_in_process(
    year_month_from: str = Query(None, alias="year_month_from", description="年月，格式yyyymm"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.End_work_in_process(year_month_from)
    return JSONResponse(content=result)

@router.post("/End_work_in_process",
        summary="查詢 期末在產品報表",
        description="請使用 GET 查詢 期末在產品報表")
def post_End_work_in_process():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/monthly_fixed_fee",
        summary="查詢 會計 固定費用報表",
        description="透過條件查詢 會計 固定費用報表")
def get_monthly_fixed_fee(
    year: str = Query(None, alias="year", description="年份，格式yyyy"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.monthly_fixed_fee(year)
    return JSONResponse(content=result)

@router.post("/monthly_fixed_fee",
        summary="查詢 會計 固定費用報表",
        description="請使用 GET 查詢 會計 固定費用報表")
def post_monthly_fixed_fee():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/monthly_energy_usage",
        summary="查詢 會計 能源耗用成本報表",
        description="透過條件查詢 會計 能源耗用成本報表")
def get_monthly_energy_usage(
    year: str = Query(None, alias="year", description="年份，格式yyyy"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.monthly_energy_usage(year)
    return JSONResponse(content=result)

@router.post("/monthly_energy_usage",
        summary="查詢 會計 能源耗用成本報表",
        description="請使用 GET 查詢 會計 能源耗用成本報表")
def post_monthly_energy_usage():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/monthly_Cost_sheet",
        summary="查詢 會計 月成本報表",
        description="透過條件查詢 會計 月成本報表，參數為(year,ptype2)、(year_month_From,mname)，前者為年模式、後者為年月模式，任選一對輸入即可")
def get_monthly_Cost_sheet(
    year_month_From: str = Query(None, alias="year_month_From", description="年月，格式yyyymm"),
    mname: str = Query(None, alias="mname", description="格式 PM18、PM19、PM20、PM21"),
    year: str = Query(None, alias="year", description="年份，格式yyyy"),
    ptype2: str = Query(None, alias="ptype2", description="兩碼紙別"),
    svc: CostSheetService = Depends(get_service)
):
    result = svc.monthly_Cost_sheet(year_month_From, mname, year, ptype2)
    return JSONResponse(content=result)

@router.post("/monthly_Cost_sheet",
        summary="查詢 會計 月成本報表",
        description="請使用 GET 查詢 會計 月成本報表")
def post_monthly_Cost_sheet():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

