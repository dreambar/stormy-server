import time
import hashlib
import requests
from datetime import datetime, timedelta
import cv2
import numpy as np
import json
from PIL import Image

#这个文件提供了下载：（1）营业门店清单（2）某家门店所有摄像头详情（3）当前摄像头截图（4）历史时刻（保留三个月）摄像头截图
#注：(1)camid的格式是"b_000abc";(2)下大量图时建议开多线程(3)程序问题可以找yanjun.li05

#下载截图所需配置
class BlieyesConf(object):
    app_source = '找yanjun.li05要'
    key = '找yanjun.li05要'
    url_base = 'http://blieyes.blibee.com/api'
    fetch_cam_api = '/v2/common/search_camera_by_store_code'
    snapshot_api = '/v2/high/nvr/fetch_snapshot'
    history_snapshot_api = '/v2/high/nvr/fetch_history_snapshot'
    video_task_api = '/v2/common/create_common_download_task'
    video_status_api = '/v2/common/fetch_common_download_task_by_video_uid'
    video_api = '/v2/common/fetch_download_link_by_video_uid'
    

#返回list形式的当前所有开业门店
def fetch_all_shops():
    url = 'http://supplychain-api.vip.blibee.com/bach/openproduct/api/shop/list/code/v1'
    param = {'typeList': [0], 'businessStateList': [1,2]}
    r = requests.post(url, headers={
                      'Connection': 'close', 'Content-Type': 'application/json'}, data=json.dumps(param))
    if r.status_code != 200:
        logger.error(
            "fetch_all_shops failed! for {} ".format(r.status_code))
        return None

    open_shops = r.json()['data']
    return open_shops

#返回某个shopid对应的摄像头详情
def fetch_cameras(shop_id):
    t = str(int(time.time()))
    hash_str = 'appSource=%s&key=%s&t=%s' % (
        BlieyesConf.app_source, BlieyesConf.key, t)
    sign = hashlib.md5(hash_str.encode('utf8')).hexdigest()

    url = '{}{}?sign={}&t={}&appSource={}&code={}'.format(
        BlieyesConf.url_base,
        BlieyesConf.fetch_cam_api,
        sign,
        t,
        BlieyesConf.app_source,
        shop_id
    )
    r = requests.get(url)
    cam_data = r.json()['data']
    return cam_data

#返回历史时刻的截图信息。输入date_time的格式是：20201018110101，详情见天眼API
def fetch_history_snapshot(shop_id, camera_id, date_time):
    t = str(int(time.time()))
    hash_str = 'appSource=%s&key=%s&t=%s' % (
        BlieyesConf.app_source, BlieyesConf.key, t)
    sign = hashlib.md5(hash_str.encode('utf8')).hexdigest()
    url = '{}{}?sign={}&t={}&appSource={}&store_code={}&camera_code={}&at={}'.format(
        BlieyesConf.url_base,
        BlieyesConf.history_snapshot_api,
        sign,
        t,
        BlieyesConf.app_source,
        shop_id,
        camera_id,
        date_time
    )
    r = requests.get(url)
    if r.status_code != 200:
        return None
    pic_bytes = r.content
    img = np.asarray(bytearray(pic_bytes), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    return img

#给图绘框
def draw_pic(img,boxes):
    for box in boxes:
        img = cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)

#从bid获取nid
def get_nid_from_shopid_bid(shop_id,bid):
    t = str(int(time.time()))
    hash_str = 'appSource=%s&key=%s&t=%s' % (
        BlieyesConf.app_source, BlieyesConf.key, t)
    sign = hashlib.md5(hash_str.encode('utf8')).hexdigest()

    url = '{}{}?sign={}&t={}&appSource={}&code={}'.format(
        BlieyesConf.url_base,
        BlieyesConf.fetch_cam_api,
        sign,
        t,
        BlieyesConf.app_source,
        shop_id
    )
    r = requests.get(url)
    cam_data = r.json()['data']
    for item in cam_data:
        if(item['code'] == bid):
            return item['id_via_ip']
    
    return None

#通过工单ID查询工单详情
def queryFlowOrder(flow_order_id):
    url = 'http://ripple-open-api.vip.blibee.com'
    location2 = '/ripple/flow/open/query/flow_order/v1'
    data = {'flowOrderId':flow_order_id,'targetSections':'flow-main,flow-form,flow-task'}
    response = requests.get(url+location2,params=data)
    return json.loads(response.text)