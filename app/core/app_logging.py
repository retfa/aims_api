#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import logging
import logging.config
<<<<<<< HEAD
from pathlib import Path
import sys

def init_logging(log_file: Path):
    # 確保 log 資料夾存在
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
=======
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/
LOG_FILE = os.path.join(BASE_DIR, "core", "app.log")   # 固定到 app/core/app.log

def init_logging(log_file: str):
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
<<<<<<< HEAD
=======
                "stream": sys.stdout,
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "level": "INFO",
<<<<<<< HEAD
                "filename": str(log_file),
=======
                "filename": log_file,
>>>>>>> 5fdc104f2621270c2c6ffd3627dc2ff894f4834d
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)

