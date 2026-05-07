#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from schemas.costsheet_maintenance_schema import CoatingWeightModel, CoatingWeightUpdateModel
from resources.CostSheet_Maintenance import CoatingWeight
from sqlalchemy import text

class CoatingWeightService:
    def __init__(self, db_engine, fetcher=None):
        self.fetcher = CoatingWeight(servers=servers)

    def get_all(self):
        return self.fetcher.fetch()

    def create(self, payload: CoatingWeightModel):
        payload_dict = payload.dict()
        try:
            with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
                fields = ", ".join(payload_dict.keys())
                values = ", ".join(f":{k}" for k in payload_dict.keys())
                sql = f"INSERT INTO [Accounting].[dbo].[CoatingWeight] ({fields}) VALUES ({values})"
                conn.execute(text(sql), payload_dict)
            return {"success": True, "message": "Inserted successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def update(self, sn: int, payload: CoatingWeightUpdateModel):
        update_data = payload.dict(exclude_unset=True)
        if not update_data:
            return {"success": False, "message": "No data provided for update"}
        update_data["sn"] = sn
        set_clause = ", ".join(f"{k} = :{k}" for k in update_data.keys() if k != "sn")
        try:
            with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
                sql = f"UPDATE [Accounting].[dbo].[CoatingWeight] SET {set_clause} WHERE Sn = :sn"
                conn.execute(text(sql), update_data)
            return {"success": True, "message": "Updated successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete(self, sn: int):
        try:
            with df_SERVER_SRVMSDBA1['create_engine'][0].connect() as conn:
                sql = "DELETE FROM [Accounting].[dbo].[CoatingWeight] WHERE Sn = :sn"
                conn.execute(text(sql), {"sn": sn})
            return {"success": True, "message": "Deleted successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

