#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import sys

def get_temproot_and_exe_folder():
    """
    取得 exe 路徑與 temproot 資料夾路徑
    - PyInstaller 打包後：temproot -> _MEIPASS, exe -> exe 所在資料夾
    - 非打包：temproot/exe -> 專案根目錄
    """
    if getattr(sys, 'frozen', False):
        exe_folder = os.path.abspath(os.path.dirname(sys.argv[0]))
        temproot = getattr(sys, '_MEIPASS', '')
    else:
        exe_folder = os.path.abspath(os.path.dirname(__file__))
        temproot = exe_folder
    return temproot, exe_folder

