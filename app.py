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

if __name__ == '__main__':
    app.run()
