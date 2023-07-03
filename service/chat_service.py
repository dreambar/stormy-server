from utils.log import get_logger
import time

logger = get_logger('./log/chat.log')


class UserCHatDataSoure:
    def __init__(self):
        pass


class ChatDataSourceStrategy:
    def __init__(self):
        self.chat_conversations = {}


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

    def delete_user_source_conversation(self, source, user_name):
        pass

    def user_add_msg(self, source, user_name, msg):
        return 0

    def fetch_robot_msg(self, source, user_name, index):
        return ""

    def fetch_conversation(self, source, user_name, index):
        return []

    def robot_add_msg(self, source, user_name, msg):
        return 0


class ChatTaskStrategy:
    def __init__(self):
        pass

    def add_task(self, source, user_name, msg_index):
        pass

    def delete_task(self, source, user_name):
        pass

    def fetch_robot_msg_index(self, source, user_name):
        return 0

    def set_robot_msg_index(self, source, user_name, index):
        pass

    def get_new_task(self, source):
        return None, None, None, None, None

    def add_new_task(self, source, user_name, conversation):
        pass

    def finish_task(self, task_id):
        pass

    def fetch_task_info(self, task_id):
        return None, None


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

    f, msg, next_index = chat_data_source_strategy.fetch_robot_msg(source, user_name, index)
    if f:
        return f, msg

    chat_task_strategy.set_robot_msg_index(source, user_name, next_index)

    return f, msg


def chat_fetch_task(source):
    f, source, user_name, msg_index, task_id = chat_task_strategy.get_new_task(source)
    conversation = chat_data_source_strategy.fetch_conversation(source, user_name, msg_index)

    return f, conversation, task_id


def chat_reply_task(source, task_id, recv_msg):
    source, user_name = chat_task_strategy.fetch_task_info(task_id)
    chat_task_strategy.finish_task(task_id)
    chat_data_source_strategy.robot_add_msg(source, user_name, recv_msg)
