#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
from datetime import datetime, timezone, timedelta

from BLL.user import UserBll
from schemas.user_schema import (
    UserResponse,
    FtaResponseUser,
    UserItem,
    UserResult,
    EmploeeItem,
    EmploeeResponse,
    FtaResponseEmploee
)
from Model.user import UserSignedIn, ImplicitUserAdd, ImplicitUserEdit, ImplicitUserPasswordEdit, ImplicitUserStatusEdit


class UserService:

    def __init__(self):
        self.bll = UserBll()

    def _get_execution_dto(self):
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        return now.isoformat()


    # 🔹 查詢全部
    def get_users(self, data):
        start = time.time()
        raw = self.bll.browse(data)
        end = time.time()

        content = [UserItem.model_construct(**r) for r in raw] if raw else []

        return FtaResponseUser(
            data=UserResponse(
                Action="GET",
                Content=content,
                ExecutionTime=f"{(end-start)*1000:.2f} ms",
                ExecutionDto=self._get_execution_dto(),
                Length=len(content)
            ),
            status_code=200,
            success=True
        )

    # 🔹 查單一
    def get_user(self, user_id: str):
        start = time.time()
        raw = self.bll.read(user_id)
        end = time.time()

        content = [UserItem.model_construct(**raw)] if raw else []

        return FtaResponseUser(
            data=UserResponse(
                Action="GET",
                Content=content,
                ExecutionTime=f"{(end-start)*1000:.2f} ms",
                ExecutionDto=self._get_execution_dto(),
                Length=len(content)
            ),
            status_code=200,
            success=True
        )

    # 🔹 新增
    def add_user(self, data, payload):
        start = time.time()

        dto = data.dict()
        dto["busr"] = payload["FTAId"]

        instance = ImplicitUserAdd(**dto)
        rst = self.bll.add(instance)

        end = time.time()

        return self._wrap_response("POST", rst, start, end)

    # 🔹 修改
    def edit_user(self, user_id, data, payload):
        start = time.time()

        dto = data.dict()
        dto["user_id"] = user_id
        dto["musr"] = payload["FTAId"]

        instance = UserSignedIn.ImplicitUserEdit(dto)
        rst = self.bll.edit(instance)

        end = time.time()

        return self._wrap_response("PATCH", rst, start, end)

    # 🔹 改密碼
    def edit_password(self, user_id, data, payload):
        start = time.time()

        dto = data.dict()
        dto["user_id"] = user_id
        dto["musr"] = payload["FTAId"]

        instance = UserSignedIn.ImplicitUserPasswordEdit(dto)
        rst = self.bll.password_edit(instance)

        end = time.time()

        return self._wrap_response("PATCH", rst, start, end)
    
    # 🔹 重設密碼
    def reset_password(self, user_id, payload):
        start = time.time()

        rst = self.bll.password_reset(user_id, payload["FTAId"])

        end = time.time()
        return self._wrap_response("PATCH", rst, start, end)    

    # 🔹 啟停用
    def edit_status(self, user_id, data, payload):
        start = time.time()

        dto = data.dict()
        dto["user_id"] = user_id
        dto["musr"] = payload["FTAId"]

        instance = UserSignedIn.ImplicitUserStatusEdit(dto)
        rst = self.bll.status_edit(instance)

        end = time.time()

        return self._wrap_response("PATCH", rst, start, end)
    
    # =================== HR ===================

    # 🔹 HR AD6 查詢使用者
    def srvad6_hr_read(self, id):
        start = time.time()
        raw = self.bll.hr_ad6_read(id)
        end = time.time()

        content = [UserItem.model_construct(**raw)] if raw else []

        return FtaResponseUser(
            data=UserResponse(
                Action="GET",
                Content=content,
                ExecutionTime=f"{(end-start)*1000:.2f} ms",
                ExecutionDto=self._get_execution_dto(),
                Length=len(content)
            ),
            status_code=200,
            success=True
        )

    # 🔹 HR 查詢使用者列表
    def hr_browse(self, data):
        start = time.time()
        raw = self.bll.hr_browse(data)
        end = time.time()
        
        content = [EmploeeItem.model_construct(**r) for r in raw] if raw else []

        return FtaResponseEmploee(
            data=EmploeeResponse(
                Action="GET",
                Content=content,
                ExecutionTime=f"{(end-start)*1000:.2f} ms",
                ExecutionDto=self._get_execution_dto(),
                Length=len(content)
            ),
            status_code=200,
            success=True
        )

    # 🔹 HR 查單一使用者
    def hr_read(self, idhris):
        start = time.time()
        raw = self.bll.hr_read(idhris)
        end = time.time()

        content = [UserItem.model_construct(**raw)] if raw else []

        return FtaResponseUser(
            data=UserResponse(
                Action="GET",
                Content=content,
                ExecutionTime=f"{(end-start)*1000:.2f} ms",
                ExecutionDto=self._get_execution_dto(),
                Length=len(content)
            ),
            status_code=200,
            success=True
        )

    # 🔹 HR 修改資料
    def hr_edit(self, idhris, data, payload):
        start = time.time()

        dto = data.dict()
        dto["user_id_hris"] = idhris
        dto["musr"] = payload["FTAId"]

        instance = ImplicitUserEdit(dto)
        rst = self.bll.hr_edit(instance)

        end = time.time()
        return self._wrap_response("PATCH", rst, start, end)

    # 🔹 HR 新增資料
    def hr_add(self, idhris, data, payload):
        start = time.time()

        dto = data.dict()
        dto["user_id_hris"] = idhris
        dto["busr"] = payload["FTAId"]

        instance = ImplicitUserAdd(**dto)
        rst = self.bll.hr_add(instance)

        end = time.time()
        return self._wrap_response("POST", rst, start, end)    

    # 🔹 共用回傳
    def _wrap_response(self, action, rst, start, end):
        success = rst != -1

        result = UserResult(
            user_id=str(rst) if success else None,
            success=success,
            message="新增成功" if success else "新增失敗"
        )

        return FtaResponseUser(
            data=UserResponse(
                Action=action,
                Content=[result],
                ExecutionTime=f"{(end-start)*1000:.2f} ms",
                ExecutionDto=self._get_execution_dto(),
                Length=1 if success else 0
            ),
            status_code=200 if success else 400,
            success=success
        )

