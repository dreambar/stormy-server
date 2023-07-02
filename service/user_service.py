from dao.user_dao import *
from utils.email_tools import *


def user_login(user_name, passwd):
    f = has_user_name(user_name)
    if not f:
        return 1, "no user"

    f = user_login_check(user_name, passwd)
    if not f:
        return 2, "passwd error"

    return 0, ""


def user_register(user_name, passwd, email):
    f = has_user_name(user_name)
    if f:
        return 1, "user_name already used"

    user_register_add(user_name, passwd, email)

    return 0, ""


def user_verify_email(email):
    f = has_email(email)
    if f:
        return 1, "email already used", ""

    code = generate_email_code()
    send_verify_email(email, code)

    return 0, "", code
