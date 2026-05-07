#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_feature_importance

class GZDataFeatureImportanceService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_feature_importance(servers=servers)

    def get_feature_importance(self, stime, etime, variable_name, machine):
        return self.fetcher.fetch(
            stime=stime,
            etime=etime,
            variable_Name=variable_name,
            MachineName=machine
        )

