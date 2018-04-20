from models import *

'''
***************数据库创建(by lei ge)*******************
1.进入mysql创建数据库parking,root用户登录mysql数据库执行以下语句:
  CREATE DATABASE parking CHARSET=UTF8
2.在config.py配置数据库连接
3.执行在create_db.py
'''

#***************创建数据库表*****************
db.drop_all()
db.create_all()


#**************初始化错误码表*****************
e200 = ErrorCode('200', 'OK')
e201 = ErrorCode('201', 'CREATED')
e204 = ErrorCode('204', 'NO CONTENT')
e400 = ErrorCode('400', 'INVALID REQUEST')
e403 = ErrorCode('403', 'Forbidden')
e404 = ErrorCode('404', 'NOT FOUND')
e500 = ErrorCode('500', 'INTERNAL SERVER ERROR')
db.session.add(e200)
db.session.add(e201)
db.session.add(e204)
db.session.add(e400)
db.session.add(e404)
db.session.add(e500)
db.session.commit()
