#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
import logging
from types import SimpleNamespace
from Kernel.JsonConverter import JsonConverter
from BLL.skyeye import SkyeyeBll, SkyeyeCategoryBll,                           SkyeyeImageBll, SkyeyeImageRealtimeBll,                           SkyeyeReelBll, skyeyeRealtimeBll,                           SkyeyeJudgeBll
#                             , SkyeyeReelRealtimeBll

logger = logging.getLogger("MES_API")

class SkyeyeService:
    @staticmethod
    def get_defect(data: dict):
        start_time = time.time()
        
        # ====== 確保必要欄位存在 ======
        data.setdefault("SkyeyeCategory", [])
        data.setdefault("Category", [])
        data.setdefault("ReelNo", [])

        # 處理 CSV
        if data.get("ReelNoCsv"):
            data["ReelNo"] = data["ReelNoCsv"].split(",")

        if data.get("SkyeyeCategoryCsv"):
            data["SkyeyeCategory"] = data["SkyeyeCategoryCsv"].split(",")

        if data.get("CategoryCsv"):
            data["Category"] = data["CategoryCsv"].split(",")
            for cat in data["Category"]:
                if "_" in cat:
                    sub = cat.split("_")[0]
                    if sub not in data["SkyeyeCategory"]:
                        data["SkyeyeCategory"].append(sub)

        # ====== 將 dict 轉成 SimpleNamespace 給 BLL ======
        data_ns = SimpleNamespace(**data)

        # ====== 呼叫 BLL ======
        try:
            bll = SkyeyeBll()
            rst = bll.ReadFromDb(data_ns)  # BLL 仍然用 data.SkyeyeCategory / data.Category

            if data.get("ExportFormat") == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)

            execution_time = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time

        except Exception as e:
            logger.exception("SkyeyeService get_defect failed")
            return [], round((time.time() - start_time) * 1000, 2)
        
    @staticmethod
    def get_defect_category(data: dict):
        start_time = time.time()
        try:
            bll = SkyeyeCategoryBll()
            rst = bll.browse(data)

            if data.get("ExportFormat") == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)

            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time_ms
        
        except Exception:
            logger.exception("Skyeye get_defect_category failed")
            raise   
            
    @staticmethod
    def get_defect_image(data: dict):
        start_time = time.time()

        # 補齊必要欄位
        data.setdefault("ReelNo", [])
        data.setdefault("SkyeyeCategory", [])
        data.setdefault("Category", [])
        data.setdefault("ExportFormat", "json")

        # 處理 CSV 欄位
        if data.get("ReelNoCsv"):
            data["ReelNo"] = data["ReelNoCsv"].split(",")
        if data.get("SkyeyeCategoryCsv"):
            data["SkyeyeCategory"] = data["SkyeyeCategoryCsv"].split(",")
        if data.get("CategoryCsv"):
            data["Category"] = data["CategoryCsv"].split(",")
            for cat in data["Category"]:
                if "_" in cat:
                    sub_category = cat.split("_")[0]
                    if sub_category not in data["SkyeyeCategory"]:
                        data["SkyeyeCategory"].append(sub_category)

        # dict -> SimpleNamespace
        data_ns = SimpleNamespace(**data)

        try:
            bll = SkyeyeImageBll()
            rst = bll.ReadFromDb(data_ns)

            if data["ExportFormat"] == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)

            execution_time = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time
        except Exception as e:
            logger.exception(f"SkyeyeService get_defect_image failed: {e}")
            return [], round((time.time() - start_time) * 1000, 2) 
        
        
#     @staticmethod
#     def get_defect_image_by_uuid(data: dict):
#         start_time = time.time()

#         data.setdefault("ExportFormat", "json")

#         # dict → namespace (因為你 BLL 可能用 data.xxx 取值)
#         data_ns = SimpleNamespace(**data)

#         try:
#             bll = SkyeyeImageBll()
#             rst = bll.ReadFromDbUuid(data_ns)

#             if data["ExportFormat"] == "tablejson":
#                 rst = JsonConverter.dict_array_to_table_json_dict(rst)

#             execution_time = round((time.time() - start_time) * 1000, 2)
#             return rst, execution_time

