#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from services.mes_service import MESService

import logging

from utils.async_utils import run_in_thread

router = APIRouter(
    prefix="/MES",
    tags=["MES"]
)

logger = logging.getLogger("MES_API")

service: MESService = None

def get_service() -> MESService:
    if service is None:
        raise RuntimeError("MESService not initialized")
    return service

@router.get(
    "/amreel_groupby_ptime",
    summary="查詢 MES 的各機台彙整的生產資訊",
    description="透過條件查詢 MES 的各機台彙整的生產資訊"
)
def get_amreel_groupby_ptime(
    stime: str = Query(None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(None, alias="mname", description="格式 18、19、20、21"),
    machine_code: str = Query(None, alias="MachineCode", description="(可選)格式 R1、C1、EA、WA"),
    svc: MESService = Depends(get_service)
):
    result = svc.get_amreel_groupby_ptime(stime, etime, mname, machine_code)
    return JSONResponse(content=result)

@router.post("/amreel_groupby_ptime")
def post_amreel_groupby_ptime():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/ERP_SR_summary",
    summary="查詢 MES 的 ERP_SR 資訊",
    description="透過條件查詢 MES 的 ERP_SR 資訊"
)
async def get_erp_sr_summary(
    stime: str = Query(None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    logging.info(f"開始查詢 ERP_SR_summary: {stime} ~ {etime} for {mname}")
    result = await run_in_thread(svc.get_erp_sr_summary, stime, etime, mname)
    logging.info(f"查詢完成 ERP_SR_summary: {stime} ~ {etime} for {mname}")
    return JSONResponse(content=result)

@router.post("/ERP_SR_summary")
def post_erp_sr_summary():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

@router.get("/ERP_SH_summary",
    summary="查詢 MES 的 ERP_SH 資訊",
    description="透過條件查詢 MES 的 ERP_SH 資訊"
)
async def get_erp_sh_summary(
    stime: str = Query(None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    logging.info(f"開始查詢 ERP_SH_summary: {stime} ~ {etime} for {mname}")
    result = await run_in_thread(svc.get_erp_sh_summary, stime, etime, mname)
    logging.info(f"查詢完成 ERP_SH_summary: {stime} ~ {etime} for {mname}")
    return JSONResponse(content=result)

@router.post("/ERP_SH_summary")
def post_erp_sh_summary():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

@router.get("/ERP_SR_detail",
    summary="查詢 MES 的 ERP_SR 明細資訊",
    description="透過 TRANSACTION_DATE 區間查詢 ERP_SR 明細資訊"
)
async def get_erp_sr_detail(
    start_Time: str = Query(None, alias="startTime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    end_Time: str = Query(None, alias="endTime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    mname: str = Query(None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    logging.info(f"開始查詢 ERP_SR_detail: {start_Time} ~ {end_Time} for {mname}")
    result = await run_in_thread(svc.get_erp_sr_detail, start_Time, end_Time, mname)
    logging.info(f"查詢完成 ERP_SR_detail: {start_Time} ~ {end_Time} for {mname}")
    return JSONResponse(content=result)

@router.post("/ERP_SR_detail")
def post_erp_sr_detail():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

@router.get("/ERP_SH_detail",
    summary="查詢 MES 的 ERP_SH 明細資訊",
    description="透過 TRANSACTION_DATE 區間查詢 ERP_SH 明細資訊"
)
async def get_erp_sh_detail(
    start_Time: str = Query(None, alias="startTime", description="起始時間，格式yyyy-mm-dd hh:mm:ss"),
    end_Time: str = Query(None, alias="endTime", description="結束時間，格式yyyy-mm-dd hh:mm:ss"),
    mname: str = Query(None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    logging.info(f"開始查詢 ERP_SH_detail: {start_Time} ~ {end_Time} for {mname}")
    result = await run_in_thread(svc.get_erp_sh_detail, start_Time, end_Time, mname)
    logging.info(f"查詢完成 ERP_SH_detail: {start_Time} ~ {end_Time} for {mname}")
    return JSONResponse(content=result)

@router.post("/ERP_SH_detail")
def post_erp_sh_detail():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

# ------------------ 日化工用量 ------------------
@router.get("/adchem_use_d",
    summary="查詢 MES 的 日化工用量",
    description="透過條件查詢 MES 的 日化工用量"
)
def adchem_use_d(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.get_adchem_use_d(stime, etime, mname)
    return JSONResponse(content=result, media_type="application/json")

@router.post("/adchem_use_d",
    summary="查詢 MES 的 日化工用量",
    description="請使用 GET 查詢 MES 的 日化工用量"
)
def POST_adchem_use_d():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# ------------------ 日塗料用量 ------------------
@router.get("/adcoat_use_d",
    summary="查詢 MES 的 日塗料用量",
    description="透過條件查詢 MES 的 日塗料用量"
)
def adcoat_use_d(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.get_adcoat_use_d(stime, etime, mname)
    return JSONResponse(content=result, media_type="application/json")

@router.post("/adcoat_use_d",
    summary="查詢 MES 的 日塗料用量",
    description="請使用 GET 查詢 MES 的 日塗料用量"
)
def POST_adcoat_use_d():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# ------------------ 日纖維用量 ------------------
@router.get("/adpulp_use_d",
    summary="查詢 MES 的 日纖維用量",
    description="透過條件查詢 MES 的 日纖維用量"
)
def adpulp_use_d(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.get_adpulp_use_d(stime, etime, mname)
    return JSONResponse(content=result, media_type="application/json")

@router.post("/adpulp_use_d",
    summary="查詢 MES 的 日纖維用量",
    description="請使用 GET 查詢 MES 的 日纖維用量"
)
def POST_adpulp_use_d():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# ------------------ 日塗料用量分攤 ------------------
@router.get("/adcoat_use_d_amortization",
    summary="查詢 MES 的 日塗料用量分攤",
    description="透過條件查詢 MES 的 日塗料用量分攤"
)
def adcoat_use_d_amortization(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.get_adcoat_use_d_amortization(stime, etime, mname)
    return JSONResponse(content=result, media_type="application/json")

@router.post("/adcoat_use_d_amortization",
    summary="查詢 MES 的 日塗料用量分攤",
    description="請使用 GET 查詢 MES 的 日塗料用量分攤"
)
def POST_adcoat_use_d_amortization():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# ------------------ 日化工用量分攤 ------------------
@router.get("/adchem_use_d_amortization",
    summary="查詢 MES 的 日化工用量分攤",
    description="透過條件查詢 MES 的 日化工用量分攤"
)
def adchem_use_d_amortization(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.get_adchem_use_d_amortization(stime, etime, mname)
    return JSONResponse(content=result, media_type="application/json")

@router.post("/adchem_use_d_amortization",
    summary="查詢 MES 的 日化工用量分攤",
    description="請使用 GET 查詢 MES 的 日化工用量分攤"
)
def POST_adchem_use_d_amortization():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})


# ------------------ 日纖維用量分攤 ------------------
@router.get("/adpulp_use_d_amortization",
    summary="查詢 MES 的 日纖維用量分攤",
    description="透過條件查詢 MES 的 日纖維用量分攤"
)
def adpulp_use_d_amortization(
    stime: str = Query(default=None, alias="stime", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(default=None, alias="etime", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(default=None, alias="mname", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.get_adpulp_use_d_amortization(stime, etime, mname)
    return JSONResponse(content=result, media_type="application/json")

@router.post("/adpulp_use_d_amortization",
    summary="查詢 MES 的 日纖維用量分攤",
    description="請使用 GET 查詢 MES 的 日纖維用量分攤"
)
def POST_adpulp_use_d_amortization():
    return JSONResponse(content={'success': False, 'message': 'Please use GET'})

# ------------------ ampaper_category ------------------
@router.get("/ampaper-category", summary="查詢 MES 的 該日期區間生產紙別彙整")
def get_ampaper_category(
    stime: str = Query(None, alias="date_from", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(None, alias="date_to", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(None, alias="machine_name", description="格式 18、19、20、21"),
    mode: str = Query(None, alias="mode", description="可選: class表示需要生產類別"),
    year_month_from: str = Query(None, alias="year_month_from", description="可選: yyyy-mm"),
    svc: MESService = Depends(get_service)
):
    result = svc.ampaper_category(stime, etime, mname, mode, year_month_from)
    return JSONResponse(content=result)

@router.post("/ampaper-category")
def post_ampaper_category():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/defect-induced-recycle/report", summary="查詢 MES 的 瑕疵回爐分析資料")
def get_defect_report(
    stime: str = Query(None, alias="yearMonthFrom", description="起始年月，格式yyyy-mm"),
    etime: str = Query(None, alias="yearMonthTo", description="結束年月，格式yyyy-mm"),
    mname: str = Query(None, alias="machineName", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.defect_report(stime, etime, mname)
    return JSONResponse(content=result)

@router.post("/defect-induced-recycle/report")
def post_defect_report():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/defect-induced-recycle/chart", summary="查詢 MES 的 瑕疵回爐分析資料圖")
def get_defect_chart(
    stime: str = Query(None, alias="yearMonthFrom", description="起始年月，格式yyyy-mm"),
    etime: str = Query(None, alias="yearMonthTo", description="結束年月，格式yyyy-mm"),
    mname: str = Query(None, alias="machineName", description="格式 18、19、20、21"),
    svc: MESService = Depends(get_service)
):
    result = svc.defect_chart(stime, etime, mname)
    return JSONResponse(content=result)

@router.post("/defect-induced-recycle/chart")
def post_defect_chart():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/yield-daily-report", summary="查詢 MES 的 加工良率每日報表")
def get_yield_daily_report(
    stime: str = Query(None, alias="date_from", description="起始日期，格式yyyy-mm-dd"),
    etime: str = Query(None, alias="date_to", description="結束日期，格式yyyy-mm-dd"),
    mname: str = Query(None, alias="machine_name", description="格式 18、19、20、21"),
    Product_Category: str = Query(None, alias="category", description="生產類別"),
    svc: MESService = Depends(get_service)
):
    result = svc.yield_daily_report(stime, etime, mname, Product_Category)
    return JSONResponse(content=result)

@router.post("/yield-daily-report")
def post_yield_daily_report():
    return JSONResponse(content={"success": False, "message": "Please use GET"})


@router.get("/Relno-production-history", summary="查詢 MES 的 紙捲號碼生產履歷")
def get_relno_history(
    relno: str = Query(None, alias="relno", description="紙捲號碼"),
    svc: MESService = Depends(get_service)
):
    result = svc.relno_production_history(relno)
    return JSONResponse(content=result)

@router.post("/Relno-production-history")
def post_relno_history():
    return JSONResponse(content={"success": False, "message": "Please use GET"})

