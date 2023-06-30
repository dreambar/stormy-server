# -*- coding: utf-8 -*-

# @Time    : 2019/8/27 上午10:30
# @Author  : gaoqi


import hashlib
import requests
import json


class BTalk:

    def __init__(self, url, rbt_name, rbt_passwd):
        self.url = url
        self.rbt_name = rbt_name
        self.rbt_passwd = rbt_passwd

    def get_md5(self, src_str):
        hl = hashlib.md5()
        hl.update(src_str.encode(encoding='utf-8'))
        return hl.hexdigest()

    def get_token(self, to_list, msg_body, passwd):
        plain_txt = ''
        for to_name in to_list:
            plain_txt += to_name
        plain_txt += msg_body
        plain_txt += passwd
        args = self.get_md5(plain_txt)
        token = args[7:23]
        return token

    def send_group_message(self, msg, group_id_list, at_user_list=None, at_user_name_list=None):
        '''
        发送群消息
        :param msg: 需要发送的消息内容
        :param group_id_list: 群id，新建群后找zhuang.hu拿群id
        :param at_user_list: 本次消息需艾特的成员的蜂语英文名
        :param at_user_name_list: 本次消息需要艾特的成员中文名字
        :return:
        '''
        if at_user_list is not None:
            notice_name_list = at_user_list if at_user_name_list is None else at_user_name_list
            for at_name in notice_name_list:
                msg += f' @{at_name}'
        msg_body = {
            'From': self.rbt_name,
            'To': [{'User': group_id} for group_id in group_id_list],
            'Type': 'groupchat',
            'Msg_Type': '1',
            'Body': msg,
            'Token': self.get_token(to_list=group_id_list, msg_body=msg, passwd=self.rbt_passwd),
            'Host': 'ejabhost1',
            'Domain': 'conference.ejabhost1',
            'Extent_Info': json.dumps({'atUserList': at_user_list}) if at_user_list is not None else ''
        }

        response = requests.post(url=self.url, json=msg_body)
        return response.status_code

    def send_message(self, msg, user_list):
        '''
        发送个人消息
        :param user_list: 哪些用户接受消息
        :param msg: 消息内容
        :return:
        '''
        msg_body = {
            'From': self.rbt_name,
            'To': [{'User': user} for user in user_list],
            'Body': msg,
            'Token': self.get_token(to_list=user_list, msg_body=msg, passwd=self.rbt_passwd),
            'Type': 'chat',
            'Host': 'ejabhost1',
            'Domain': '',
            'Extend_Info': json.dumps({'atUserList': user_list}) if user_list is not None else '',
        }

        response = requests.post(url=self.url, json=msg_body)
        return response.status_code


if __name__ == "__main__":
    btalk = BTalk(url="http://btalkim.vip.blibee.com/api/sendmessage", rbt_name="rbt_aishopserver_notice",
                  rbt_passwd="bef1b1cc9ad64a91b29dee225ecf8fe9")
    btalk.send_message("测试", ['qi.gao01'])
    btalk.send_group_message("测试", ['0aad2d778c0000000aad2d778c001000'])
