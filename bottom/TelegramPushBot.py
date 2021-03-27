# -*- coding: utf-8 -*-
"""
@author: WhyFear
@software: pycharm
@file: TelegramPushBot.py
@time: 2019/5/5 0005 19:51
@desc: telegram推送底层，交互逻辑写在TelegramBot.py中
"""
import os
import logging
import telegram
from dotenv import load_dotenv

from PushDatabase import pg_db, User, search

load_dotenv(encoding='utf-8')
token = os.getenv("TELEGRAM_BOT_TOKEN")
tele_bot = telegram.Bot(token=token)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def register(user_uuid, chat_id) -> dict:
    user_dict = {"UUID": user_uuid, "telegram": chat_id}
    try:
        pg_db.connect()
        with pg_db.atomic():  # 插入数据
            User.create(**user_dict)
        return {"result": True}
    except Exception as e:
        return {"result": False, "message": e}
    finally:
        pg_db.close()


def push_message(chat_id, text):
    """
    主动向用户推送消息
    :param chat_id: 用户id
    :param text: 推送的消息内容
    :return: no return
    """
    tele_bot.send_message(chat_id=chat_id, text=text)


def push_bot(user_uuid, text, desp=None):
    is_send = False
    result = search(user_uuid=user_uuid)
    if result["is_in_the_database"]:
        chat_id = result["chat_id"]
        if desp:
            send_text = """%s\n%s""" % (text, desp)
        else:
            send_text = text
        push_message(chat_id, send_text)
        is_send = True
    return is_send
