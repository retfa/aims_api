#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
from BLL.menu import MenuBll
from schemas.menu import FtaResponseWrapper
from Kernel.JsonConverter import JsonConverter

import logging
logger = logging.getLogger("MES_API")

class MenuService:
    @staticmethod
    def get_menu(data: dict):
        start_time = time.time()
        try:
            bll = MenuBll()
            rst = bll.browse(data)

            execution_time = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time

        except Exception as e:
            logger.exception("MenuService get_menu failed")
            return [], round((time.time() - start_time) * 1000, 2)

