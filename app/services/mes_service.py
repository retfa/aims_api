#!/usr/bin/env python
# coding: utf-8



from resources.MES import (
    amreel_groupby_ptime, 
    ERP_SR_summary, 
    ERP_SH_summary,
    ERP_SR_detail,
    ERP_SR_prod_groupby,
    ERP_SH_detail,    
    adchem_use_d,
    adcoat_use_d,
    adpulp_use_d,
    adcoat_use_d_amortization,
    adchem_use_d_amortization,
    adpulp_use_d_amortization,
    Ampaper_category,
    Defect_induced_recycle_analysis_report,
    Defect_induced_recycle_chart,
    Yield_daily_report,
    Relno_production_history,
    Relno_production_history_duration,
    vehicles_daily_schedule,
    scale_weigh_tickets,
    blanket_replacement_record
)
from resources.energy import energy_daily_sttlement
from resources.truck_scale import truck_scale_payloads

class MESService:

    def __init__(self, servers, redis_client=None):
        self.amreel_fetcher = amreel_groupby_ptime(servers)
        self.erp_sr_fetcher = ERP_SR_summary(servers)
        self.erp_sh_fetcher = ERP_SH_summary(servers)
        self.erp_sr_detail_fetcher = ERP_SR_detail(servers)
        self.erp_sr_prod_groupby_fetcher = ERP_SR_prod_groupby(servers)
        self.erp_sh_detail_fetcher = ERP_SH_detail(servers)        

        self.adchem_use_d_fetcher = adchem_use_d(servers)
        self.adcoat_use_d_fetcher = adcoat_use_d(servers)
        self.adpulp_use_d_fetcher = adpulp_use_d(servers)

        self.adcoat_use_d_amortization_fetcher = adcoat_use_d_amortization(servers)
        self.adchem_use_d_amortization_fetcher = adchem_use_d_amortization(servers)
        self.adpulp_use_d_amortization_fetcher = adpulp_use_d_amortization(servers)
        
        self.ampaper_fetcher = Ampaper_category(servers=servers)
        self.defect_report_fetcher = Defect_induced_recycle_analysis_report(servers=servers)
        self.defect_chart_fetcher = Defect_induced_recycle_chart(servers=servers)
        self.yield_fetcher = Yield_daily_report(servers=servers)
        
        self.relno_fetcher = Relno_production_history(servers=servers) 
        self.relno_duration_fetcher = Relno_production_history_duration(servers=servers) 
        
        self.vehicles_daily_schedule_fetcher = vehicles_daily_schedule(servers=servers)
        
        self.scale_weigh_tickets_fetcher = scale_weigh_tickets(servers=servers)
        
        self.blanket_fetcher = blanket_replacement_record(servers=servers)
        self.energy_daily_settlement_fetcher = energy_daily_sttlement(servers=servers)
        self.truck_scale_payloads_fetcher = truck_scale_payloads(servers=servers)

    def get_amreel_groupby_ptime(self, stime, etime, mname, machine_code=None):
        return self.amreel_fetcher.fetch(stime=stime, etime=etime, mname=mname, MachineCode=machine_code)

    def get_erp_sr_summary(self, stime, etime, mname):
        return self.erp_sr_fetcher.fetch(stime=stime, etime=etime, mname=mname)

    def get_erp_sh_summary(self, stime, etime, mname):
        return self.erp_sh_fetcher.fetch(stime=stime, etime=etime, mname=mname)
    
    def get_erp_sr_detail(self, start_Time, end_Time, mname, detail=True):
        return self.erp_sr_detail_fetcher.fetch(start_Time=start_Time, end_Time=end_Time, mname=mname, detail=detail)

    def get_erp_sr_prod_groupby(self, stime, etime, mname):
        return self.erp_sr_prod_groupby_fetcher.fetch(stime=stime, etime=etime, mname=mname)

    def get_erp_sh_detail(self, start_Time, end_Time, mname, detail=True):
        return self.erp_sh_detail_fetcher.fetch(start_Time=start_Time, end_Time=end_Time, mname=mname, detail=detail)    
    
    def get_adchem_use_d(self, stime, etime, mname):
        return self.adchem_use_d_fetcher.fetch(stime, etime, mname)

    def get_adcoat_use_d(self, stime, etime, mname):
        return self.adcoat_use_d_fetcher.fetch(stime, etime, mname)

    def get_adpulp_use_d(self, stime, etime, mname):
        return self.adpulp_use_d_fetcher.fetch(stime, etime, mname)

    def get_adcoat_use_d_amortization(self, stime, etime, mname):
        return self.adcoat_use_d_amortization_fetcher.fetch(stime, etime, mname)

    def get_adchem_use_d_amortization(self, stime, etime, mname):
        return self.adchem_use_d_amortization_fetcher.fetch(stime, etime, mname)

    def get_adpulp_use_d_amortization(self, stime, etime, mname):
        return self.adpulp_use_d_amortization_fetcher.fetch(stime, etime, mname)    
    
    def ampaper_category(self, stime, etime, mname, mode, year_month_from):
        return self.ampaper_fetcher.fetch(stime=stime, etime=etime, mname=mname, mode=mode, year_month_from=year_month_from)

    def defect_report(self, stime, etime, mname):
        return self.defect_report_fetcher.fetch(stime=stime, etime=etime, mname=mname)

    def defect_chart(self, stime, etime, mname):
        return self.defect_chart_fetcher.fetch(stime=stime, etime=etime, mname=mname)

    def yield_daily_report(self, stime, etime, mname, Product_Category):
        return self.yield_fetcher.fetch(stime=stime, etime=etime, mname=mname, Product_Category=Product_Category)

    def relno_production_history(self, relno):
        return self.relno_fetcher.fetch(relno=relno)    
    
    def relno_production_history_duration(self, stime, etime, mname, relno):
        return self.relno_duration_fetcher.fetch(stime=stime, etime=etime, mname=mname, relno=relno)
    
    def get_vehicles_daily_schedule(self, stime, etime, mname):
        return self.vehicles_daily_schedule_fetcher.fetch(stime, etime, mname)
    
    def refresh_vehicles_daily_schedule(self, stime, etime, mname):
        return self.vehicles_daily_schedule_fetcher.refresh(stime, etime, mname)
    
    def patch_vehicles_daily_schedule(self, id: int, body: dict):
        return self.vehicles_daily_schedule_fetcher.patch(id, body)  
    
    def get_scale_weigh_tickets(self, stime, etime, mname):
        return self.scale_weigh_tickets_fetcher.fetch(stime, etime, mname)
    
    def patch_scale_weigh_tickets(self, body: dict):
        return self.scale_weigh_tickets_fetcher.patch(body)  

    def get_blanket_records(self, mname: str = None, year: int = None):
        return self.blanket_fetcher.fetch(mname=mname, year=year)

    def get_blanket_equipment(self):
        return self.blanket_fetcher.fetch_equipment()

    def post_blanket_record(self, mname: str, change_date: str, equipment_code: str, busr: str):
        return self.blanket_fetcher.create(mname=mname, change_date=change_date, equipment_code=equipment_code, busr=busr)

    def put_blanket_record(self, mname: str, change_date: str, equipment_code: str, new_change_date: str, new_equipment_code: str, busr: str):
        return self.blanket_fetcher.update(mname=mname, change_date=change_date, equipment_code=equipment_code, new_change_date=new_change_date, new_equipment_code=new_equipment_code, busr=busr)

    def delete_blanket_record(self, mname: str, change_date: str, equipment_code: str):
        return self.blanket_fetcher.delete(mname=mname, change_date=change_date, equipment_code=equipment_code)

    def get_energy_record(self, date: str):
        return self.energy_daily_settlement_fetcher.fetch(date=date)

    def patch_energy_record(self, sdate: str, body: dict, user_info: dict):
        return self.energy_daily_settlement_fetcher.patch(sdate_str=sdate, update_fields=body, user_info=user_info)

    def get_truck_scale_payloads(self, category: str = None):
        return self.truck_scale_payloads_fetcher.fetch(category=category)

    def create_truck_scale_payload(self, category: str, item_name: str, item_code: str, company: str = None, company_code: str = None, description: str = None, category_order: int = 0):
        return self.truck_scale_payloads_fetcher.create(
            category=category, item_name=item_name, item_code=item_code,
            company=company, company_code=company_code, description=description,
            category_order=category_order
        )

    def update_truck_scale_payload(self, id: int, item_name: str, category: str = None, item_code: str = None, company: str = None, company_code: str = None, description: str = None, category_order: int = None):
        return self.truck_scale_payloads_fetcher.update(
            id=id, item_name=item_name, category=category, item_code=item_code,
            company=company, company_code=company_code, description=description,
            category_order=category_order
        )

    def delete_truck_scale_payload(self, id: int):
        return self.truck_scale_payloads_fetcher.delete(id=id)


