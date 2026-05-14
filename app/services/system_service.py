#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import logging
from resources.System import CurrentTime

logger = logging.getLogger("MES_API")

class SystemService:
    def __init__(self, servers):
        self.fetcher = CurrentTime(servers=servers)

    def fetch_current_time(self):
        try:
            return self.fetcher.fetch()
        except Exception as e:
            logger.error(f"CurrentTime fetch error: {e}")
            return {"success": False, "message": str(e)}

