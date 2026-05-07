from DAL.permicrossdepartment import PermissionCrossDepartmentDal


class PermissionCrossDepartmentBll:
    def browse(self, data):
        dal = PermissionCrossDepartmentDal()
        rst = dal.query(data)
        return rst

    def add(self, data):
        return data
        dal = PermissionCrossDepartmentDal()
        rst = dal.insert(data)
        return rst

    def edit(self, data):
        # return data
        dal = PermissionCrossDepartmentDal()
        rst = dal.upsert(data)
        return rst

    def read(self, data):
        dal = PermissionCrossDepartmentDal()
        rst = dal.select(data)
        return rst
