#数据库配置
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/parking?charset=utf8'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 数据库链接池初始和最大的链接数
SQLALCHEMY_POOL_SIZE = 4
SQLALCHEMY_MAX_OVERFLOW = 20

# token加密的密钥，随机写,token过期时间单位为秒
SECRET_KEY = 'sdkfjlqjluio23u429037907!@#!@#!@@'
TOKEN_EXPIRES_TIME = 600

DEBUG = False
