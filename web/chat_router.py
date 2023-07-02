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
    source = requests.form["source"]
    chat_refresh(source)
    return Response(json.dumps({'msg': 'success', 'status': 0}), mimetype='application/json',
                    status=200)


@chat_router.route('/chat/send_msg', methods=['GET', 'POST'])
@web_exception_handler
@check_login_handler
def send_msg():
    source = requests.form["source"]
    send_msg = requests.form["send_msg"]
    user_name = requests.cookies.form["Name"]

    chat_send_msg(source, user_name, send_msg)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}), mimetype='application/json',
                    status=200)


@chat_router.route('/chat/receive_msg', methods=['GET', 'POST'])
@web_exception_handler
@check_login_handler
def receive_msg():
    source = requests.form["source"]
    user_name = requests.cookies.form["Name"]

    chat_receive_msg(source, user_name, send_msg)

    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}), mimetype='application/json',
                    status=200)


@chat_router.route('/chat/fetch_task', methods=['GET', 'POST'])
@web_exception_handler
def fetch_task():
    source = requests.form["source"]

    flag, conversation, task_id = chat_fetch_task(source)

    return Response(json.dumps(
        {'msg': 'success', 'status': 0, 'data': {"flag": flag, "conversation": conversation, "task_id": task_id}}),
        mimetype='application/json',
        status=200)


@chat_router.route('/chat/reply_task', methods=['GET', 'POST'])
@web_exception_handler
def fetch_task():
    source = requests.form["source"]
    task_id = requests.form["task_id"]
    recv_msg = requests.form["recv_msg"]

    chat_reply_task(source, task_id, recv_msg)

    return Response(json.dumps(
        {'msg': 'success', 'status': 0}), mimetype='application/json', status=200)
