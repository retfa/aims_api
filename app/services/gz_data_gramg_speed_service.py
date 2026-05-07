#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_gramg_speed

class GZDataGramgSpeedService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_gramg_speed(servers=servers)

    def get_gramg_speed(self, stime, etime, machine):
        # variable_Name 固定為 METROLOGY-COATINGWEIGHT
        return self.fetcher.fetch(
            stime=stime,
            etime=etime,
            variable_Name='METROLOGY-COATINGWEIGHT',
            MachineName=machine
        )

