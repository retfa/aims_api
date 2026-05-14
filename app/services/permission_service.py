#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from typing import Optional
import time, logging
from datetime import datetime, timezone, timedelta

from BLL.permission import PermissionBll
from schemas.permission_schema import PermissionItem, PermissionQuery, PermissionResponse, FtaResponsePermission, PermissionCopyQuery


class PermissionService:

    def __init__(self):
        self.bll = PermissionBll()

    def _get_execution_dto(self):
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        execution_dto = now.strftime("%Y-%m-%d %H:%M:%S.%f ") + now.strftime("%z")
        execution_dto = execution_dto[:-2] + ":" + execution_dto[-2:]
        return execution_dto        

    def get_permission(self, data):
        start_time = time.time()
        raw_data = self.bll.read_by_user(data)
        end_time = time.time()

        content = [PermissionItem.model_construct(**row)for row in raw_data] if raw_data else []

        response = PermissionResponse(
            Action="GET",
            Content=content,
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=len(content),
        )

        return FtaResponsePermission(data=response,success=True,status_code=200)

    def get_user_permission(self, user_id: str, up_function: Optional[str] = None):
        start_time = time.time()
        raw_data = self.bll.read_by_user(type("Data", (), {"user_id": user_id, "up_function": up_function})())
        end_time = time.time()

        content = [PermissionItem.model_construct(**row)for row in raw_data] if raw_data else []     

        response = PermissionResponse(
            Action="GET",
            Content=content,
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=len(content),
        )

        return FtaResponsePermission(data=response,success=True,status_code=200)
    
    def get_current_permission(self, user_id: str = None, data: PermissionQuery = None):
        """
        查詢當前使用者權限
        user_id: 可選，若使用 JWT 取得就不需要外部傳入
        """
        start_time = time.time()

        if not user_id:
            # 這裡可改成解析 JWT
            raise ValueError("user_id required for current permission")
            
        # 建立查詢物件，把 user_id + query string 的欄位都放進去
        query_obj = type("Data", (), {
            "user_id": user_id,
            "function": data.function if data else None,
            "up_function": data.up_function if data else None,
            "progm_id": data.progm_id if data else None
        })()

        # 呼叫 BLL 取得資料
        raw_data = self.bll.read_by_user(query_obj)

        end_time = time.time()

        content = [PermissionItem.model_construct(**row) for row in raw_data] if raw_data else []

        response = PermissionResponse(
            Action="GET",
            Content=content,
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=datetime.now().isoformat(),
            Length=len(content),
        )

        return FtaResponsePermission(data=response, success=True, status_code=200)    

    def edit_permission(self, user_id, data):
        start_time = time.time()

        data["user_id"] = user_id
        rst = self.bll.editbulk(data)

        end_time = time.time()

        response = PermissionResponse(
            Action="PUT",
            Content=[],
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=rst if rst else 0,
        )

        return FtaResponsePermission(
            data=response,
            success=True,
            status_code=200
        )

    def copy_permission(self, user_id: str, data: PermissionCopyQuery):
        start_time = time.time()
        
        payload = data.dict()
        payload["destination_id"] = user_id
        payload["busr"] = payload.get("busr", user_id)  # 如果 buser 沒帶，可以用自己
        length = self.bll.copy(payload) or 0  # 回傳 INSERT 影響行數
        
        end_time = time.time()

        # 回傳 FtaResponsePermission 格式
        return FtaResponsePermission(
            data=PermissionResponse(
                Action="COPY",
                Content=[],  # COPY 操作通常不回傳完整 Content，可視需求回傳來源/目標ID
                ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
                ExecutionDto=self._get_execution_dto(),
                Length=length
            ),
            status_code=200,
            success=True
        )  

    def delete_permission(self, datum: dict):
        start_time = time.time()
        rst = self.bll.delete(datum)
        end_time = time.time()

        # Content 必須是 list[PermissionItem]
        content = [PermissionItem(
            sid=None,
            user_id=datum["user_id"],
            f_code=datum["function"],
            mname=datum["machine"]
        )] if rst else []

        response = PermissionResponse(
            Action="DELETE",
            Content=content,
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=len(content),
        )
        return FtaResponsePermission(data=response, success=True, status_code=200)

    def delete_permission_bulk(self, data_list: list):
        start_time = time.time()
        deleted_items = []
        for datum in data_list:
            if "machine" not in datum or datum["machine"] is None:
                datum["machine"] = ""
            rst = self.bll.delete(datum)
            if rst not in (-1, None):
                deleted_items.append(datum)
        end_time = time.time()

        response = PermissionResponse(
            Action="DELETE",
            Content=[],
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=len(deleted_items),
        )
        return FtaResponsePermission(data=response, success=True, status_code=200)

