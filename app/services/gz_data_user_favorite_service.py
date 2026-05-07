#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from resources.get_gz_data import GET_GZ_data_user_favorite
from sqlalchemy import text

class GZDataUserFavoriteService:

    def __init__(self, servers, redis_client=None):
        self.fetcher = GET_GZ_data_user_favorite(servers=servers)
        self.servers = servers

    def get_user_favorite(self, isfavorite, machine):
        return self.fetcher.fetch(Isfavorite=isfavorite, MachineName=machine)

    def update_user_favorite(self, favorite_list: list):
        try:
            srv_GZ = self.servers['GZ']
            with srv_GZ['create_engine'][0].connect() as conn:
                with conn.begin():
                    conn.execute(text("DELETE FROM public.favoritesensor"))
                    sql = text("INSERT INTO public.favoritesensor (sensor) VALUES (:sensor)")
                    for sensor in favorite_list:
                        conn.execute(sql, {"sensor": sensor})
        except Exception as e:
            raise RuntimeError(f"Favorite list update failed: {str(e)}")
        return {"success": True, "message": "Favorite list updated successfully"}

