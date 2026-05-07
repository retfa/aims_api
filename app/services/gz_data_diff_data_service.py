#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_diff_data

class GZDataDiffDataService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_diff_data(servers=servers)

    def get_diff_data(self, variable_name, machine, ptype, smax, smin, bdate, wmax, wmin):
        return self.fetcher.fetch(
            variable_Name=variable_name,
            MachineName=machine,
            ptype=ptype,
            smax=smax,
            smin=smin,
            bdate=bdate,
            wmax=wmax,
            wmin=wmin
        )

