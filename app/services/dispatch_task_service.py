#!/usr/bin/env python
# coding: utf-8



#!/usr/bin/env python
# coding: utf-8

import json
import uuid
from datetime import datetime


class DispatchTaskService:

    QUEUE_KEY = "task:dispatch:queue"
    STATUS_KEY = "task:dispatch:status"
    LOCK_KEY = "task:dispatch:lock"
    LOCK_TTL_SECONDS = 3600  # 保險用 TTL，正常情況由 worker 主動釋放鎖

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def trigger(self) -> dict:
        """送出觸發請求。回傳 dict；若已有任務進行中，acquired 為 False。"""
        trigger_id = str(uuid.uuid4())

        # SET NX：搶不到鎖代表已有一次觸發在進行中
        acquired = self.redis_client.set(
            self.LOCK_KEY, trigger_id, nx=True, ex=self.LOCK_TTL_SECONDS
        )
        if not acquired:
            return {"acquired": False}

        now = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
        self.redis_client.set(self.STATUS_KEY, json.dumps({
            "trigger_id": trigger_id,
            "status": "queued",
            "message": "已送出觸發請求，等待主機接收",
            "started_at": "",
            "finished_at": "",
            "updated_at": now,
        }, ensure_ascii=False))
        self.redis_client.lpush(self.QUEUE_KEY, json.dumps({
            "trigger_id": trigger_id,
            "requested_at": now,
        }))
        return {"acquired": True, "trigger_id": trigger_id, "status": "queued"}

    def get_status(self) -> dict:
        raw = self.redis_client.get(self.STATUS_KEY)
        if raw is None:
            return {"status": "idle", "message": "尚無執行紀錄"}
        return json.loads(raw)

