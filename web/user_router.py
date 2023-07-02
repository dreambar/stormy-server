from flask import Flask, Response, request
from utils.log import get_logger
from utils.decorator import web_exception_handler
from flask import Blueprint
from service.user_service import *
import requests
import json

session_obj = requests.session()

logger = get_logger('./log/server.log')

user_router = Blueprint('user_router', __name__, template_folder='templates')


@user_router.route('/user/login', methods=['GET', 'POST'])
@web_exception_handler
def login():
    user_name = request.form['user_name']
    passwd = request.form['passwd']
    f = user_login(user_name, passwd)
    logger.info("user_name: {} login: {}".format(user_name, f))
    session_obj.cookies.set("Name", user_name)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"flag": f}}), mimetype='application/json',
                    status=200)


@user_router.route('/user/register', methods=['GET', 'POST'])
@web_exception_handler
def register():
    user_name = request.form['user_name']
    passwd = request.form['passwd']
    email = requests.form["email"]

    f, msg = user_register(user_name, passwd, email)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"flag": f, "msg": msg}}),
                    mimetype='application/json',
                    status=200)


@user_router.route('/user/verify_email_code', methods=['GET', 'POST'])
@web_exception_handler
def verify_email_code():
    email = request.form['email']

    f, code = user_verify_email(email)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"flag": f, "code": code}}),
                    mimetype='application/json',
                    status=200)
