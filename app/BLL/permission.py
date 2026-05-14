from DAL.permission import PermissionDal


class PermissionBll:
    def browse(self, data):
        return data
        dal = PermissionDal()
        rst = dal.query(data)
        return rst

    def add(self, data):
        dal = PermissionDal()
        rst = dal.insert(data)
        return rst

    def edit(self, data):
        dal = PermissionDal()
        rst = dal.update(data)
        return rst

    def editbulk(self, data):
        dal = PermissionDal()
        dal.delete_by_upcode(data)
        rst = dal.insert_by_upcode(data)
        return rst

    def read(self, data):
        return data
        dal = PermissionDal()
        rst = dal.select(data)
        return rst

    def read_by_user(self, data):
        dal = PermissionDal()
        rst = dal.query(data)
        return rst

    def copy(self, data):
        # return data
        dal = PermissionDal()
        rst = dal.copy(data)
        return rst

    def delete(self, data):
        dal = PermissionDal()
        rst = dal.delete(data)
        return rst
