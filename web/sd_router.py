from flask import Flask, Response, request
from utils.log import get_logger
from utils.decorator import web_exception_handler
from flask import Blueprint
from service.user_service import *
import requests
import json
from datetime import datetime
from service import vision_service



session_obj = requests.session()

logger = get_logger('./log/server.log')

sd_router = Blueprint('sd_router', __name__, template_folder='templates')

@sd_router.route('/vision/getUndoTask', methods=['POST', 'GET'])
@web_exception_handler
def get_undo_task():
    res_list_p = vision_service.get_undo_task_service()
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': res_list_p}, ensure_ascii=False),
                    mimetype='application/json',
                    status=200)


@sd_router.route('/vision/collectResult', methods=['POST', 'GET'])
@web_exception_handler
def collect_result():
    task_id = request.form['task_id']
    data = request.files
    file = data['image']
    vision_service.collect_result_service(file, task_id)
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}, ensure_ascii=False),
                    mimetype='application/json',
                    status=200)

@sd_router.route('/vision/submitTask', methods=['POST', 'GET'])
@web_exception_handler
def submit_task():
    param_dict = request.get_json()
    logger.info("submit_task: {}".format(param_dict))
    user_name = param_dict['user_name']
    cookie_user_name = request.cookies.get('Name', None)
    isOk, msg = vision_service.check_username(user_name, cookie_user_name)
    logger.info("用户验证结果:{}, {}".format(isOk, msg))
    if not isOk:
        return Response(json.dumps({'msg': msg, 'status': 1, 'data': {}}, ensure_ascii=False),
                        mimetype='application/json',
                        status=200)
    task_id = vision_service.submit_task_service(user_name, param_dict)
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {"task_id":task_id}}, ensure_ascii=False), mimetype='application/json',
                    status=200)

## 查看任务结果
@sd_router.route('/vision/getTaskResult', methods=['POST', 'GET'])
@web_exception_handler
def get_task_result():
    param_dict = request.get_json()
    # logger.info("get_task_result: {}".format(param_dict))
    user_name = param_dict['user_name']
    task_id = param_dict['task_id']
    res_list = vision_service.get_task_result_service(user_name, task_id)
    if len(res_list) == 0:
        return Response(json.dumps({'msg': '任务不存在', 'status': 2, 'data': {}}, ensure_ascii=False), mimetype='application/json',
                    status=200)
    if res_list[0][4] == 0 or res_list[0][4] == 1:
        return Response(json.dumps({'msg': '您的任务在执行中，请耐心等待', 'status': 1, 'data': {}}, ensure_ascii=False),
                        mimetype='application/json',
                        status=200)
    if res_list[0][4] == -1:
        return Response(json.dumps({'msg': '您的任务执行失败或已超时', 'status': 2, 'data': {}}, ensure_ascii=False),
                        mimetype='application/json',
                        status=200)
    if res_list[0][4] == 2:
        return Response(json.dumps({'msg': '任务完成', 'status': 0, 'data': {'img': res_list[0][3]}}, ensure_ascii=False), mimetype='application/json',
                    status=200)

##  列表页查询
@sd_router.route('/vision/myTaskList', methods=['POST', 'GET'])
@web_exception_handler
def my_task_list():
    param_dict = request.get_json()
    logger.info("task_list_query: {}".format(param_dict))
    user_name = param_dict['user_name']
    res_list_p = vision_service.my_task_list_service(user_name)
    logger.info("task_list_query_res:{}".format(res_list_p))
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': res_list_p}, ensure_ascii=False),
                    mimetype='application/json', status=200)

