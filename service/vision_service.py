from utils.db_manager import dbm


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