#         except Exception as e:
#             logger.exception(f"get_defect_image_by_uuid failed: {e}")
#             return [], round((time.time() - start_time) * 1000, 2)    
        
    @staticmethod
    def get_defect_image_realtime(data: dict):
        start_time = time.time()

        # 預設值
        data.setdefault("ReelNo", [])
        data.setdefault("SkyeyeCategory", [])
        data.setdefault("Category", [])
        data.setdefault("ExportFormat", "json")

        # CSV 處理
        if data.get("ReelNoCsv"):
            data["ReelNo"] = data["ReelNoCsv"].split(",")

        if data.get("SkyeyeCategoryCsv"):
            data["SkyeyeCategory"] = data["SkyeyeCategoryCsv"].split(",")

        if data.get("CategoryCsv"):
            data["Category"] = data["CategoryCsv"].split(",")
            for cat in data["Category"]:
                if "_" in cat:
                    sub_category = cat.split("_")[0]
                    if sub_category not in data["SkyeyeCategory"]:
                        data["SkyeyeCategory"].append(sub_category)

        # dict → namespace (因為 BLL 可能用 data.xxx)
        data_ns = SimpleNamespace(**data)

        try:
            bll = SkyeyeImageRealtimeBll()
            rst = bll.ReadFromDb(data_ns)

            if data["ExportFormat"] == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)

            execution_time = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time

        except Exception as e:
            logger.exception(f"get_defect_image_realtime failed: {e}")
            return [], round((time.time() - start_time) * 1000, 2)      
        
    @staticmethod
    def add_defect_judge(data: dict):
        start_time = time.time()

        data_ns = SimpleNamespace(**data)

        try:
            bll = SkyeyeJudgeBll()
            rst = bll.add(data_ns)

            execution_time_ms = round((time.time() - start_time) * 1000, 2)

            # 保留原 tuple 判斷
            if isinstance(rst, tuple):

                return rst[0], execution_time_ms

            return rst, execution_time_ms

        except Exception as e:
            logger.exception(f"add_defect_judge failed: {e}")
            return [], round((time.time() - start_time) * 1000, 2)         
        
    @staticmethod
    def get_defect_reel_statistics(data: dict):
        """
        查詢指定紙捲號的瑕疵統計
        """
        start_time = time.time()

        # 補齊必要欄位
        data.setdefault("ReelNoCsv", "")
        data.setdefault("CategoryCsv", "")
        data.setdefault("ExportFormat", "json")

        if data.get("ReelNoCsv"):
            data["ReelNo"] = data["ReelNoCsv"].split(",")
        if data.get("CategoryCsv"):
            data["Category"] = data["CategoryCsv"].split(",")

        data_ns = SimpleNamespace(**data)

        try:
            bll = SkyeyeReelBll()
            rst = bll.ReadFromDb(data_ns)  # list of dict，每列含 relno + pivot defect 欄位
                
            if data["ExportFormat"] == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)                

            execution_time = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time

        except Exception as e:
            logger.exception(f"SkyeyeService get_defect_reel_statistics failed: {e}")
            return [], round((time.time() - start_time) * 1000, 2)
        
        
#     @staticmethod
#     def get_defect_reel_realtime(data: dict):
#         start_time = time.time()

#         # 補齊必要欄位
#         data.setdefault("ReelNo", [])
#         data.setdefault("Category", [])
#         data.setdefault("ExportFormat", "json")

#         # 處理 CSV 欄位
#         if data.get("ReelNoCsv"):
#             data["ReelNo"] = data["ReelNoCsv"].split(",")
#         if data.get("CategoryCsv"):
#             data["Category"] = data["CategoryCsv"].split(",")

#         # dict -> SimpleNamespace
#         data_ns = SimpleNamespace(**data)

#         try:
#             bll = SkyeyeReelRealtimeBll()
#             rst = bll.ReadFromDb(data_ns)

#             if data["ExportFormat"] == "tablejson":
#                 rst = JsonConverter.dict_array_to_table_json_dict(rst)

#             execution_time = round((time.time() - start_time) * 1000, 2)
#             return rst, execution_time
#         except Exception as e:
#             logger.exception(f"SkyeyeService get_defect_reel_realtime failed: {e}")
#             return [], round((time.time() - start_time) * 1000, 2)           
        
        
    @staticmethod
    def get_defect_realtime(data: dict):
        start_time = time.time()    
        
        # 補齊必要欄位
        data.setdefault("SkyeyeCategory", [])
        data.setdefault("Category", [])
        data.setdefault("ReelNo", [])
        data.setdefault("ExportFormat", "json")

        if data.get("ReelNoCsv"):
            data["ReelNo"] = data["ReelNoCsv"].split(",")

        if data.get("SkyeyeCategoryCsv"):
            data["SkyeyeCategory"] = data["SkyeyeCategoryCsv"].split(",")

        if data.get("CategoryCsv"):
            data["Category"] = data["CategoryCsv"].split(",")
            for cat in data["Category"]:
                if "_" in cat:
                    sub_category = cat.split("_")[0]
                    if sub_category not in data["SkyeyeCategory"]:
                        data["SkyeyeCategory"].append(sub_category)

        # ====== 將 dict 轉成 SimpleNamespace 給 BLL ======
        data_ns = SimpleNamespace(**data)                        

        try:
            bll = skyeyeRealtimeBll()
            rst = bll.ReadFromDb(data_ns)
            if data["ExportFormat"] == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)
            execution_time = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time
        except Exception as e:
            logger.exception(f"SkyeyeService get_defect_realtime failed: {e}")
            return [], round((time.time() - start_time) * 1000, 2)
        
        
    @staticmethod
    def get_rule_alarm(data: dict):
        start_time = time.time()

        data.setdefault("ExportFormat", "json")
        data_ns = SimpleNamespace(**data)

        try:
            bll = SkyeyeCategoryBll()
            rst = bll.browse(data_ns)

            if data["ExportFormat"] == "tablejson":
                rst = JsonConverter.dict_array_to_table_json_dict(rst)

            execution_time = round((time.time() - start_time) * 1000, 2)
            return rst, execution_time

        except Exception as e:
            logger.exception(f"get_rule_alarm failed: {e}")
            return [], round((time.time() - start_time) * 1000, 2)      

