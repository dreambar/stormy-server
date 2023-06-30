# -*- coding: utf-8 -*-

# @Time    : 2019/2/15 下午2:39
# @Author  : gaoqi


import swiftclient


class Swift:
    def __init__(self, user, key, auth_url, container):
        self.user = user
        self.key = key
        self.auth_url = auth_url
        self.swift = None
        self.container = container
        self.view_url = None

        self.init()

    def init(self):
        self.swift = swiftclient.client.Connection(user=self.user, key=self.key, authurl=self.auth_url,
                                                   retry_on_ratelimit=True)
        try:
            self.swift.head_container(self.container)
        except:
            self.swift.put_container(self.container, headers={'x-container-read': '.r:*'})
        self.view_url = self.swift.url

    def get_data_by_url(self, url):
        try:
            object_name = url.split('/')[-1]
            container_name = url.split('/')[-2]
            header, data_stream = self.swift.get_object(container_name, object_name)
        except BaseException as e:
            return None
        return data_stream

    def save_data_stream(self, container_name, object_name, data_stream):
        try:
            self.swift.put_object(container_name, object_name, data_stream)
            return f"{self.view_url}/{container_name}/{object_name}"
        except BaseException as e:
            return None

    def delete_data(self, container_name, object_name):
        try:
            self.swift.delete_object(container_name, object_name)
            return True
        except BaseException as e:
            return False
