import time
import logging

from sqlalchemy import text

logger = logging.getLogger("MES_API")

class truck_scale_payloads:
    def __init__(self, servers):
        self.servers = servers

    def fetch(self, category: str = None):
        """查詢 Payload 紀錄，以 category_order 降序，id 升序"""
        try:
            srv_db = self.servers['SRVMESDBA1_FTA_TRUCK_SCALE_2026']
            with srv_db['create_engine'][0].connect() as conn:
                sql = "SELECT id, category, item_name, item_code, company, company_code, description, category_order FROM [dbo].[payloads] WHERE 1=1"
                params = {}
                if category:
                    sql += " AND category = :category"
                    params['category'] = category
                
                sql += " ORDER BY category_order DESC, id ASC"
                query = conn.execute(text(sql), params)
                return [dict(i._mapping) for i in query]
        except Exception as e:
            logger.exception(f"查詢 payloads 失敗: {str(e)}")
            raise e

    def create(self, category: str, item_name: str, item_code: str, company: str = None, company_code: str = None, description: str = None, category_order: int = 0):
        """新增 Payload 項目，會檢查 category + item_code 唯一性"""
        try:
            srv_db = self.servers['SRVMESDBA1_FTA_TRUCK_SCALE_2026']
            with srv_db['create_engine'][0].connect() as conn:
                sql_check = "SELECT 1 FROM [dbo].[payloads] WHERE category = :category AND item_code = :item_code"
                exists = conn.execute(text(sql_check), {"category": category, "item_code": item_code}).fetchone()
                if exists:
                    return {"success": False, "message": "相同分類下此項目代碼已存在"}

            with srv_db['create_engine'][0].begin() as conn:
                sql_insert = """
                    INSERT INTO [dbo].[payloads] (category, item_name, item_code, company, company_code, description, category_order)
                    OUTPUT INSERTED.id
                    VALUES (:category, :item_name, :item_code, :company, :company_code, :description, :category_order)
                """
                params = {
                    "category": category,
                    "item_name": item_name,
                    "item_code": item_code,
                    "company": company,
                    "company_code": company_code,
                    "description": description,
                    "category_order": category_order
                }
                new_id = conn.execute(text(sql_insert), params).scalar()

            # 重新查詢並回傳
            with srv_db['create_engine'][0].connect() as conn:
                sql_select = "SELECT id, category, item_name, item_code, company, company_code, description, category_order FROM [dbo].[payloads] WHERE id = :id"
                row = conn.execute(text(sql_select), {"id": new_id}).fetchone()

            if row:
                return {"success": True, "data": dict(row._mapping)}
            return {"success": False, "message": "取得新增資料失敗"}
        except Exception as e:
            logger.exception(f"新增 payload 失敗: {str(e)}")
            raise e

    def update(self, id: int, item_name: str, category: str = None, item_code: str = None, company: str = None, company_code: str = None, description: str = None, category_order: int = None):
        """修改特定的 Payload 項目"""
        try:
            srv_db = self.servers['SRVMESDBA1_FTA_TRUCK_SCALE_2026']
            with srv_db['create_engine'][0].connect() as conn:
                sql_check = "SELECT 1 FROM [dbo].[payloads] WHERE id = :id"
                exists = conn.execute(text(sql_check), {"id": id}).fetchone()
                if not exists:
                    return {"success": False, "message": "找不到要更新的記錄"}

            set_clauses = ["item_name = :item_name"]
            params = {"id": id, "item_name": item_name}

            if category is not None:
                set_clauses.append("category = :category")
                params["category"] = category
            if item_code is not None:
                set_clauses.append("item_code = :item_code")
                params["item_code"] = item_code
            if company is not None:
                set_clauses.append("company = :company")
                params["company"] = company
            if company_code is not None:
                set_clauses.append("company_code = :company_code")
                params["company_code"] = company_code
            if description is not None:
                set_clauses.append("description = :description")
                params["description"] = description
            if category_order is not None:
                set_clauses.append("category_order = :category_order")
                params["category_order"] = category_order

            with srv_db['create_engine'][0].begin() as conn:
                sql_update = f"UPDATE [dbo].[payloads] SET {', '.join(set_clauses)} WHERE id = :id"
                conn.execute(text(sql_update), params)

            # 重新查詢並回傳
            with srv_db['create_engine'][0].connect() as conn:
                sql_select = "SELECT id, category, item_name, item_code, company, company_code, description, category_order FROM [dbo].[payloads] WHERE id = :id"
                row = conn.execute(text(sql_select), {"id": id}).fetchone()

            if row:
                return {"success": True, "data": dict(row._mapping)}
            return {"success": False, "message": "取得更新資料失敗"}
        except Exception as e:
            logger.exception(f"修改 payload 失敗: {str(e)}")
            raise e

    def delete(self, id: int):
        """刪除特定 Payload 項目"""
        try:
            srv_db = self.servers['SRVMESDBA1_FTA_TRUCK_SCALE_2026']
            # 先讀取，以便回傳被刪除的資料
            with srv_db['create_engine'][0].connect() as conn:
                sql_select = "SELECT id, category, item_name, item_code, company, company_code, description, category_order FROM [dbo].[payloads] WHERE id = :id"
                row = conn.execute(text(sql_select), {"id": id}).fetchone()

            if not row:
                return {"success": False, "message": "找不到要刪除的記錄"}

            deleted_data = dict(row._mapping)

            with srv_db['create_engine'][0].begin() as conn:
                sql_delete = "DELETE FROM [dbo].[payloads] WHERE id = :id"
                conn.execute(text(sql_delete), {"id": id})

            return {"success": True, "data": deleted_data}
        except Exception as e:
            logger.exception(f"刪除 payload 失敗: {str(e)}")
            raise e
