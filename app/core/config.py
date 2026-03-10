#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
from pathlib import Path

class Settings:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        config_path = base_dir / "appsettings.json"

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.CORS = config["CORS"]
        self.SERVER_HOST = config["Server"]["Host"]
        self.SERVER_PORT = config["Server"]["Port"]

settings = Settings()

