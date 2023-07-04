from utils.db_manager import dbm
import json
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from utils.log import get_logger

import oss2
import os
# 阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户。
auth = oss2.Auth('LTAI5tRAbpW9MNjDDnDAVCsq', '7RguIff46JiTrh43HkULgbXZPiIVqu')
# yourEndpoint填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
# 填写Bucket名称。
bucket = oss2.Bucket(auth, 'oss-ap-southeast-1.aliyuncs.com', 'aistormy2023')
oss_url_prefix = "https://aistormy2023.oss-ap-southeast-1.aliyuncs.com/"

logger = get_logger('./log/server.log')

pool = ThreadPoolExecutor(10)

sql_dict = {
    "update_status":"update sd_task set status={} where id={}",
    "submit_result":"update sd_task set status=2, content='{}' where id={}",
    "user_used_count":"select count(1) from sd_task where user_name='{}' and TO_DAYS(create_time) = TO_DAYS(NOW())",
    "has_user":"select * from wp_users where user_login='{}'",
    "submit_task":"insert into sd_task(user_name,param, status) values (%s,%s,%s)",
    "task_list":"select * from sd_task where user_name='{}' order by id desc limit 20",
    "task_query":"select * from sd_task where user_name='{}' and id={}",
    "get_undo_task":"select * from sd_task where status=0 order by id limit 1",
    "my_last_task":"select * from sd_task where user_name='{}' order by id desc limit 1"
}

##这个部分后续check cookie
def check_username(user_name):

    # if user_name == "":
    #     return False, '用户不存在，请先注册'
    # res1 = dbm.query(sql_dict["has_user"].format(user_name))
    # logger.info("user_true_check:{}".format(res1))
    # if len(res1) == 0:
    #     return False, '用户不存在，请先注册'
    # res2 = dbm.query(sql_dict["user_used_count"].format(user_name))
    # logger.info("user_num_check:{}".format(res2))
    # if res2[0][0] >= 20:
    #     return False, '您所使用的用户，今日使用次数已达上限20次, 如需大量使用请联系管理员aistormy2049@gmail.com'
    return True, ""

pos_prompt_dict = {
    "default":"8k photo, RAW photo, best quality, masterpiece, photorealistic, ultra high res, intricate detail, Exquisite details and textures, physically-based rendering, award winning photography,film granularity, huge_filesize, golden ratio，CG, unity, 2k wallpaper, Amazing, official art, beautiful detailed nose, beautiful detailed eyes, extremely detailed eyes and face, one lady ",
    "jpf":"<lora:FilmVelvia2:1.3>,(film grain:1.5),(analog film style:1.5), vivid color,(grainy, dimly lit:1.3), (masterpiece:1.2), best quality, high quality, (realistic), (absurdres:1.2), UHD, ultrarealistic,  portrait, full body, slim, detail face, perfect body,best illumination, professional lighting,foggy, Chromatic Aberration, ((best quality)), ((masterpiece)), ((realistic)), radiant light rays, highres, analog style, realism",
    "hgmn":"8k photo, RAW photo, best quality, masterpiece, photorealistic, ultra high res, intricate detail, Exquisite details and textures, physically-based rendering, award winning photography,film granularity, huge_filesize, golden ratio，CG, unity, 2k wallpaper, Amazing, official art,a korean beauty,beautiful detailed nose, beautiful detailed eyes, extremely detailed eyes and face",
    "jxj":"complex 3d render ultra detailed of a beautiful porcelain profile woman android face, cyborg, robotic parts, 150 mm, beautiful studio soft light, rim light, vibrant details, luxurious cyberpunk, lace, hyperrealistic, anatomical, facial muscles, cable electric wires, microchip, elegant, beautiful background, octane render, H. R. Giger style, 8k, best quality, masterpiece, illustration, an extremely delicate and beautiful, extremely detailed ,CG ,unity ,wallpaper, (realistic, photo-realistic:1.37),Amazing, finely detail, masterpiece,best quality,official art, extremely detailed CG unity 8k wallpaper, absurdres, incredibly absurdres, robot, silver halmet, <lora:JapaneseDollLikeness_v15:0.2> <lora:koreanDollLikeness:0.2>,(full body:1.2)",
    "sbj":"8k photo, RAW photo, best quality, masterpiece, photorealistic, ultra high res, intricate detail, Exquisite details and textures, physically-based rendering, award winning photography,film granularity, huge_filesize, golden ratio，CG, unity, 2k wallpaper, Amazing, official art,best illumination, professional lighting, beautiful detailed nose, beautiful detailed eyes, extremely detailed eyes and face,portrait, full body, slim, detail face, perfect body, stunning lady, perfect anatomy, realistic skin, beautiful thighs, big eyes, underboob,extremely delicate and beautiful, beautiful detailed nose, beautiful detailed eyes, extremely detailed eyes and face, large breast, (full body:1.5)",
    "jsjj":"8k photo, RAW photo, best quality, masterpiece, photorealistic, ultra high res, intricate detail, Exquisite details and textures, physically-based rendering, award winning photography,film granularity, huge_filesize, golden ratio，CG, unity, 2k wallpaper, Amazing, official art,a korean beauty,beautiful detailed nose, beautiful detailed eyes, extremely detailed eyes and face, <lora:JapaneseDollLikeness_v15:0.2> <lora:koreanDollLikeness:0.2>,(sexy teacher:1.4)(office lady:1.8),full body, (blackboard:1.2), (classroom:1.2), beautiful detailed nose, beautiful detailed eyes, extremely detailed eyes and face"
}


