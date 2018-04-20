from models import *
from flask_restful import Resource,reqparse,fields,marshal_with
from time import localtime,strftime

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
        self.parser.add_argument('balance', type=int)
        self.parser.add_argument('type',type=str)
        self.parser.add_argument('status', type=str)
        self.parser.add_argument('username', type=str)
        self.parser.add_argument('activedate',type=str)
        self.parser.add_argument('userphone',type=str)
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
1.停车进场
  URI:/cards/<int:cardno>/fee
  POST方法
  参数(body):车牌号carno
  
2.查询停车费
  URI:/cards/<int:cardno>/fee
  GET方法
  
3.离场缴费
  URI:/cards/<int:cardno>/fee
  参数(body):优惠券promotioncode(可选择)
  DELETE方法
'''
class FeeRc(Resource):
    def get(self):
        return

    def post(self):
        return

    def delete(self):
        return


'''
---------------------------------充值记录资源-------------------------------------
1.查询充值记录
  URI:/cards/<int:cardnum>/RechargeRecords
  GET方法
  参数(param):starttime,endtime
'''
class RechargeRecordsRc(Resource):
    def get(self):
        return


'''
---------------------------------会员卡消费记录资源--------------------------------------
1.查询会员卡消费记录
  URI:/cards/<int:cardnum>/ConsumedRecords
  GET方法
  参数(param):starttime,endtime
'''
class ConsumedRecordsRc(Resource):
    def get(self):
        return


'''
-------------------------------------优惠券资源-----------------------------------------
1.查询优惠券
  URI:/promotions/<int:code>
  URI:/promotions
  GET方法
  
2.新建一个优惠券
  URI:/promotions/
  POST方法
  参数(body):优惠券号码(可选填，系统随机产生),优惠时长(必填)
  
3.删除优惠券
  URI:/promotions/<int:code>
  DELETE方法
'''
class PromotionsRc(Resource):
    def get(self):
        return

    def post(self):
        return

    def delete(self):
        return
