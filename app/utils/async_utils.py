#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# utils/async_utils.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 全域 ThreadPoolExecutor，可以根據 CPU 核心數調整
executor = ThreadPoolExecutor(max_workers=4)

async def run_in_thread(func, *args, **kwargs):
    """
    將同步阻塞函式包成 async，交給 ThreadPoolExecutor 執行
    用法：
        result = await run_in_thread(sync_func, arg1, arg2, kw1=val)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))

