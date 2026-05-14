#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_diff_data_feature_importance

class GZDataDiffDataFeatureImportanceService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_diff_data_feature_importance(servers=servers)

    def get_feature_importance(self, variable_name, machine, ptype, smax, smin, timetag, bdate, cdate, wmax, wmin):
        return self.fetcher.fetch(
            variable_Name=variable_name,
            MachineName=machine,
            ptype=ptype,
            smax=smax,
            smin=smin,
            timetag=timetag,
            bdate=bdate,
            cdate=cdate,
            wmax=wmax,
            wmin=wmin
        )

