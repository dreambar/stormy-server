from utils.db_manager import dbm
import json


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

def get_undo_task_service():
    res_list = dbm.query(sql_dict["get_undo_task"])
    res_list_p = []
    ##这里要处理风格和prompt前后对应的部分的逻辑
    for res in res_list:
        res_p = [res[0], res[1], res[2], res[3], res[4], res[5].strftime("%Y-%m-%d %H:%M:%S"),
                 res[6].strftime("%Y-%m-%d %H:%M:%S")]
        res_list_p.append(res_p)
    # logger.info("undo_task send: {}".format(res_list_p))
    if len(res_list) != 0:
        id = res_list[0][0]
        dbm.update(sql_dict["update_status"].format(1, id))
    return res_list_p

def collect_result_service(file, task_id):
    file.save(f"./static/{file.filename}")
    image_url = f"http://aistormy.com/vision/{file.filename}"
    # logger.info("collect_result: {}, image_url:{}".format(task_id, image_url))
    dbm.update(sql_dict["submit_result"].format(task_id, image_url))


def submit_task_service(user_name, param_dict):
    data = [[user_name, json.dumps(param_dict, ensure_ascii=False), 0]]
    # logger.info("submit_task_sql: {}".format(data))
    dbm.insert(sql_dict["submit_task"], data)
    res_list = dbm.query(sql_dict["my_last_task"].format(user_name))
    task_id = res_list[0][0]
    return task_id


def my_task_list_service(user_name):
    res_list = dbm.query(sql_dict["task_list"].format(user_name))
    res_list_p = []
    for res in res_list:
        params = json.loads(json.loads(res[2])["params"])
        res_p = {
            "task_id":res[0], 
            "user_name": res[1],
            "pos_prompt":params["pos_prompt"],
            "neg_prompt":params["neg_prompt"],
            "style":res[2]["style"],
            "img": res[3], 
            "status":res[4],
            "create_time":res[6].strftime("%Y-%m-%d %H:%M:%S")
            }
        res_list_p.append(res_p)
    return res_list_p

def get_task_result_service(user_name, task_id):
    return dbm.query(sql_dict["task_query"].format(user_name, task_id))