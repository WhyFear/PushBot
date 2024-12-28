# -*- coding: utf-8 -*-
"""
@author: WhyFear
@software: pycharm
@file: WeChatPushBot.py
@time: 2019/9/10 0010 16:08
@desc: 企业微信推送底层，只负责推送
"""
import json
import os
import time

import requests
# from dotenv import load_dotenv

from bottom import MyErrors

try:
    from PushDatabase import search
except:
    from .PushDatabase import search

# load_dotenv(encoding='utf-8')  # 读取本地变量
WECHAT_KEY = os.getenv("WECHAT_KEY")
WEBHOOK_URL = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key='
WECOM_URL = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token='
access_token_str = ""
access_token_get_time = time.time()


def push_message(url, post_data):
    status = requests.post(url, data=post_data.encode())
    if json.loads(status.text)["errcode"] == 0:
        return True
    else:
        print(status.text)
        return False


# deprecated
def wecom_push_bot(user_uuid, text, desp=None):
    """
    企业微信群推送机器人
    这个机器人推送的消息只能在企业微信中查看，局限较大。
    """
    is_send = False
    result = search(user_uuid=user_uuid)
    if result["is_in_the_database"]:
        wechat_key = result["wechat_key"]
        if desp:
            send_text = """%s\n%s""" % (text, desp)
        else:
            send_text = text

        url = WEBHOOK_URL + wechat_key
        post_data = """{
            "msgtype": "text",
            "text": {
                "content": "%s"
            }
        }""" % send_text
        is_send = push_message(url, post_data)
    return is_send


async def wecom_app_bot(user_uuid, text, desp=None, to_user="@all"):
    """
    企业微信应用消息机器人，使用微信插件后，可以在微信中收取该bot的消息。
    流程：
    1. 获取access_token，失效时间7200秒。目前消息发送量小，可以在每次发送时获取access_token，后面做定时获取。
    2. 使用post方法发送消息。
    """
    is_send = False
    result = search(user_uuid=user_uuid)
    if result["is_in_the_database"]:
        access_token = get_wecom_access_token(result["wecom_company_id"], result["wecom_secret"])
        if access_token["errcode"] == 0:
            access_token = access_token["access_token"]
            url = WECOM_URL + access_token
            if desp:
                send_text = """%s\n%s""" % (text, desp)
            else:
                send_text = text
            post_data = '''{
                           "touser" : "%s",
                           "msgtype" : "text",
                           "agentid" : %s,
                           "text" : {
                               "content" : "%s"
                           }
                        }''' % (to_user, result["wecom_agent_id"], send_text)
            is_send = push_message(url, post_data)
        else:
            print(access_token)
            is_send = False  # 获取 access_token 失败也应该返回 False
    return is_send


def get_wecom_access_token(wecom_company_id, wecom_secret) -> dict:
    """
    获取access_token,并持久化
    """
    global access_token_str, access_token_get_time
    access_token = dict()
    try:
        if access_token_str == "" or time.time() - access_token_get_time > 7000:  # 7200秒，为了保证可用，设置为7000秒
            access_token_content = requests.get(
                f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_company_id}&corpsecret={wecom_secret}')
            access_token = json.loads(access_token_content.text)
            if access_token["errcode"] == 0:
                access_token_str = access_token["access_token"]
                access_token_get_time = time.time()
            else:
                raise MyErrors.GetWecomAccessTokenErrors
        else:
            access_token["errcode"] = 0
            access_token["access_token"] = access_token_str
    except MyErrors.GetWecomAccessTokenErrors:
        # 不处理，直接返回错误
        pass
    except Exception as e:
        access_token["errcode"] = 1
        access_token["message"] = e
        print(e)
    finally:
        return access_token


def get_user_list(user_uuid) -> list:
    """
    获取企业中所有员工的信息
    :return: list格式，除非正常获取到员工信息，否则直接返回空列表
    """
    user_list = list()
    result = search(user_uuid=user_uuid)
    if result["is_in_the_database"]:
        access_token = get_wecom_access_token(result["wecom_company_id"], result["wecom_secret"])
        if access_token["errcode"] == 0:
            access_token = access_token["access_token"]
            get_user_list_url = "https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?department_id=1&fetch_child=1&access_token=" + access_token
            # 错误处理
            try:
                user_list_content = requests.get(get_user_list_url).content
                user_list_json = json.loads(user_list_content)
                if user_list_json["errcode"] == 0:
                    for user_json in user_list_json["userlist"]:
                        user_list.append(user_json["userid"])
                    return user_list
                else:
                    print(user_list_json["errcode"], " ", user_list_json["errmsg"])
            except Exception as e:
                print(e)
        else:
            print(access_token)
    return user_list
