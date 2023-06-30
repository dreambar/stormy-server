# -*- coding: utf-8 -*-

# @Time    : 2020/6/9 下午3:04
# @Author  : gaoqi

import json
import sys

from flask import Flask, Response, request

sys.path.append('.')
from utils.log import get_logger
from utils.decorator import web_exception_handler
from utils.db_manager import DBManager
# logger
logger = get_logger('./log/server.log')

app = Flask("python-template-server", static_folder='./static', static_url_path='/vision/')

# host = '10.253.209.26'
# port = 33006
# user = 'beta'
# password = 'kVkBhpSVa6!3'
# database = 'fangdao_image_server'
# charset = 'utf8'

host = '127.0.0.1'
port = 3306
user = 'wordpress'
password = 'wordpress'
database = 'wordpress'
charset = 'utf8'

dbm = DBManager(host=host,port=port,user=user,password=password,database=database,charset=charset)



@app.route('/vision/python/template/hello', methods=['GET', 'POST'])
@web_exception_handler
def hello():

    logger.info('hello, hello, 测试接口')
    logger.info('cookie {}'.format(request.cookies))

    print('hello, hello, 测试接口')
    return Response(json.dumps({'msg': 'hello', 'status': 0, 'data': {}}), mimetype='application/json', status=200)


@app.route('/vision/python/template/example/v1', methods=['POST', 'GET'])
@web_exception_handler
def example_v1():
    param = request.get_json()
    # do anything here
    return Response(json.dumps({'msg': 'success', 'status': 200, 'data': {}}),
                    mimetype='application/json', status=200)



@app.route('/get_cookie')
def get_cookie():
    name=request.cookies.get('Name')
    return name


@app.route('/vision/getUndoTask', methods=['POST', 'GET'])
@web_exception_handler
def get_undo_task():
    sql = "select * from sd_task where status=0 order by id limit 1"
    res_list = dbm.query(sql)

    res_list_p = []
    for res in res_list:
        res_p = [res[0], res[1], res[2], res[3], res[4], res[5].strftime("%Y-%m-%d %H:%M:%S"),
                 res[6].strftime("%Y-%m-%d %H:%M:%S")]
        res_list_p.append(res_p)

    logger.info("undo_task send: {}".format(res_list_p))
    if len(res_list) != 0:
        id = res_list[0][0]
        sql2 = "update sd_task set status=1 where id={}".format(id)
        dbm.update(sql2)
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': res_list_p}, ensure_ascii=False), mimetype='application/json',
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
    sql = "update sd_task set status=2, content='{}' where id={}".format(image_url, task_id)
    dbm.update(sql)
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}, ensure_ascii=False), mimetype='application/json',
                    status=200)




def check_username(user_name):
    if user_name == "":
        return False, '用户不存在，请先注册'
    sql_check1 = "select * from wp_users where user_login='{}'".format(user_name)
    logger.info(sql_check1)
    res1 = dbm.query(sql_check1)
    logger.info("user_true_check:{}".format(res1))
    if len(res1) == 0:
        return False, '用户不存在，请先注册'
    sql_check2 = "select count(1) from sd_task where user_name='{}' and TO_DAYS(create_time) = TO_DAYS(NOW())".format(user_name)
    res2 = dbm.query(sql_check2)
    logger.info("user_num_check:{}".format(res2))
    if res2[0][0] >= 20:
        return False, '您所使用的用户，今日使用次数已达上限20次, 如需大量使用请联系管理员assassin.creed.wax@gmail.com'
    return True, ""





@app.route('/vision/submitTask', methods=['POST', 'GET'])
@web_exception_handler
def submit_task():
    param_dict = request.get_json()
    logger.info("submit_task: {}".format(param_dict))
    user_name = param_dict['user_name']
    isOk, msg = check_username(user_name)
    logger.info("提交结果:{}, {}".format(isOk, msg))
    if not isOk:
        return Response(json.dumps({'msg': msg, 'status': 1, 'data': {}}, ensure_ascii=False),
                        mimetype='application/json',
                        status=200)

    data = [[user_name, json.dumps(param_dict, ensure_ascii=False), 0]]

    sql = "insert into sd_task(user_name,param, status) values (%s,%s,%s)"
    logger.info("submit_task_sql: {}".format(data))
    dbm.insert(sql, data)
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': {}}, ensure_ascii=False), mimetype='application/json',
                    status=200)


##  列表页查询
@app.route('/vision/myTaskList', methods=['POST', 'GET'])
@web_exception_handler
def my_task_list():
    param_dict = request.get_json()
    logger.info("task_list_query: {}".format(param_dict))
    user_name = param_dict['user_name']
    sql = "select * from sd_task where user_name='{}' order by id desc limit 20".format(user_name)
    res_list = dbm.query(sql)
    res_list_p = []
    for res in res_list:
        res_p = [res[0], res[1], res[2], res[3], res[4], res[5].strftime("%Y-%m-%d %H:%M:%S"), res[6].strftime("%Y-%m-%d %H:%M:%S")]
        res_list_p.append(res_p)
    logger.info("task_list_query_res:{}".format(res_list_p))
    return Response(json.dumps({'msg': 'success', 'status': 0, 'data': res_list_p}, ensure_ascii=False), mimetype='application/json', status=200)




if __name__ == "__main__":
    app.run(host='127.0.0.1', port=11111)
