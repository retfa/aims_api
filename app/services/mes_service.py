#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.MES import (
    amreel_groupby_ptime, 
    ERP_SR_summary, 
    ERP_SH_summary,
    ERP_SR_detail,
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
    Relno_production_history    
)

class MESService:

    def __init__(self, servers, redis_client=None):
        self.amreel_fetcher = amreel_groupby_ptime(servers)
        self.erp_sr_fetcher = ERP_SR_summary(servers)
        self.erp_sh_fetcher = ERP_SH_summary(servers)
        self.erp_sr_detail_fetcher = ERP_SR_detail(servers)
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

    def get_amreel_groupby_ptime(self, stime, etime, mname, machine_code=None):
        return self.amreel_fetcher.fetch(stime=stime, etime=etime, mname=mname, MachineCode=machine_code)

    def get_erp_sr_summary(self, stime, etime, mname):
        return self.erp_sr_fetcher.fetch(stime=stime, etime=etime, mname=mname)

    def get_erp_sh_summary(self, stime, etime, mname):
        return self.erp_sh_fetcher.fetch(stime=stime, etime=etime, mname=mname)

    def get_erp_sr_detail(self, start_Time, end_Time, mname):
        return self.erp_sr_detail_fetcher.fetch(start_Time=start_Time, end_Time=end_Time, mname=mname)

    def get_erp_sh_detail(self, start_Time, end_Time, mname):
        return self.erp_sh_detail_fetcher.fetch(start_Time=start_Time, end_Time=end_Time, mname=mname)
    
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

