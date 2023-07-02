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





sql_dict = {
    "update_status":"update sd_task set status={} where id={}",
    "submit_result":"update sd_task set status=2, content='{}' where id={}",
    "user_used_count":"select count(1) from sd_task where user_name='{}' and TO_DAYS(create_time) = TO_DAYS(NOW())",
    "has_user":"select * from wp_users where user_login='{}'",
    "submit_task":"insert into sd_task(user_name,param, status) values (%s,%s,%s)",
    "task_list":"select * from sd_task where user_name='{}' order by id desc limit 20",
    "task_query":"select * from sd_task where user_name='{}' and id={}",
    "get_undo_task":"select * from sd_task where status=0 order by id limit 1",
    "my_last_task":"select * from sd_task where user_name='{}' order by id desc limit 1"
}


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


##这个部分后续check cookie
def check_username(user_name):

    # if user_name == "":
    #     return False, '用户不存在，请先注册'
    # res1 = dbm.query(sql_dict["has_user"].format(user_name))
    # logger.info("user_true_check:{}".format(res1))
    # if len(res1) == 0:
    #     return False, '用户不存在，请先注册'
    # res2 = dbm.query(sql_dict["user_used_count"].format(user_name))
    # logger.info("user_num_check:{}".format(res2))
    # if res2[0][0] >= 20:
    #     return False, '您所使用的用户，今日使用次数已达上限20次, 如需大量使用请联系管理员aistormy2049@gmail.com'
    return True, ""


@sd_router.route('/vision/submitTask', methods=['POST', 'GET'])
@web_exception_handler
def submit_task():
    param_dict = request.get_json()
    logger.info("submit_task: {}".format(param_dict))
    user_name = param_dict['user_name']
    isOk, msg = check_username(user_name)
    logger.info("用户验证结果:{}, {}".format(isOk, msg))
    if not isOk:
        return Response(json.dumps({'msg': msg, 'status': 1, 'data': {}}, ensure_ascii=False),
                        mimetype='application/json',
                        status=200)
    data = [[user_name, json.dumps(param_dict, ensure_ascii=False), 0]]
    logger.info("submit_task_sql: {}".format(data))
    dbm.insert(sql_dict["submit_task"], data)
    res_list = dbm.query(sql_dict["my_last_task"].format(user_name))
    task_id = res_list[0][0]
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
    res_list = dbm.query(sql_dict["task_query"].format(user_name, task_id))
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
    res_list = dbm.query(sql_dict["task_list"].format(user_name))
    res_list_p = []
    for res in res_list:
        res_p = {"task_id":res[0], "user_name": res[1], "param":res[2], "content": res[3], "status":res[4],"update_time":res[5].strftime("%Y-%m-%d %H:%M:%S"),
                 "create_time":res[6].strftime("%Y-%m-%d %H:%M:%S")}
        res_list_p.append(res_p)
    logger.info("task_list_query_res:{}".format(res_list_p))
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': res_list_p}, ensure_ascii=False),
                    mimetype='application/json', status=200)

