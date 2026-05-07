#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_Outputlist

class GZDataOutputlistService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_Outputlist(servers=servers, redis_client=redis_client)

    def get_outputlist(self, machine):
        return self.fetcher.fetch(MachineName=machine)