neg_normal_text = "EasyNegative,(worst quality:2), (low quality:2), (normal quality:2), lowres,easynegative, two spaces, watermark, DeepNegative, jpeg artifacts,heavy body, bad, fat body, small hip, muscles, (4legs:1.5), (3legs:1.5), (2faces:1.5), (collected legs:1.5), (foot:2), bad legs, thick thighs, bad thighs,(Wrinkles:1.8), (short legs:1.8), extra digit, fewer digits, extra fingers, fewer digits, extra limbs,skin spots, acnes, skin blemishes, missing fingers, blurry,bad feet,cropped,poorly drawn hands,poorly drawn face,mutation,deformed, fused fingers,too many fingers,long neck,cross-eyed,mutated hands,polar lowres,bad body,bad proportions,gross proportions,text,error,missing fingers,missing arms,missing legs, age spot, glans, username,bad composition, deformed body features,paintings, sketches, grayscale, monochrome"


def style_add_detail(params):
    
    style = params["style"]
    if style == "jpf":
        params["pos_prompt"] = params["pos_prompt"]+","+ pos_prompt_dict["jpf"]
        params["neg_prompt"] = neg_normal_text
        params["sampler"] = "DPM++ SDE Karras"
        params["step"] = 20
    elif style == "hgmn":
        params["pos_prompt"] = params["pos_prompt"]+","+ pos_prompt_dict["hgmn"]
        params["neg_prompt"] = neg_normal_text
        params["sampler"] = "DPM++ SDE Karras"
        params["step"] = 20
    elif style == "jxj":
        params["pos_prompt"] = params["pos_prompt"]+","+ pos_prompt_dict["jxj"]
        params["neg_prompt"] = neg_normal_text
        params["sampler"] = "DPM++ SDE Karras"
        params["step"] = 33
    elif style == "sbj":
        params["pos_prompt"] = params["pos_prompt"]+","+ pos_prompt_dict["sbj"]
        params["neg_prompt"] = neg_normal_text
        params["sampler"] = "DPM++ SDE Karras"
        params["step"] = 20
    elif style == "jsjj":
        params["pos_prompt"] = params["pos_prompt"]+","+ pos_prompt_dict["sbj"]
        params["neg_prompt"] = neg_normal_text
        params["sampler"] = "DPM++ SDE Karras"
        params["step"] = 20
    else:
        params["pos_prompt"] = params["pos_prompt"]+","+ pos_prompt_dict["default"]
        params["neg_prompt"] = neg_normal_text
        params["sampler"] = "DPM++ SDE Karras"
        params["step"] = 20
    return params


def style_add(res_list):
    res_list_p = []
    logger.info("get_undo_task, res = {}".format(res_list))
    for res in res_list:
        params = style_add_detail(json.loads(res[2])["params"])
        res_p = [res[0], res[1], json.dumps(params, ensure_ascii=False), res[3], res[4], res[5].strftime("%Y-%m-%d %H:%M:%S"),
                 res[6].strftime("%Y-%m-%d %H:%M:%S")]
        res_list_p.append(res_p)
    logger.info("get_undo_task, res_p = {}".format(res_list_p))
    return res_list_p
    

def get_undo_task_service():
    res_list = dbm.query(sql_dict["get_undo_task"])
    if len(res_list) != 0:
        id = res_list[0][0]
        dbm.update(sql_dict["update_status"].format(1, id))
    return style_add(res_list)


def generate_thumbnail(file_name, content):
    img = Image.open(BytesIO(content))
    # img = img.convert('RGB')
    fn_jpg = file_name.split('.')[0] + ".jpg"
    with BytesIO() as out:
        img.save(out, quality=50, format="jpeg")
        bucket.put_object(fn_jpg, out.getvalue())


def collect_result_service(file, task_id):
    # file.save(f"./static/{file.filename}")
    # logger.info("collect_result: {}, image_url:{}".format(task_id, image_url))
    f= file.read()
    bucket.put_object(file.filename, f)
    image_url = oss_url_prefix + file.filename
    dbm.update(sql_dict["submit_result"].format(image_url, task_id))
    pool.submit(generate_thumbnail, file.filename, f)



def submit_task_service(user_name, param_dict):
    data = [[user_name, json.dumps(param_dict, ensure_ascii=False), 0]]
    # logger.info("submit_task_sql: {}".format(data))
    dbm.insert(sql_dict["submit_task"], data)
    res_list = dbm.query(sql_dict["my_last_task"].format(user_name))
    task_id = res_list[0][0]
    return task_id


def my_task_list_service(user_name):
    res_list = dbm.query(sql_dict["task_list"].format(user_name))
    res_list_p = []
    for res in res_list:
        params = json.loads(res[2])["params"]
        res_p = {
            "task_id":res[0], 
            "user_name": res[1],
            "pos_prompt":params["pos_prompt"],
            "neg_prompt":params["neg_prompt"],
            "style":params["style"],
            "img": res[3], 
            "status":res[4],
            "create_time":res[6].strftime("%Y-%m-%d %H:%M:%S")
            }
        res_list_p.append(res_p)
    return res_list_p

def get_task_result_service(user_name, task_id):
    return dbm.query(sql_dict["task_query"].format(user_name, task_id))