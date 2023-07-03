# -*- coding: utf-8 -*-

# @Time    : 2020/6/9 下午3:04
# @Author  : gaoqi

import json
import sys

from flask import Flask, Response, request
from datetime import datetime

sys.path.append('.')
from utils.log import get_logger
from utils.decorator import web_exception_handler
from utils.db_manager import DBManager
from web.user_router import user_router
from web.sd_router import sd_router
from web.chat_router import chat_router
from utils.db_manager import dbm

# logger
logger = get_logger('./log/server.log')

app = Flask("python-template-server", static_folder='./static', static_url_path='/vision/')
app.register_blueprint(user_router)
app.register_blueprint(sd_router)
# app.register_blueprint(chat_router)


@app.route('/vision/python/template/hello', methods=['GET', 'POST'])
@web_exception_handler
def hello():
    logger.info('hello, hello, 测试接口')
    logger.info('cookie {}'.format(request.cookies))

    print('hello, hello, 测试接口')
    return Response(json.dumps({'msg': 'hello', 'status': 0, 'data': {}}), mimetype='application/json', status=200)


@app.route('/get_cookie')
def get_cookie():
    name = request.cookies.get('Name')
    return name


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=11111)
