#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung

class GZDataMachineRunService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_Machine_Run_Sheet_Break_Signal_Scanner_Runnung(servers=servers)

    def get_machine_run(self, stime, etime, machine):
        # variable_Name 固定為 METROLOGY-COATINGWEIGHT
        return self.fetcher.fetch(
            stime=stime,
            etime=etime,
            variable_Name='METROLOGY-COATINGWEIGHT',
            MachineName=machine
        )

