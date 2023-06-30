# -*- coding: utf-8 -*-

# @Time    : 2020/11/17 上午11:00
# @Author  : gaoqi


from pyhive import hive
from threading import Lock


class HiveManager:
    def __init__(self, host, port, user, password, database, auth):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.auth = auth
        self.connection = None
        self.cursor = None
        self.lock = Lock()
        self.init_hive()

    def init_hive(self):
        self.connection = hive.Connection(host=self.host, port=self.port, username=self.user, password=self.password,
                                          database=self.database, auth=self.auth)
        self.cursor = self.connection.cursor()

    def close_hive(self):
        self.lock.acquire()
        self.cursor.close()
        self.connection.close()
        self.lock.release()

    def query(self, sql):
        self.lock.acquire()
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        self.lock.release()
        return data

    def create(self, sql):
        self.lock.acquire()
        self.cursor.execute(sql)
        self.lock.release()

    def drop(self, sql):
        self.lock.acquire()
        self.cursor.execute(sql)
        self.lock.release()

