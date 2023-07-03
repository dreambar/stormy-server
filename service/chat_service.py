from utils.log import get_logger
import time
import threading
import uuid

logger = get_logger('./log/chat.log')


class ChatDataSourceStrategy:
    def __init__(self):
        self.chat_conversations = {}
        self.th = threading.Thread(target=self.run)
        self.th.start()

    def run(self):
        while True:
            try:
                now_time = time.time()
                user_name_deletes = []

                for user_name, source_dicts in self.chat_conversations.items():
                    delete_flag = True

                    sources_detect = []
                    for source, conversation_info in source_dicts.items():
                        conversation_time = conversation_info["time"]
                        if now_time - conversation_time > 600:
                            sources_detect.append(source)
                        else:
                            delete_flag = False

                    for d in sources_detect:
                        del source_dicts[d]

                    if delete_flag:
                        user_name_deletes.append(user_name)

                logger.info("ChatTaskStrategy refresh deletes: {}".format(user_name_deletes))
                for d in user_name_deletes:
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
            logger.info("user_add_msg user_name: {} not in chat_conversations".format(user_name))
            self.chat_conversations[user_name] = {}

        if source not in self.chat_conversations[user_name]:
            logger.info("user_add_msg user_name: {} source: {} not in chat_conversations".format(user_name, source))
            self.chat_conversations[user_name][source] = {"time": time.time(), "conversation": []}

        self.chat_conversations[user_name][source]["conversation"].append({"type": "user", "msg": msg})
        self.refresh_ttl(user_name, source)
        logger.info("user_add_msg user_name: {} source: {} len: {}".format(user_name, source, len(
            self.chat_conversations[user_name][source]["conversation"])))

        return len(self.chat_conversations[user_name][source]) - 1

    def fetch_robot_msg(self, source, user_name, index):
        if user_name not in self.chat_conversations or source not in self.chat_conversations[user_name]:
            return -1, ""

        self.refresh_ttl(user_name, source)
        now_index = index
        while now_index < len(self.chat_conversations[user_name][source]["conversation"]):
            if self.chat_conversations[user_name][source]["conversation"][now_index]["type"] == "robot":
                return now_index + 1, self.chat_conversations[user_name][source]["conversation"][now_index]["msg"]

        return -1, ""

    def fetch_conversation(self, source, user_name, index):
        self.refresh_ttl(user_name, source)
        logger.info("fetch_conversation: {}".format(self.chat_conversations))
        return self.chat_conversations[user_name][source]["conversation"][: index + 1]

    def robot_add_msg(self, source, user_name, msg):
        if user_name not in self.chat_conversations or source not in self.chat_conversations[user_name]:
            return

        self.refresh_ttl(user_name, source)
        self.chat_conversations[user_name][source].append({"type": "robot", "msg": msg})


class ChatTaskStrategy:
    def __init__(self):
        self.tasks = {}
        self.user_tasks = {}
        self.user_task_ttls = {}
        self.sources_task = {}
        self.th = threading.Thread(target=self.run)
        self.th.start()

    def refresh_ttl(self, user_name, source):
        self.user_task_ttls[user_name + "_" + source] = time.time()

    def run(self):
        while True:
            try:
                now_time = time.time()
                deletes = []
                for key, before_time in self.user_task_ttls.items():
                    if now_time - before_time > 600:
                        deletes.append(key)

                logger.info("ChatTaskStrategy refresh deletes: {}".format(deletes))
                for d in deletes:
                    del self.user_task_ttls[d]
                    task_ids = self.user_tasks[d]
                    for task_id in task_ids:
                        if task_id in self.tasks:
                            del self.tasks[task_id]
                        if task_id in self.sources_task:
                            del self.sources_task[task_id]

                    del self.user_tasks[d]
                time.sleep(10)
            except BaseException as e:
                logger.error(e)

    def add_task(self, source, user_name, index):
        self.refresh_ttl(user_name, source)
        task_id = str(uuid.uuid1())
        self.tasks[task_id] = {"user_name": user_name, "source": source, "index": index}
        if user_name + "_" + source not in self.user_tasks:
            self.user_tasks[user_name + "_" + source] = {"task_ids": [task_id], "robot_msg_index": 0}
        else:
            self.user_tasks[user_name + "_" + source]["task_ids"].append(task_id)

        if source not in self.sources_task:
            self.sources_task[source] = []
        self.sources_task[source].append(task_id)
        logger.info("add_task sources_task: {}".format(self.sources_task))

    def delete_task(self, source, user_name):
        self.refresh_ttl(user_name, source)
        if user_name + "_" + source not in self.user_tasks:
            return
        task_ids = self.user_tasks[user_name + "_" + source]["task_ids"]
        del self.user_tasks[user_name + "_" + source]

        for task_id in task_ids:
            if task_id not in self.tasks:
                return
            del self.tasks[task_id]

    def fetch_robot_msg_index(self, source, user_name):
        self.refresh_ttl(user_name, source)
        if user_name + "_" + source not in self.user_tasks:
            return 0

        return self.user_tasks[user_name + "_" + source]["robot_msg_index"]

    def set_robot_msg_index(self, source, user_name, index):
        self.refresh_ttl(user_name, source)
        self.user_tasks[user_name + "_" + source]["robot_msg_index"] = index

    def get_new_task(self, source):
        logger.info("get_new_task: {}".format(self.sources_task))
        if len(self.sources_task[source]) == 0:
            return False, None, None, None, None

        task_id = self.sources_task[source][0]
        task_info = self.tasks[task_id]
        del self.sources_task[source][0]
        logger.info("get_new_task task_id: {}".format(task_id))

        return True, task_info["user_name"], task_info["source"], task_info["index"], task_id

    def finish_task(self, task_id):
        if task_id not in self.tasks:
            return
        user_name = self.tasks[task_id]["user_name"]
        source = self.tasks[task_id]["source"]
        del self.tasks[task_id]

        if user_name + "_" + source not in self.user_tasks:
            return

        i = self.user_tasks[user_name + "_" + source]["task_ids"].index(task_id)
        del self.user_tasks[user_name + "_" + source]["task_ids"][i]

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
