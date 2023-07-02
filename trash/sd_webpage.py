import streamlit as st
import json
import pandas as pd
import requests
from utils.log import get_logger
from streamlit.web.server.websocket_headers import _get_websocket_headers


url_prefix = "http://aistormy.com"
# url_prefix = 'http://127.0.0.1:11111'
submit_task = "/vision/submitTask"
my_task_list = "/vision/myTaskList"

logger = get_logger('./log/sd_ui.log')

def status_mapping(s):
    if s == 0:
        return "待执行"
    elif s == 1:
        return "执行中"
    elif s == 2:
        return "已完成"
    else:
        return "执行失败"

def get_cookie_username():
    if not bool(_get_websocket_headers()):
        return ""
    if _get_websocket_headers().get("Cookie") == "":
        return ""
    cookies = _get_websocket_headers().get("Cookie")
    # cookies = 'wordpress_test_cookie=WP%20Cookie%20check; wp_lang=zh_CN; ajs_anonymous_id=faf56cdb-dfb1-4d92-85b5-48907aec0729; wordpress_logged_in_701d13825842b70eaa1d312570482f15=xt%7C1688442683%7CmWcNA3spK8sUkz9AWcwC8wCyfgMdC3y1vetxG0TRbX9%7C6b6edb51c464b0d950dbbe65ab44d1e2459badb72e963fbc0c0d3013b13afc2e; wp-settings-time-1=1687249546; wp-settings-1=libraryContent%3Dbrowse%26mfold%3Do'
    cookies_list = cookies.split(';')
    logger.info("cookie_list:{}".format(cookies_list))
    for c in cookies_list:
        if c.strip().startswith('wordpress_logged_in_'):
            return c.split('=')[1].split('%')[0]
    return ""

@st.cache_resource()
def load_process_prompt():
    with open('prompt.json', 'r') as prompt_file:
        prompt = json.load(prompt_file)
        return prompt

user_name = get_cookie_username()
prompt_data = load_process_prompt()
print ("user_name:" + user_name)
logger.info("user_name:{}".format(user_name))

def gen_image():

    # print(len(prompt_data))

    model_name = st.selectbox('模型选择', options=['韩国女孩', '动漫风格'])
    # img_num = st.selectbox('一次生成图像数量，最大为4张', options=['1', '2', '3', '4'])

    pos_prompt = st.text_area('正向提示词(需使用英文部分)', '', height=200, max_chars=None)
    neg_prompt = st.text_area('负向提示词(需使用英文部分)', '', height=200, max_chars=None)

    if st.button("生成图片"):
        if len(pos_prompt) == 0:
            st.write('您的输入为空，请输入正向提示词')
        else:
            ## 这个位置需要用cookie或者怎么拿到
            url = url_prefix + submit_task
            param = {'user_name': user_name, 'params' : {'pos_prompt': pos_prompt, 'neg_prompt': neg_prompt, 'model_name':model_name}}
            logger.info("收到生成任务: {}".format(json.dumps(param, ensure_ascii=False)))

            r = requests.post(url, headers={'Connection': 'close', 'Content-Type': 'application/json'}, json=param)
            if r.status_code != 200:
                logger.error('调用失败: {}', json.dumps(param, ensure_ascii=False))
                st.write('图片生成服务调用失败，请联系管理员 assassins.creed.wax@gmail.com ')
            else:
                if r.json()['status'] == 0:
                    st.write('调用成功，稍后请在"我的生成结果中"查看')
                else:
                    st.write(r.json()['msg'])

    head_tab_list = st.tabs(['提示词字典', '我的生成结果'])


    ##提示词树
    with head_tab_list[0]:
        keys = list(prompt_data.keys())
        # print (len(keys))
        print (keys)
        tab_list = st.tabs(keys)

        # print (tab_list)
        for i in range(0, len(keys) - 1):
            with tab_list[i]:
                tab_data = prompt_data[keys[i]]
                origin_prompt_list = []
                desc_list = []
                for p in tab_data:
                    desc_list.append(p['desc'])
                    origin_prompt_list.append(p['origin_prompt'])
                d = pd.DataFrame({
                    "中文": desc_list,
                    "对应提示词": origin_prompt_list
                })
                st.dataframe(d, use_container_width=True, hide_index=True, height=2000)


    ## 任务列表
    with head_tab_list[1]:
        url = url_prefix + my_task_list
        param = {'user_name': user_name}
        print (param)
        r = requests.post(url, headers={'Connection': 'close', 'Content-Type': 'application/json'}, data=json.dumps(param, ensure_ascii=False))
        if r.status_code != 200:
            logger.error('调用失败: {}'.format(json.dumps(param, ensure_ascii=False)))
            st.write('图片生成服务调用失败，请联系管理员 assassins.creed.wax@gmail.com ')
        else:
            st.write('系统只能展示您最近的20次调用结果')

            ret_data = r.json()['data']

            id_list = []
            img_list = []
            status_list = []
            create_time_list = []

            for ret in ret_data:
                id_list.append(ret[0])
                img_list.append(ret[3])
                status_list.append(status_mapping(ret[4]))
                create_time_list.append(ret[6])

            data_df = pd.DataFrame({
                "任务编号": id_list,
                "任务状态": status_list,
                "创建时间": create_time_list,
                "图像结果": img_list
            })
            st.dataframe(
                data_df,
                column_config={
                    "图像结果": st.column_config.ImageColumn()
                },
                hide_index=True,
                use_container_width = True
            )

            # st.header("您最近的{}次任务, 标签为创建时间".format(len(ret_data)))
            # task_tab_list = st.tabs(create_time_list)
            # for i in range(0, len(ret_data) - 1):
            #     with task_tab_list[i]:
            #         st.subheader("任务状态: {}".format(status_mapping(ret_data[i][4])))
            #         if ret_data[i][4] == 2:
            #             for img in ret_data[i][3]:
            #                 st.image(img_data)


st.title("生成你的梦中情人")
gen_image()



