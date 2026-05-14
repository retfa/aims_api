import json
import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from common import get_connection_string

from utils.db_engine import get_session

logger = logging.getLogger("MES_API")

class MenuDal:
    def __init__(self, folders=None):
        trace_msg = f'{self.__class__.__name__}'
        logging.info(trace_msg)
        try:
            SessionLocal = get_session("SRVMESDBA1_AMIS")
            self.Session = SessionLocal()  # ← 建立一個 session 實例
            self.engine = self.Session.get_bind()
            self.folders = folders
        except Exception as e:
            logger.error(f"skyeye.py | init error: {e}")

    def query(self, userid, node):
        if not self.Session:
            raise Exception("Database session not initialized")        
        try:
            with self.Session.begin():
                node_name = f"{node}%"
                query = text('''
                SELECT
                     tree.[floor]
                    ,tree.[f_code]
                    ,tree.[up_code]
                    ,tree.[f_name]
                    ,prog.url
                FROM [AMIS].[dbo].[zdtree] tree
                LEFT JOIN [AMIS].[dbo].[zdpermi] permi on tree.f_code=permi.f_code
                LEFT JOIN [AMIS].[dbo].[zdprogm] prog on tree.f_code=prog.f_code
                where permi.user_id=:userid
                and tree.[f_code] like :node
                order by floor,f_code
                ''')
                result = self.Session.execute(query, {'userid': userid, 'node': node_name})
                rows = result.fetchall()
                
                # 封裝成 dict
                code_dict = {}
                for row in rows:
                    floor, f_code, up_code, f_name, url = row
                    item = {
                        "Depth": floor,
                        "Code": f_code,
                        "ParentCode": up_code,
                        "Name": f_name,
                        "Url": url,
                        "children": []  # 子项为空列表
                    }
                    code_dict[f_code] = item
                
                # 建立樹狀結構
                root_items = []
                for f_code, item in code_dict.items():
                    parent_code = item.get("ParentCode")
                    if parent_code == '0':  # 根项目的up_code为0
                        pass
                    else:
                        parent_item = code_dict.get(parent_code)
                        if parent_item:
                            parent_item["children"].append(item)
                    root_items.append(item)
                    
                  # 過濾指定 Node
                filtered_result = [obj for obj in root_items if obj["Code"] == node]
                return filtered_result
            
        except OperationalError as e:
            msg = f"Database connection error: {str(e)}"
            logging.error(msg)
            raise Exception(msg)

    def queryroot(self, userid):
        if not self.Session:
            raise Exception("Database session not initialized")
            
        try:
            with self.Session.begin():
                query = text('''
                SELECT
                     tree.[floor]
                    ,tree.[f_code]
                    ,tree.[up_code]
                    ,tree.[f_name]
                    ,prog.url
                FROM [AMIS].[dbo].[zdtree] tree
                LEFT JOIN [AMIS].[dbo].[zdpermi] permi on tree.f_code=permi.f_code
                LEFT JOIN [AMIS].[dbo].[zdprogm] prog on tree.f_code=prog.f_code
                where permi.user_id=:userid
                and tree.[up_code] ='0'
                order by floor,f_code
                ''')
                result = self.Session.execute(query, {'userid': userid})
                rows = result.fetchall()
                
                code_dict = {}
                for row in rows:
                    floor, f_code, up_code, f_name, url = row
                    item = {
                        "Depth": floor,
                        "Code": f_code,
                        "ParentCode": up_code,
                        "Name": f_name,
                        "Url": url,
                        "children": []  # 子项为空列表
                    }
                    code_dict[f_code] = item

                root_items = []
                for f_code, item in code_dict.items():
                    parent_code = item.get("ParentCode")
                    if parent_code == '0':  # 根项目的up_code为0
                        pass
                    else:
                        parent_item = code_dict.get(parent_code)
                        if parent_item:
                            parent_item["children"].append(item)
                    root_items.append(item)

                return root_items
        except OperationalError as e:
            msg = f"Database connection error: {str(e)}"
            logging.error(msg)
            raise Exception(msg)
