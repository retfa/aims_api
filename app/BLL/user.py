from DAL.srvad6.amis.hdtree import hdtreeDal
from DAL.srvmesdbt1.hr.emploee import EmploeeDal
from DAL.user import UserDal


class UserBll:
    def browse(self, data):
        zmuser_dal = UserDal()
        rst = zmuser_dal.query(data)
        print(f'type: {type(rst)}')
        return rst

    def add(self, data):
        zmuser_dal = UserDal()
        rst = zmuser_dal.insert(data)
        return rst

    def edit(self, data):
        zmuser_dal = UserDal()
        rst = zmuser_dal.update(data)
        return rst

    def password_edit(self, data):
        zmuser_dal = UserDal()
        rst = zmuser_dal.update_password(data)
        return rst

    def password_reset(self, data):
        zmuser_dal = UserDal()
        rst = zmuser_dal.reset_password(data)
        return rst

    def status_edit(self, data):
        zmuser_dal = UserDal()
        rst = zmuser_dal.update_status(data)
        return rst

    def read(self, data):
        zmuser_dal = UserDal()
        rst = zmuser_dal.select(data)
        return rst

    def srvad6_hr_read(self, data):
        hdtree_dal = hdtreeDal()
        rst = hdtree_dal.select(data)
        return rst

    def hr_browse(self, data):
        emploee_dal = EmploeeDal()
        rst = emploee_dal.query(data)
        return rst

    def hr_read(self, data):
        emploee_dal = EmploeeDal()
        rst = emploee_dal.select(data)
        return rst

    def hr_add(self, data):
        zmuser_dal = EmploeeDal()
        rst = zmuser_dal.insert(data)
        return rst

    def hr_edit(self, data):
        emploee_dal = EmploeeDal()
        rst = emploee_dal.update(data)
        return rst
