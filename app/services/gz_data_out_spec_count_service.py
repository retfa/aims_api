#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_out_spec_count

class GZDataOutSpecCountService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_out_spec_count(servers=servers)

    def get_out_spec_count(self, stime, etime, machine):
        # variable_Name 固定為 METROLOGY-COATINGWEIGHT
        return self.fetcher.fetch(
            stime=stime,
            etime=etime,
            variable_Name='METROLOGY-COATINGWEIGHT',
            MachineName=machine
        )

