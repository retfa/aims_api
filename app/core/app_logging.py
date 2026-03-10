#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import logging
import logging.config
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/
LOG_FILE = os.path.join(BASE_DIR, "core", "app.log")   # 固定到 app/core/app.log

def init_logging(log_file: str):
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
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "level": "INFO",
                "filename": log_file,
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

