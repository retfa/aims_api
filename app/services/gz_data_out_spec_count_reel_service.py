#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_out_spec_count_reel

class GZDataOutSpecCountReelService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_out_spec_count_reel(servers=servers)

    def get_out_spec_count_reel(self, dFrom, machine):
        return self.fetcher.fetch(dFrom=dFrom, MachineName=machine)

