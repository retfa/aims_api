#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
import logging
from types import SimpleNamespace
from app.Kernel.JsonConverter import JsonConverter
from app.BLL.wintriss import wintrissBll

logger = logging.getLogger("MES_API")

class WintrissService:
    @staticmethod
    def get_length_realtime(data: dict):
        start_time = time.time()
        try:
            bll = wintrissBll()
            rst = bll.getLength(data)

            if data.get("ExportFormat") == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)

            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time_ms
        
        except Exception:
            logger.exception("Wintriss get_length failed")
            raise   

