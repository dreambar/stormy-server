from flask import Flask, Response, request
from utils.log import get_logger
from utils.decorator import web_exception_handler
from flask import Blueprint
from service.chat_service import *
import requests
import json
from utils.decorator import check_login_handler

session_obj = requests.session()

logger = get_logger('./log/server.log')

chat_router = Blueprint('chat_router', __name__, template_folder='templates')


@chat_router.route('/chat/sources', methods=['GET', 'POST'])
@web_exception_handler
@check_login_handler
def sources():
    data = ["百川", "chatgpt", "viccuna"]
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"sources": data}}), mimetype='application/json',
                    status=200)


@chat_router.route('/chat/refresh', methods=['GET', 'POST'])
@web_exception_handler
@check_login_handler
def refresh():
    param_dict = request.get_json()
    source = param_dict["source"]
    user_name = param_dict["user_name"]
    chat_refresh(source, user_name)
    return Response(json.dumps({'msg': 'success', 'status': 0}), mimetype='application/json',
                    status=200)


@chat_router.route('/chat/send_msg', methods=['GET', 'POST'])
@web_exception_handler
@check_login_handler
def send_msg():
    param_dict = request.get_json()
    source = param_dict["source"]
    send_msg = param_dict["send_msg"]
    user_name = param_dict["user_name"]

    chat_send_msg(source, user_name, send_msg)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}), mimetype='application/json',
                    status=200)


@chat_router.route('/chat/receive_msg', methods=['GET', 'POST'])
@web_exception_handler
@check_login_handler
def receive_msg():
    param_dict = request.get_json()
    user_name = param_dict["user_name"]
    source = param_dict["source"]

    chat_receive_msg(source, user_name, send_msg)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}), mimetype='application/json',
                    status=200)


@chat_router.route('/chat/fetch_task', methods=['GET', 'POST'])
@web_exception_handler
def fetch_task():
    param_dict = request.get_json()
    source = param_dict["source"]

    flag, conversation, task_id = chat_fetch_task(source)

    return Response(json.dumps(
        {'msg': 'success', 'status': 0, 'data': {"flag": flag, "conversation": conversation, "task_id": task_id}}),
        mimetype='application/json',
        status=200)


@chat_router.route('/chat/reply_task', methods=['GET', 'POST'])
@web_exception_handler
def reply_task():
    param_dict = request.get_json()
    source = param_dict["source"]
    task_id = param_dict["task_id"]
    recv_msg = param_dict["recv_msg"]

    chat_reply_task(source, task_id, recv_msg)

    return Response(json.dumps(
        {'msg': 'success', 'status': 0}), mimetype='application/json', status=200)
