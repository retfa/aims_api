from pydantic import BaseModel
from typing import List, Any
from datetime import datetime
import pytz

# ===============================
# 回傳工具類別（取代 Flask 版本）
# ===============================

class FtaResult:
    def __init__(self, data=None, execution_time=0, success=False, export_format="json", status_code=None):
        self.data = data if data is not None else []
        self.execution_time = execution_time
        self.success = success
        self.export_format = export_format
        # status_code 由 success 決定，除非外部指定
        self.status_code = status_code if status_code is not None else (200 if success else 400)

    def to_dict(self):
        # 取得台北時間字串
        utc_now = datetime.now(pytz.utc)
        taipei_time = utc_now.astimezone(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S.%f %z")
        taipei_time_formatted = taipei_time[:-2] + ":" + taipei_time[-2:]

        content = self.data

        # tablejson 模式，直接回傳原始 content
        if self.export_format == "tablejson":
            return {
                "data": {
                    "Action": "",
                    "Content": content,
                    "ExecutionTime": f"{self.execution_time} ms",
                    "ExecutionDto": taipei_time_formatted,
                },
                "success": self.success,
                "status_code": self.status_code,
            }

        # json 模式，只包 metadata，不解析 schema
        length = len(content) if isinstance(content, list) else 1

        return {
            "data": {
                "Action": "",
                "Content": content,
                "ExecutionTime": f"{self.execution_time} ms",
                "ExecutionDto": taipei_time_formatted,
                "Length": length,
            },
            "success": self.success,
            "status_code": self.status_code,
        }