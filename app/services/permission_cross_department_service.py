#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
from datetime import datetime, timezone, timedelta
from BLL.permissioncrossdepartment import PermissionCrossDepartmentBll
from schemas.permission_cross_department_schema import (
    PermissionCrossDepartmentQuery,
    PermissionCrossDepartmentEdit,
    PermissionCrossDepartmentItem,
    PermissionCrossDepartmentResponse,
    FtaResponsePermissionCrossDepartment
)

class PermissionCrossDepartmentService:
    def __init__(self):
        self.bll = PermissionCrossDepartmentBll()

    def _get_execution_dto(self):
        tz = timezone(timedelta(hours=8))
        return datetime.now(tz).isoformat()

    def browse(self, query: PermissionCrossDepartmentQuery):
        start_time = time.time()
        raw_data = self.bll.browse(query)
        end_time = time.time()

        content = [PermissionCrossDepartmentItem(**row) for row in raw_data] if raw_data else []

        response = PermissionCrossDepartmentResponse(
            Action="GET",
            Content=content,
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=len(content),
        )
        return FtaResponsePermissionCrossDepartment(data=response, success=True, status_code=200)

    def read(self, user_id: str, query: PermissionCrossDepartmentQuery):
        start_time = time.time()
        query.user_id = user_id
        raw_data = self.bll.read(query)
        end_time = time.time()

        content = [PermissionCrossDepartmentItem(**row) for row in raw_data] if raw_data else []

        response = PermissionCrossDepartmentResponse(
            Action="GET",
            Content=content,
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=len(content),
        )
        return FtaResponsePermissionCrossDepartment(data=response, success=True, status_code=200)

    def edit(self, user_id: str, data: PermissionCrossDepartmentEdit, current_user_id: str):
        start_time = time.time()
        payload = data.dict()
        payload['user_id'] = user_id
        payload['busr'] = current_user_id
        payload['musr'] = current_user_id

        rst = self.bll.edit(payload) or 0
        end_time = time.time()

        response = PermissionCrossDepartmentResponse(
            Action="PUT",
            Content=[],
            ExecutionTime=f"{(end_time - start_time)*1000:.2f} ms",
            ExecutionDto=self._get_execution_dto(),
            Length=rst if rst else 0,
        )
        return FtaResponsePermissionCrossDepartment(data=response, success=True, status_code=200)

