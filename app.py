from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

# Flask App实例化,并且读取配置文件
app = Flask(__name__)
app.config.from_object('config')

# 数据库实例db
db = SQLAlchemy(app)

# restful Api实例api
api = Api(app)
from resources import *

# 挂载资源到路径上
api.add_resource(CardsRc, '/v1/cards', '/v1/cards/<string:cardno>')
api.add_resource(FeeRc, '/v1/cards/<string:cardno>/fee')
api.add_resource(RechargeRecordsRc, '/v1/cards/<string:cardno>/rechargerecords')
api.add_resource(ConsumedRecordsRc, '/v1/cards/<string:cardno>/consumedrecords')
api.add_resource(PromotionsRc, '/v1/promotions', '/v1/promotions/<string:promotionCode>')

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)

