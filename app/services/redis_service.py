#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
from typing import List, Optional

class RedisService:
    def __init__(self, redis_client):
        self.client = redis_client

    def scan_keys(self, keywords: Optional[List[str]], limit: int = 1000):
        """
        根據關鍵字搜尋 Redis keys
        若 keywords 為 None 或空，則搜尋全部
        並限制最多返回 limit 筆
        """        
        all_keys = set()
        
        # 👉 沒給 keywords = 全部
        if not keywords:
            keywords = [""]  # 等同 match="*"      
            
        for kw in keywords:
            cursor = 0
            while True:
                cursor, batch = self.client.scan(cursor=cursor, match=f"*{kw}*", count=100)
                for k in batch:
                    all_keys.add(k)
                    # 👉 達到上限就直接停止
                    if len(all_keys) >= limit:
                        return [
                            {"key": key, "ttl": self.client.ttl(key)}
                            for key in all_keys
                        ]
                if cursor == 0:
                    break
        all_keys = list(set(all_keys))
        return [{"key": k, "ttl": self.client.ttl(k)} for k in all_keys]

    def get_key(self, key: str, limit: int = 100):
        """
        取得 key 的值，若是 JSON 並含 "data" 欄位，會限制返回筆數
        """        
        value = self.client.get(key)
        if value is None:
            return {"success": False, "message": "Key not found"}
        try:
            parsed = json.loads(value)
        except:
            parsed = value
        if isinstance(parsed, dict) and "data" in parsed:
            total = len(parsed["data"])
            parsed["data"] = parsed["data"][:limit]
            return {
                "key": key,
                "ttl": self.client.ttl(key),
                "total": total,
                "show": len(parsed["data"]),
                "data": parsed
            }
        return {"key": key, "ttl": self.client.ttl(key), "data": parsed}

    def delete_key(self, key: str):
        """
        刪除指定 key
        """        
        result = self.client.delete(key)
        return {"deleted": result}

