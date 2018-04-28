from models import *
from flask_restful import Resource,reqparse,fields,marshal_with
from time import localtime,strftime,time,mktime,strptime

'''
--------------------------------会员卡资源------------------------------------
1.查询会员卡信息
  URI:/cards/<string:cardno>
  GET方法
  
2.开卡
  URI:/cards
  POST方法,参数写入body
  
3.更改卡信息(如卡状态改为激活状态,充值卡金额)
  URI:/cards/<string:cardno>
  方法:PUT
  3.1 激活会员卡/销卡功能,参数status(写入body)
  3.2 会员卡充值功能,参数balance(写入body)
  
4.删除会员卡
  URI:/cards/<string:cardno>
  DELETE方法
'''

Cards_fields = {
    'error_code': fields.String,
    'reason': fields.String,
    'data': {
        'cardno': fields.String,
        'balance': fields.Integer,
        'type': fields.String,
        'status': fields.String,
        'opendate': fields.DateTime(dt_format='iso8601'),
        'activedate': fields.DateTime(dt_format='iso8601'),
        'closedate': fields.DateTime(dt_format='iso8601'),
        'username': fields.String,
        'userphone': fields.String,
        'remark': fields.String,
    }
}

class CardsRc(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('cardno', type=str)
        self.parser.add_argument('type', type=str)
        self.parser.add_argument('balance', type=int)
        self.parser.add_argument('status', type=str)
        self.parser.add_argument('username', type=str)
        self.parser.add_argument('activedate', type=str)
        self.parser.add_argument('userphone', type=str)
        self.parser.add_argument('remark', type=str)

    #校验输入的参数是否合法
    def checkArgs(self,cardno=None,args=None):
        #URL中的参数
        if cardno is not None:
            if cardno.isdigit() == False or len(cardno) != 6:
                return ErrorCode(400, '卡号必须是6位数字字符组成')

        #HTTP Body中的参数
        if args is not None:
            if args.cardno:
                if args.cardno.isdigit() == False or len(args.cardno) != 6:
                    return ErrorCode(400, '卡号必须是6位数字字符组成')
            if args.balance:
                if args.balance <= 0 or args.balance > 9999\
                    or isinstance(args.balance,int) == False:
                    return ErrorCode(400, '金额必须是(0,9999]的整数')
            if args.type:
                if args.type != '0' and args.type != '1':
                    return ErrorCode(400, '卡类型必须是0,1')
            if args.status:
                if args.status != '1' and args.status != '2':
                    return ErrorCode(400, '卡状态必须是1,2')
            if args.username:
                if len(args.username)>50:
                    return ErrorCode(400, '用户名长度必须小于50')
            if args.userphone:
                if len(args.userphone)>12:
                    return ErrorCode(400, '用户联系方式长度必须小于12')
            if args.remark:
                if len(args.remark)>50:
                    return ErrorCode(400, '备注字符长度必须小于50')

        return None

    #***************根据卡号查询卡信息********************
    @marshal_with(Cards_fields)
    def get(self,cardno):

        #对输入的参数校验
        errorCode = self.checkArgs(cardno)
        if errorCode is not None:
            return errorCode

        #根据卡号查询数据库表cards
        result = Cards.query.get(cardno)
        if result:
            #成功查到，返回结果数据，并且设置返回码为200
            return result.setErrorCode(200,'卡信息查询成功')
        else:
            return ErrorCode(404,'卡号不存在')

    #*****************办理停车卡*****************
    @marshal_with(Cards_fields)
    def post(self):
        #解析POST请求上送的参数
        args = self.parser.parse_args()

        #对输入的参数校验
        errorCode = self.checkArgs(None,args)
        if errorCode is not None:
            return errorCode

        #如果卡号已经存在，报错
        result = Cards.query.get(args.cardno)
        if result is not None:
            return ErrorCode(400,'卡号已存在')

        #生成开卡时间
        myDateTime = strftime("%Y-%m-%d %H:%M:%S", localtime())

        #设置激活状态,银卡默认为未激活状态,临时卡设置为激活状态
        status = '0'
        if args.type == '0':
            status = '1'

        #参数校验成功后，将卡信息插入数据库
        card = Cards(cardno=args.cardno,balance=0,type=args.type,status=status,opendate=myDateTime,\
              username=args.username,userphone=args.userphone,remark=args.remark)
        db.session.add(card)
        db.session.commit()

        #办理停车卡成功，返回卡信息数据，并且设置返回码为201
        result = Cards.query.get(args.cardno)
        return  result.setErrorCode(201,'开卡成功')

    #******************销户功能，停车卡充值功能**********************
    @marshal_with(Cards_fields)
    def put(self,cardno):
        args = self.parser.parse_args()

        #对输入的参数校验
        errorCode = self.checkArgs(cardno,args)
        if errorCode is not None:
            return errorCode

        #卡不存的情况直接报错返回
        card = Cards.query.get(cardno)
        if card is None:
            return ErrorCode(404, '卡号不存在')
        if card.type == '0':
            return ErrorCode(403, '此卡为临时卡')
        if card.status == '2':
            print(card.status)
            return ErrorCode(403, '此卡已销户')

        #获取当前时间
        myDateTime = strftime("%Y-%m-%d %H:%M:%S", localtime())

        #销户
        if args.status == '2':

            #卡正在使用中不能进行销户
            isUse = ParkingFee.query.get(cardno)
            if isUse:
                return ErrorCode(403, '此卡正在消费中,不能销户')

            card.status = '2'
            card.balance = 0               #余额退还客户,变更为0
            card.closedate = myDateTime
            db.session.commit()
            return card.setErrorCode(201,'销户成功')

        #金额参数存在就执行充值
        if args.balance == 0:
            return ErrorCode(400, '金额必须是(0,9999]的整数')
        else:
            #查询充值记录表中最近2笔记录
            result = RechargeRecords.query.filter_by(cardno=cardno) \
                .order_by(RechargeRecords.recordid.desc()).limit(2).all()

            #首次充值
            if len(result) == 0:
                if args.balance >= 200:
                    card.status = '1'                 #大于等于200元默认激活卡
                    card.activedate = myDateTime
                    if args.balance >= 800:           #大于等于800，升级为金卡
                        card.type = '2'
                else:
                    return ErrorCode(400, '首次充值金额最少200元')

            #银卡,连续3次充值的金额大于等于1000元，升级为金卡
            if card.type != '2' and len(result) == 2 and args.balance >= 1000\
                    and result[0].fee >= 1000 and result[1].fee >= 1000:
                card.type = '2'

            #累加充值金额
            card.balance += args.balance
            #插入充值记录表
            rechargeRecord=RechargeRecords(cardno=cardno,fee=args.balance,operatetime=myDateTime)
            db.session.add(rechargeRecord)
            db.session.commit()
            return card.setErrorCode(201,'充值成功')

        #默认返回无效请求错误
        return ErrorCode(400)

    #****************彻底删除卡信息**********************
    #销户的卡才可以删除
    @marshal_with(Cards_fields)
    def delete(self,cardno):

        #对输入的参数校验
        errorCode = self.checkArgs(cardno)
        if errorCode is not None:
            return errorCode

        #根据卡号查询数据库表cards
        card = Cards.query.get(cardno)
        if card is None:
            return ErrorCode(404, '卡号不存在')
        #金卡和银行在销户状态才可以删除
        if card.type != '0' and card.status != '2':
            return ErrorCode(404, '此卡未销户')

        db.session.delete(card)
        #删除卡充值记录和消费记录
        RechargeRecords.query.filter_by(cardno=cardno).delete()
        ConsumedRecords.query.filter_by(cardno=cardno).delete()
        db.session.commit()
        return ErrorCode(204)

'''
--------------------------------停车费资源------------------------------------
1.查询停车费
  URI:/cards/<string:cardno>/fee
  GET方法

2.停车进场
  URI:/cards/<string:cardno>/fee
  POST方法
  参数(body):车牌号carno
   
3.离场缴费
  URI:/cards/<string:cardno>/fee
  DELETE方法
'''
Fee_data_fields = {
    'cardno': fields.String,
    'carno': fields.String,
    'entertime': fields.DateTime(dt_format='iso8601'),
    'leavetime': fields.DateTime(dt_format='iso8601'),
    'totaltime': fields.Integer,
    'promotioncode': fields.String,
    'fee': fields.Integer
}
ParkingFee__fields = {
    'error_code': fields.String(default='200'),
    'reason': fields.String(default='查询成功'),
    'data': fields.Nested(Fee_data_fields)
}
class FeeRc(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('promotioncode', type=str)  #优惠券号码
        self.parser.add_argument('carno',type=str)           #车牌号

    #****************查询停车费(可选优惠券)*********************
    '''
    15分钟内免费停车
    金卡会员2元/小时,每24小时收费24元封顶(12小时计费封顶)
    银卡会员3元/小时,每24小时收费36元封顶(12小时计费封顶)
    临时卡4元/小时,每24小时收费48元封顶(12小时计费封顶)
    '''
    @marshal_with(ParkingFee__fields)
    def get(self,cardno):

        #设置收费规则
        jinka_fee = 2
        yinka_fee = 3
        lska_fee = 4

        #解析的POST参数
        args = self.parser.parse_args()

        #检查cardno是否合法
        if cardno is not None:
            if cardno.isdigit() == False or len(cardno) != 6:
                return ErrorCode('400', '卡号必须是6位数字字符组成')

        #根据卡号查询数据库表cards
        card = Cards.query.get(cardno)
        if card is None:
            return ErrorCode('404', '卡号不存在')

        #根据卡号查询计费表
        parkingFee = ParkingFee.query.get(cardno)
        if parkingFee is None:
            return ErrorCode('404', '无车辆持此卡入场')

        #如果使用优惠券,查询优惠券优惠时间
        if args.promotioncode is not None:
            promotion = Promotions.query.get(args.promotioncode)
            if promotion:
                if promotion.status == '1':
                    return ErrorCode('403','优惠券已被使用')
            else:
                return ErrorCode('404', '优惠券不存在')

        #将入场时间转换成以秒计算的时间
        enterTimeSeconds = mktime(strptime(str(parkingFee.entertime), "%Y-%m-%d %H:%M:%S"))
        #查询截至时间转换成秒
        endtimeSeconds = time()

        #停车时间(秒)
        parkingTimeSeconds = endtimeSeconds - enterTimeSeconds

        #先减去15分钟免费期
        parkingTimeSeconds -= 15*60

        #减去优惠券时间
        if args.promotioncode is not None:
            parkingTimeSeconds -= promotion.time*3600

        #如果小于，把它置为0，方便以下计算
        if parkingTimeSeconds < 0:
            parkingTimeSeconds = 0

        #要计费的小时数
        chargingHours = 0

        #算算车停了一共几天
        parkingDays=parkingTimeSeconds//(3600*24)
        if parkingDays > 0:
            chargingHours = parkingDays*12 #每天最多计费12小时

        #不足一天的计算
        lastDaySeconds=parkingTimeSeconds%(3600*24)
        if lastDaySeconds >= 3600*12:     #不足一天大于12小时,按12小时计费
            chargingHours += 12
        if lastDaySeconds > 0 and lastDaySeconds < 3600*12:  #最后一天停车小于12小时
            if lastDaySeconds%3600 != 0:
                chargingHours += (lastDaySeconds//3600 + 1)

        #临时卡计费,临时卡，银卡，金卡分别计费
        if card.type == '0':
            fee = chargingHours*lska_fee
        elif card.type == '1':
            fee = chargingHours*yinka_fee
        else:
            fee = chargingHours*jinka_fee

        parkingFee.leavetime = strftime("%Y-%m-%d %H:%M:%S", localtime(endtimeSeconds))
        parkingFee.totaltime = endtimeSeconds - enterTimeSeconds
        if args.promotioncode is not None:
            parkingFee.promotioncode = args.promotioncode
        parkingFee.fee = fee

        db.session.commit()

        return {'data': parkingFee}

    #*********************入场停车*************************
    @marshal_with(ParkingFee__fields)
    def post(self,cardno):
        #解析的POST参数
        args = self.parser.parse_args()
        #参数校验
        if cardno is not None:
            if cardno.isdigit() == False or len(cardno) != 6:
                return ErrorCode('400', '卡号必须是6位数字字符组成')
        else:
            return ErrorCode('400', '请输入停车卡号')

        if args.carno is None:
            return ErrorCode('400', '车牌号必须输入')

        if len(args.carno) > 10:
            return ErrorCode('100', '车牌号长度必须小于10')

        #根据卡号查询数据库表cards
        card = Cards.query.get(cardno)
        if card is None:
            return ErrorCode('404', '卡号不存在')
        #未激活销户的卡不能停车
        if card.status == '0' and card.status == '2':
            return ErrorCode('403', '未激活或销户卡不能停车')

        #卡正在使用中，不能重复入场
        isUse = ParkingFee.query.get(cardno)
        if isUse:
            return ErrorCode(403, '此卡正在消费中,不能重复使用')

        #获取当前时间
        nowTime = strftime("%Y-%m-%d %H:%M:%S", localtime())

        parkingFee = ParkingFee(cardno=cardno,carno=args.carno,entertime=nowTime)

        db.session.add(parkingFee)
        db.session.commit()

        return {'error_code': '201', 'reason': '入场成功', 'data': parkingFee}

    #********************离场缴费*********************
    @marshal_with(ParkingFee__fields)
    def delete(self,cardno):
        #参数校验
        if cardno is not None:
            if cardno.isdigit() == False or len(cardno) != 6:
                return ErrorCode('400', '卡号必须是6位数字字符组成')

        #根据卡号查询计费表
        parkingFee = ParkingFee.query.get(cardno)
        if parkingFee is None:
            return ErrorCode('404', '无车辆持此卡入场')

        if parkingFee.leavetime is None:
            return ErrorCode('403', '车辆立场前请先查询车辆停车费用')

        #根据卡号查询数据库表cards
        card = Cards.query.get(cardno)
        if card is None:
            return ErrorCode('404', '卡号不存在')

        #检查优惠券
        if parkingFee.promotioncode is not None:
            promotion = Promotions.query.get(parkingFee.promotioncode)
            if promotion:
                if promotion.status == '1':
                    return ErrorCode('403','优惠券已被使用')
                promotion.status = '1'        #优惠券状态设置为已经使用
            else:
                return ErrorCode('404', '优惠券不存在')

        #银行和金卡，扣除卡余额后才可以缴费离开,临时卡直接现金缴费
        if card.type != '0':
            if card.balance < parkingFee.fee:
                return ErrorCode('403','卡余额不足，请充值后在缴费离场')
            #卡上扣款
            card.balance -= parkingFee.fee    #卡扣款

        #插入消费流水
        consumedRecord = ConsumedRecords(cardno=parkingFee.cardno,\
                                         carno=parkingFee.carno,\
                                         entertime=parkingFee.entertime, \
                                         leavetime=parkingFee.leavetime, \
                                         totaltime=parkingFee.totaltime, \
                                         promotioncode=parkingFee.promotioncode,\
                                         fee=parkingFee.fee)
        db.session.add(consumedRecord)
        #删除计费表中的记录
        db.session.delete(parkingFee)
        db.session.commit()

        return {'error_code': '204', 'reason': '离场缴费成功', 'data': consumedRecord}

'''
---------------------------------充值记录资源-------------------------------------
1.查询充值记录
  URI:/cards/<sting:cardnum>/RechargeRecords
  GET方法
  参数(param):starttime,endtime
'''
RechargeRecords_data_fields = {
    'recordid': fields.Integer,
    'cardno': fields.String,
    'fee': fields.Integer,
    'operatetime': fields.DateTime(dt_format='iso8601')
}

RechargeRecords_fields = {
    'error_code': fields.String(default='200'),
    'reason': fields.String(default='查询成功'),
    'data': fields.List(fields.Nested(RechargeRecords_data_fields))   #数组
}

class RechargeRecordsRc(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('starttime', type=str)  #开始时间
        self.parser.add_argument('endtime',type=str)     #结束时间
        self.parser.add_argument('limit', type=int)      #查询记录数

    # 校验输入的参数是否合法
    def checkArgs(self, cardno=None, args=None):
        # URL中的参数
        if cardno is not None:
            if cardno.isdigit() == False or len(cardno) != 6:
                return ErrorCode('400', '卡号必须是6位数字字符组成')

        # HTTP URL中的 查询参数
        if args is not None:
            if args.starttime:
                if args.starttime.isdigit() == False or len(args.starttime) != 8:
                    return ErrorCode('400', '开始日期必须8为数字字符组成')
            else:
                return ErrorCode('400', '开始日期不能为空')

            if args.endtime:
                if args.endtime.isdigit() == False or len(args.endtime) != 8:
                    return ErrorCode('400', '结束日期必须8为数字字符组成')
            else:
                return ErrorCode('400', '结束日期不能为空')

            if args.starttime > args.endtime:
                return ErrorCode('400', '开始日期不能大于结束日期')

            today = strftime("%Y%m%d", localtime())
            if args.endtime > today:
                return ErrorCode(400, '结束日期不能大于当前日期%s'%today)
            #结束时间等于当前日期+1处理才可以正确查到当前时间的记录
            if args.endtime == today:
                args.endtime = str(int(today)+1)

            if args.limit:
                if args.limit <= 0 or args.limit > 5 \
                        or isinstance(args.limit, int) == False:
                    return ErrorCode(400, '查询条目数最多5条')
            else:
                args.limit = 5         #默认值最多查询5条
        else:
            return ErrorCode(400, '查询参数不能为空')

    #查询充值记录
    @marshal_with(RechargeRecords_fields)
    def get(self,cardno):
        #解析URL中的查询参数
        args = self.parser.parse_args()

        #校验查询参数格式
        errorCode = self.checkArgs(cardno,args)
        if errorCode is not None:
            return errorCode

        #按开始时间结束时间查询充值记录表中记录
        result = RechargeRecords.query\
            .filter(RechargeRecords.cardno==cardno,\
                    RechargeRecords.operatetime>=args.starttime, \
                    RechargeRecords.operatetime<=args.endtime) \
            .order_by(RechargeRecords.recordid.desc()).limit(args.limit).all()

        if result:
            return {'data':result}
        else:
            return ErrorCode(404,'卡号不存在或者无充值记录')


'''
---------------------------------会员卡消费记录资源--------------------------------------
1.查询会员卡消费记录
  URI:/cards/<int:cardnum>/ConsumedRecords
  GET方法
  参数(param):starttime,endtime
'''
ConsumedRecords_data_fields = {
    'recordid': fields.Integer,
    'cardno': fields.String,
    'carno': fields.String,
    'entertime': fields.DateTime(dt_format='iso8601'),
    'leavetime': fields.DateTime(dt_format='iso8601'),
    'totaltime': fields.Integer,
    'promotioncode': fields.String,
    'fee': fields.Integer
}

ConsumedRecords_fields = {
    'error_code': fields.String(default='200'),
    'reason': fields.String(default='查询成功'),
    'data': fields.List(fields.Nested(ConsumedRecords_data_fields))   #数组
}

class ConsumedRecordsRc(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('starttime', type=str)  #开始时间
        self.parser.add_argument('endtime',type=str)     #结束时间

    # 校验输入的参数是否合法
    def checkArgs(self, cardno=None, args=None):
        # URL中的参数
        if cardno is not None:
            if cardno.isdigit() == False or len(cardno) != 6:
                return ErrorCode(400, '卡号必须是6位数字字符组成')

        # HTTP URL中的 查询参数
        if args is not None:
            if args.starttime:
                if args.starttime.isdigit() == False or len(args.starttime) != 8:
                    return ErrorCode(400, '开始日期必须8为数字字符组成')
            else:
                return ErrorCode(400, '开始日期不能为空')

            if args.endtime:
                if args.endtime.isdigit() == False or len(args.endtime) != 8:
                    return ErrorCode(400, '结束日期必须8为数字字符组成')
            else:
                return ErrorCode(400, '结束日期不能为空')

            if args.starttime > args.endtime:
                return ErrorCode(400, '开始日期不能大于结束日期')

            today = strftime("%Y%m%d", localtime())
            if args.endtime > today:
                return ErrorCode(400, '结束日期不能大于当前日期%s'%today)
            #结束时间等于当前日期+1处理才可以正确查到当前时间的记录
            if args.endtime == today:
                args.endtime = str(int(today)+1)
        else:
            return ErrorCode(400, '查询参数不能为空')

    @marshal_with(ConsumedRecords_fields)
    def get(self,cardno):
        #解析URL中的查询参数
        args = self.parser.parse_args()

        #校验查询参数格式
        errorCode = self.checkArgs(cardno,args)
        if errorCode is not None:
            return errorCode

        #按车离场时间查询消费记录表中所有记录
        result = ConsumedRecords.query\
            .filter(ConsumedRecords.cardno==cardno,\
                    ConsumedRecords.leavetime>=args.starttime,\
                    ConsumedRecords.leavetime<=args.endtime)\
            .order_by(ConsumedRecords.recordid.desc()).all()

        if result:
            return {'data':result}
        else:
            return ErrorCode(404,'卡号不存在或者无消费记录')

'''
-------------------------------------优惠券资源-----------------------------------------
1.查询优惠券
  URI:/promotions/<string:promotionCode>
  URI:/promotions
  GET方法
  
2.新建一个优惠券
  URI:/promotions
  POST方法
  参数(body):优惠时长time(必填)
  
3.删除优惠券
  URI:/promotions/<string:promotionCode>
  DELETE方法
'''
Promotions_data_fields = {
    'promotioncode': fields.String,
    'time': fields.Integer,
    'status': fields.String,
    'remark': fields.String
}

Promotions_fields = {
    'error_code': fields.String(default='200'),
    'reason': fields.String(default='查询成功'),
    'data': fields.List(fields.Nested(Promotions_data_fields))   #数组
}

class PromotionsRc(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('time', type=int)    #优惠券时间2小时或24小时

    #校验输入的参数是否合法
    def checkArgs(self, PromotionCode=None, args=None):
        # URL中的参数
        if PromotionCode is not None:
            if PromotionCode.isdigit() == False or len(PromotionCode) != 9:
                return ErrorCode(400, '优惠券号码必须是9位数字字符组成')

        # HTTP Body中的 查询参数
        if args is not None:
            if args.time:
                if args.time != 2 and args.time !=24:
                    return ErrorCode(400, '优惠券时长只能选2或者24')

    #**************查询优惠券**********************
    @marshal_with(Promotions_fields)
    def get(self, promotionCode=None):
        #校验参数格式
        errorCode = self.checkArgs(promotionCode)
        if errorCode is not None:
            return errorCode

        #按优惠券号码查询
        if promotionCode:
            result = Promotions.query.get(promotionCode)
            if result:
                return {'data':[result]}
            else:
                return ErrorCode(404,'优惠券号码不存在')
        else:
        #查询所有优惠券
            result = Promotions.query.all()
            if result:
                return {'data':result}
            else:
                return ErrorCode(404,'没有任何优惠券')

    #***************新建一张优惠券************************
    @marshal_with(Promotions_fields)
    def post(self):
        #解析URL中的查询参数
        args = self.parser.parse_args()

        #校验参数格式
        if args.time is None:
            return ErrorCode(400, '优惠券时长必须填写')

        errorCode = self.checkArgs(None,args)
        if errorCode is not None:
            return errorCode

        #获取优惠券号码
        Promotion = Promotions.query.order_by(Promotions.promotioncode.desc()).first()
        if Promotion:
            newPromotionCode = str(int(Promotion.promotioncode)+1)
        else:
            newPromotionCode = '100000001'

        newPromotion = Promotions(promotioncode=newPromotionCode,time=args.time,status='0')
        db.session.add(newPromotion)
        db.session.commit()

        return {'error_code':'201','reason':'新优惠券创建成功','data':[newPromotion]}

    #*************删除优惠券*******************
    @marshal_with(Promotions_fields)
    def delete(self,promotionCode):
        #校验参数格式
        errorCode = self.checkArgs(promotionCode)
        if errorCode is not None:
            return errorCode

        Promotion = Promotions.query.get(promotionCode)
        if Promotion:
            db.session.delete(Promotion)
            db.session.commit()
            return ErrorCode(204, '删除成功')
        else:
            return ErrorCode(404,'优惠券不存在')
