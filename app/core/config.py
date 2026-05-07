#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
from pathlib import Path
<<<<<<< HEAD
import sys

class Settings:
    def __init__(self):
        # =============================
        # 專案根目錄判斷（可打包）
        # =============================
        if getattr(sys, "frozen", False):
            base_dir = Path(sys._MEIPASS) / "app"
        else:
            base_dir = Path(__file__).resolve().parent.parent
            
        # appsettings.json 路徑
        config_path = base_dir / "appsettings.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Cannot find {config_path}")        
        
        # 讀取設定
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # =============================
        # 設定屬性
        # =============================        
        self.CORS = config.get("CORS", [])
        self.SERVER_HOST = config.get("Server", {}).get("Host", "127.0.0.1")
        self.SERVER_PORT = config.get("Server", {}).get("Port", 8000)
=======

class Settings:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        config_path = base_dir / "appsettings.json"

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.CORS = config["CORS"]
        self.SERVER_HOST = config["Server"]["Host"]
        self.SERVER_PORT = config["Server"]["Port"]
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d

settings = Settings()

