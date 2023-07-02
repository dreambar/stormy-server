from flask import Flask, Response, request
from utils.log import get_logger
from utils.decorator import web_exception_handler
from flask import Blueprint
from service.user_service import *
import requests
import json

logger = get_logger('./log/server.log')

user_router = Blueprint('user_router', __name__, template_folder='templates')


@user_router.route('/user/login', methods=['GET', 'POST'])
@web_exception_handler
def login():
    param_dict = request.get_json()
    logger.info("login params: {}".format(param_dict))
    user_name = param_dict['user_name']
    passwd = param_dict['passwd']
    status, msg = user_login(user_name, passwd)

    logger.info("user_name: {} login: {}".format(user_name, status))

    resp = Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"status": status, "msg": msg}}),
                    mimetype='application/json',
                    status=200)
    resp.headers["Content-Type"] = "application/json;chartset=UTF-8"  # 设置响应头
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'  # 如果有其它方法（delete,put等），断续添加
    resp.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    resp.set_cookie('Name', user_name, max_age=None)

    return resp


@user_router.route('/user/register', methods=['GET', 'POST'])
@web_exception_handler
def register():
    param_dict = request.get_json()
    logger.info("register params: {}".format(param_dict))
    user_name = param_dict['user_name']
    passwd = param_dict['passwd']
    email = param_dict["email"]

    status, msg = user_register(user_name, passwd, email)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"status": status, "msg": msg}}),
                    mimetype='application/json',
                    status=200)


@user_router.route('/user/verify_email_code', methods=['GET', 'POST'])
@web_exception_handler
def verify_email_code():
    param_dict = request.get_json()
    logger.info("verify_email_code params: {}".format(param_dict))
    email = param_dict['email']

    status, msg, code = user_verify_email(email)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"status": status, "code": code, "msg": msg}}),
                    mimetype='application/json',
                    status=200)
