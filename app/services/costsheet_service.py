#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.CostSheet import (
    product_cost_details,
    product_cost_equivalent,
    monthly_equivalent_production,
    monthly_ERP_inventory,
    monthly_yield_rate,
    ERP_inventory,
    End_work_in_process,
    monthly_fixed_fee,
    monthly_energy_usage,
    monthly_Cost_sheet
)

class CostSheetService:
    def __init__(self, servers, redis_client=None):
        self.product_cost_details_fetcher = product_cost_details(servers=servers)
        self.product_cost_equivalent_fetcher = product_cost_equivalent(servers=servers)
        self.monthly_equivalent_production_fetcher = monthly_equivalent_production(servers=servers)
        self.monthly_ERP_inventory_fetcher = monthly_ERP_inventory(servers=servers)
        self.monthly_yield_rate_fetcher = monthly_yield_rate(servers=servers)
        self.ERP_inventory_fetcher = ERP_inventory(servers=servers)
        self.End_work_in_process_fetcher = End_work_in_process(servers=servers)
        self.monthly_fixed_fee_fetcher = monthly_fixed_fee(servers=servers)
        self.monthly_energy_usage_fetcher = monthly_energy_usage(servers=servers)
        self.monthly_Cost_sheet_fetcher = monthly_Cost_sheet(servers=servers)

    def product_cost_details(self, stime, etime, mname, Product_Category, Product_two_ptype, two_month, level):
        return self.product_cost_details_fetcher.fetch(stime=stime, etime=etime, mname=mname,
                                                       Product_Category=Product_Category,
                                                       Product_two_ptype=Product_two_ptype,
                                                       two_month=two_month, level=level)

    def product_cost_equivalent(self, stime, etime, mname, Product_Category, Product_two_ptype, two_month):
        return self.product_cost_equivalent_fetcher.fetch(stime=stime, etime=etime, mname=mname,
                                                          Product_Category=Product_Category,
                                                          Product_two_ptype=Product_two_ptype,
                                                          two_month=two_month)

    def monthly_equivalent_production(self, year):
        return self.monthly_equivalent_production_fetcher.fetch(year=year)

    def monthly_ERP_inventory(self, year):
        return self.monthly_ERP_inventory_fetcher.fetch(year=year)

    def monthly_yield_rate(self, year):
        return self.monthly_yield_rate_fetcher.fetch(year=year)

    def ERP_inventory(self, stime, etime, mname, month):
        return self.ERP_inventory_fetcher.fetch(stime=stime, etime=etime, mname=mname, month=month)

    def End_work_in_process(self, year_month_from):
        return self.End_work_in_process_fetcher.fetch(year_month_from=year_month_from)

    def monthly_fixed_fee(self, year):
        return self.monthly_fixed_fee_fetcher.fetch(year=year)

    def monthly_energy_usage(self, year):
        return self.monthly_energy_usage_fetcher.fetch(year=year)

    def monthly_Cost_sheet(self, year_month_From, mname, year, ptype2):
        return self.monthly_Cost_sheet_fetcher.fetch(year_month_From=year_month_From,
                                                     mname=mname, year=year, ptype2=ptype2)

