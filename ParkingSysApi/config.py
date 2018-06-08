#数据库配置
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/parking?charset=utf8'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 数据库链接池初始和最大的链接数
SQLALCHEMY_POOL_SIZE = 4
SQLALCHEMY_MAX_OVERFLOW = 20

DEBUG = False
