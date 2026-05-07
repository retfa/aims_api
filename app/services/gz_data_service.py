#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data


class GZDataService:

    def __init__(self, servers, redis_client):
        self.fetcher = GET_GZ_data(
            servers=servers,
            redis_client=redis_client
        )

    def get_data(self, stime, etime, variable_name, machine):

        return self.fetcher.fetch(
            stime=stime,
            etime=etime,
            variable_Name=variable_name,
            MachineName=machine
        )

