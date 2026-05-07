#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import time
import datetime
from datetime import timedelta
from sqlalchemy import text

import requests
import json

from collections import defaultdict


# In[ ]:


import logging
logger = logging.getLogger(__name__)  # 取得和主程式共用的 logger


# In[ ]:


class CurrentTime:
    def __init__(self, servers):
        self.servers = servers       
    
    def fetch(self):
        # 使用本地時間
        now = datetime.datetime.now()
        return {
            "data": [
                {
                    "CurrentTime_time": now.strftime("%Y-%m-%d %H:%M:%S.%f")  # 精確到毫秒
                }
            ]
        }

