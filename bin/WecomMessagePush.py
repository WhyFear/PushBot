# -*- coding: utf-8 -*-
"""
@author: Zeng LH
@contact: 893843891@qq.com
@software: pycharm
@file: WecomMessagePush.py
@time: 2021/3/26 0026 19:39
@desc: 向指定用户推送消息
"""
import os
import requests
from dotenv import load_dotenv
from bottom import WeChatPushBot
from bottom.PushDatabase import search

load_dotenv(encoding='utf8')  # 读取本地变量


def get_user_list():
    result = search(user_uuid=os.getenv("MY_UUID"))
    access_token = WeChatPushBot.get_wecom_access_token()
