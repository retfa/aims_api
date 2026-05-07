#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_prediction_status

class GZDataPredictionStatusService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_prediction_status(servers=servers)

    def get_prediction_status(self, machine):
        return self.fetcher.fetch(MachineName=machine)

