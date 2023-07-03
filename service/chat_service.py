from utils.log import get_logger
import time
import threading
import uuid

logger = get_logger('./log/chat.log')


class ChatDataSourceStrategy:
    def __init__(self):
        self.chat_conversations = {}
        self.th = threading.Thread(target=self.run)

    def run(self):
        while True:
            try:
                now_time = time.time()
                user_name_deletes = []

                for user_name, source_dicts in self.chat_conversations.items():
                    delete_flag = True

                    sources_detect = []
                    for source, conversation_info in source_dicts:
                        conversation_time = conversation_info["time"]
                        if now_time - conversation_time > 600:
                            sources_detect.append(source)
                        else:
                            delete_flag = False

                    for d in sources_detect:
                        del source_dicts[d]

                    if delete_flag:
                        user_name_deletes.append(user_name)

                for d in user_name_deletes:
                    logger.info("delete user_name: {}".format(d))
                    del self.chat_conversations[d]

                time.sleep(10)
            except BaseException as e:
                logger.error(e)

    def refresh_ttl(self, user_name, source):
        if user_name not in self.chat_conversations or source not in self.chat_conversations[user_name]:
            return

        self.chat_conversations[user_name][source]["time"] = time.time()

    def delete_user_source_conversation(self, source, user_name):
        if user_name not in self.chat_conversations:
            return

        if source not in self.chat_conversations:
            return

        del self.chat_conversations[user_name][source]

    def user_add_msg(self, source, user_name, msg):
        if user_name not in self.chat_conversations:
            self.chat_conversations[user_name] = {}

        if source not in self.chat_conversations[user_name]:
            self.chat_conversations[user_name][source] = {"time": time.time()}

        self.chat_conversations[user_name][source]["conversation"].append({"type": "user", "msg": msg})
        self.refresh_ttl(user_name, source)

        return len(self.chat_conversations[user_name][source]) - 1

    def fetch_robot_msg(self, source, user_name, index):
        if user_name not in self.chat_conversations or source not in self.chat_conversations[user_name]:
            return -1, ""

        self.refresh_ttl(user_name, source)
        now_index = index
        while now_index < self.chat_conversations[user_name][source]["conversation"]:
            if self.chat_conversations[user_name][source][now_index]["type"] == "robot":
                return now_index + 1, self.chat_conversations[user_name][source]["conversation"][now_index]["msg"]

        return -1, ""

    def fetch_conversation(self, source, user_name, index):
        self.refresh_ttl(user_name, source)
        return self.chat_conversations[user_name][source][: index + 1]

    def robot_add_msg(self, source, user_name, msg):
        if user_name not in self.chat_conversations or source not in self.chat_conversations[user_name]:
            return

        self.refresh_ttl(user_name, source)
        self.chat_conversations[user_name][source].append({"type": "robot", "msg": msg})


class ChatTaskStrategy:
    def __init__(self):
        self.tasks = {}
        self.user_tasks = {}
        self.robot_msg_tasks = {}
        self.sources_task = {}
        self.user_task_ttl = {}

    def add_task(self, source, user_name, msg_index):
        task_id = uuid.uuid1()
        self.tasks[task_id] = {"user_name": user_name, "source": source, "index": msg_index}
        self.user_tasks[user_name + "_" + source] = task_id

        if source not in self.sources_task:
            self.sources_task[source] = []
        self.sources_task[source].append(task_id)

    def delete_task(self, source, user_name):
        if user_name + "_" + source not in self.user_tasks:
            return
        task_ids = self.user_tasks[user_name + "_" + source]
        del self.user_tasks[user_name + "_" + source]

        if user_name + "_" + source in self.robot_msg_tasks:
            del self.robot_msg_tasks[user_name + "_" + source]

        for task_id in task_ids:
            if task_id not in self.tasks:
                return
            del self.tasks[task_id]

    def fetch_robot_msg_index(self, source, user_name):
        if user_name + "_" + source not in self.robot_msg_tasks:
            return 0

        return self.robot_msg_tasks[user_name + "_" + source]

    def set_robot_msg_index(self, source, user_name, index):
        self.robot_msg_tasks[user_name + "_" + source] = index

    def get_new_task(self, source):
        if len(self.sources_task[source]) == 0:
            return False, None, None, None, None

        task_id = self.sources_task[source][0]
        task_info = self.tasks[task_id]

        return True, task_info["user_name"], task_info["source"], task_info["index"], task_id

    def finish_task(self, task_id):
        if task_id not in self.tasks:
            return
        user_name = self.tasks[task_id]["user_name"]
        source = self.tasks[task_id]["source"]
        del self.tasks[task_id]

        if user_name + "_" + source not in self.user_tasks:
            return

        i = self.user_tasks[user_name + "_" + source].index(task_id)
        del self.user_tasks[user_name + "_" + source][i]

    def fetch_task_info(self, task_id):
        if task_id not in self.tasks:
            return False, "", ""
        return True, self.user_tasks[task_id]["user_name"], self.user_tasks[task_id]["source"]


def init():
    global chat_data_source_strategy, chat_task_strategy
    chat_data_source_strategy = ChatDataSourceStrategy()
    chat_task_strategy = ChatTaskStrategy()


init()


def chat_refresh(source, user_name):
    chat_data_source_strategy.delete_user_source_conversation(source, user_name)
    chat_task_strategy.delete_task(source, user_name)


def chat_send_msg(source, user_name, msg):
    msg_index = chat_data_source_strategy.user_add_msg(source, user_name, msg)
    chat_task_strategy.add_task(source, user_name, msg_index)


def chat_receive_msg(source, user_name):
    index = chat_task_strategy.fetch_robot_msg_index(source, user_name)
    if index == -1:
        return False, ""

    next_index, msg = chat_data_source_strategy.fetch_robot_msg(source, user_name, index)
    if next_index == -1:
        return False, msg

    chat_task_strategy.set_robot_msg_index(source, user_name, next_index)

    return True, msg


def chat_fetch_task(source):
    f, source, user_name, msg_index, task_id = chat_task_strategy.get_new_task(source)
    conversation = chat_data_source_strategy.fetch_conversation(source, user_name, msg_index)

    return f, conversation, task_id


def chat_reply_task(source, task_id, recv_msg):
    f, source, user_name = chat_task_strategy.fetch_task_info(task_id)
    if not f:
        return

    chat_task_strategy.finish_task(task_id)
    chat_data_source_strategy.robot_add_msg(source, user_name, recv_msg)
