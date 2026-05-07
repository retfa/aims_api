from DAL.menu import MenuDal


class MenuBll:
    def browse(self, data):
        dal = MenuDal()
        jwt_payload = data.get("jwt", {})
        user_id = jwt_payload.get("FTAId")  # <- 注意 key 要跟 JWT payload 一致        
        if data['Node'] == '0':
            return dal.queryroot(userid=user_id)
        else:
            return dal.query(userid=user_id, node=data['Node'])