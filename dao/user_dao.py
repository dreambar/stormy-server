from utils.db_manager import dbm


def has_user_name(user_name):
    sql = "select * from user_info where user_name = '{}'".format(user_name)

    data = dbm.query(sql)

    return len(data) > 0


def user_login_check(user_name, passwd):
    sql = "select * from user_info where user_name = '{}'".format(user_name)
    data = dbm.query(sql)
    user_passwd = data[0][2]

    return user_passwd == passwd


def user_register_add(user_name, passwd, email):
    insert = "insert into user_info(user_name, passwd, email) values(%s, %s, %s)"
    dbm.insert(insert, [[user_name, passwd, email]])


def has_email(email):
    sql = "select * from user_info where email = '{}'".format(email)
    data = dbm.query(sql)

    return len(data) > 0
