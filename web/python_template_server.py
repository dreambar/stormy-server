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
from utils.db_manager import dbm

# logger
logger = get_logger('./log/server.log')

app = Flask("python-template-server", static_folder='./static', static_url_path='/vision/')
app.register_blueprint(user_router)

# host = '10.253.209.26'
# port = 33006
# user = 'beta'
# password = 'kVkBhpSVa6!3'
# database = 'fangdao_image_server'
# charset = 'utf8'

sql_dict = {
    "update_status":"update sd_task set status={} where id={}",
    "submit_result":"update sd_task set status=2, content='{}' where id={}",
    "user_used_count":"select count(1) from sd_task where user_name='{}' and TO_DAYS(create_time) = TO_DAYS(NOW())",
    "has_user":"select * from wp_users where user_login='{}'",
    "submit_task":"insert into sd_task(user_name,param, status) values (%s,%s,%s)",
    "task_list":"select * from sd_task where user_name='{}' order by id desc limit 20",
    "task_query":"select * from sd_task where user_name='{}' and id={}",
    "get_undo_task":"select * from sd_task where status=0 order by id limit 1"
}


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


@app.route('/vision/getUndoTask', methods=['POST', 'GET'])
@web_exception_handler
def get_undo_task():
    res_list = dbm.query(sql_dict["get_undo_task"])
    res_list_p = []
    ##这里要处理风格和prompt前后对应的部分的逻辑
    for res in res_list:
        res_p = [res[0], res[1], res[2], res[3], res[4], res[5].strftime("%Y-%m-%d %H:%M:%S"),
                 res[6].strftime("%Y-%m-%d %H:%M:%S")]
        res_list_p.append(res_p)
    logger.info("undo_task send: {}".format(res_list_p))
    if len(res_list) != 0:
        id = res_list[0][0]
        dbm.update(sql_dict["update_status"].format(1, id))
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': res_list_p}, ensure_ascii=False),
                    mimetype='application/json',
                    status=200)


@app.route('/vision/collectResult', methods=['POST', 'GET'])
@web_exception_handler
def collect_result():
    task_id = request.form['task_id']
    data = request.files
    file = data['image']
    file.save(f"./static/{file.filename}")
    image_url = f"http://aistormy.com/vision/{file.filename}"
    logger.info("collect_result: {}, image_url:{}".format(task_id, image_url))
    dbm.update(sql_dict["submit_result"].format(task_id, image_url))
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


@app.route('/vision/submitTask', methods=['POST', 'GET'])
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
    res = dbm.insert(sql_dict["submit_task"], data)
    print("submit_task_res: {}".format(res))
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}, ensure_ascii=False), mimetype='application/json',
                    status=200)

## 查看任务结果
@app.route('/vision/getTaskResult', methods=['POST', 'GET'])
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
    if res_list[0][4] == -1 or datetime.now() - res_list[0][6] > 600:
        return Response(json.dumps({'msg': '您的任务执行失败或已超时', 'status': 2, 'data': {}}, ensure_ascii=False),
                        mimetype='application/json',
                        status=200)
    if res_list[0][4] == 2:
        return Response(json.dumps({'msg': '任务完成', 'status': 0, 'data': {'img': res_list[0][3]}}, ensure_ascii=False), mimetype='application/json',
                    status=200)

##  列表页查询
@app.route('/vision/myTaskList', methods=['POST', 'GET'])
@web_exception_handler
def my_task_list():
    param_dict = request.get_json()
    logger.info("task_list_query: {}".format(param_dict))
    user_name = param_dict['user_name']
    res_list = dbm.query(sql_dict["task_list"].format(user_name))
    res_list_p = []
    for res in res_list:
        res_p = [res[0], res[1], res[2], res[3], res[4], res[5].strftime("%Y-%m-%d %H:%M:%S"),
                 res[6].strftime("%Y-%m-%d %H:%M:%S")]
        res_list_p.append(res_p)
    logger.info("task_list_query_res:{}".format(res_list_p))
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': res_list_p}, ensure_ascii=False),
                    mimetype='application/json', status=200)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=22222)
