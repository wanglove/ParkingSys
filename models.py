from app import db

#停车系统用户表(系统管理员)
class SysUser(db.Model):
    __tablename__ = 'sys_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30), nullable=False)

'''会员卡表'''
class Cards(db.Model):
    __tablename__ = 'cards'
    cardno = db.Column(db.String(10), primary_key=True)  #卡号
    balance = db.Column(db.Integer)                      #卡金额 系统只支持整数金额
    type = db.Column(db.String(1), nullable=False)       #卡类型 0-临时卡 1-金卡 2-银卡
    status = db.Column(db.String(1))                     #卡状态 0-未激活 1-激活 2-销户
    opendate = db.Column(db.DateTime, nullable=False)    #开卡日期
    activedate = db.Column(db.DateTime)                  #激活日期
    closedate = db.Column(db.DateTime)                   #销户日期
    username = db.Column(db.String(50))                  #用户姓名
    userphone = db.Column(db.String(11))                 #用户联系电话
    remark = db.Column(db.String(50))                    #备注

    #给返回数据附加错误码
    def setErrorCode(self,errorCode,reason=None):
        self.error_code = errorCode
        if reason:
            self.reason = reason
        else:
            self.reason = ErrorCode(errorCode).reason
        return self

'''优惠券表'''
class Promotions(db.Model):
    __tablename__ = 'promotions'
    promotioncode = db.Column(db.String(9),primary_key=True) #优惠券码
    time = db.Column(db.Integer, nullable=False)             #优惠时长 只有2小时或24小时
    status = db.Column(db.String(1), nullable=False)         #优惠券状态 0-无效 1-有效
    remark = db.Column(db.String(50), nullable=False)        #备注

'''停车计费表'''
class ParkingFee(db.Model):
    __tablename__ = 'parking_fee'
    cardno = db.Column(db.String(6), primary_key=True)   #卡号
    carno = db.Column(db.String(10), unique=True)        #车牌号
    entertime = db.Column(db.DateTime, nullable=False)   #进场时间

'''消费流水表'''
class ConsumedRecords(db.Model):
    __tablename__ = 'consumed_records'
    recordid = db.Column(db.Integer, primary_key=True)   #消费流水号
    cardno = db.Column(db.String(6), nullable=False)     #卡号
    carno = db.Column(db.String(10), nullable=False)     #车牌号
    entertime = db.Column(db.DateTime, nullable=False)   #进场时间
    leavetime = db.Column(db.DateTime, nullable=False)   #离场时间
    totaltime = db.Column(db.Integer, nullable=False)    #停车时长(分钟)
    promotioncode = db.Column(db.String(9))              #优惠券码
    fee = db.Column(db.Integer, nullable=False)          #停车费用

'''充值流水表'''
class RechargeRecords(db.Model):
    __tablename__ = 'recharge_records'
    recordid = db.Column(db.Integer, primary_key=True)              #充值流水号
    cardno = db.Column(db.String(6), nullable=False)                #卡号
    fee = db.Column(db.Integer, nullable=False)                     #充值金额
    operatetime = db.Column(db.DateTime, nullable=False)            #充值时间

'''错误码表'''
class ErrorCode(db.Model):
    __tablename__ = 'error_codes'
    error_code = db.Column(db.String(4), primary_key=True)  #错误码
    reason = db.Column(db.String(128))                      #错误说明

    #类初始化,根据错误码查询错误说明
    def __init__(self,errorCode,reason=None):
        self.error_code = errorCode
        #支持自定义错误码和错误原因
        if reason:
            self.reason = reason
        else:
            result = ErrorCode.query.get(errorCode)
            if result is not None:
                self.reason = result.reason
            else:
                self.reason = 'Not found reason for errorCode[%s]' % str(errorCode)

