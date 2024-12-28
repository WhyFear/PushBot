# -*- coding: utf-8 -*-
"""
@author: WhyFear
@software: pycharm
@file: TelegramPushBot.py
@time: 2019/5/5 0005 19:51
@desc: telegram推送底层，交互逻辑写在TelegramBot.py中
"""
import logging
import os

import telegram
from telegram.request import HTTPXRequest

from bottom.PushDatabase import pg_db, User, search

token = os.getenv("TELEGRAM_BOT_TOKEN")

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
        logger.error(f"注册失败: {e}")
        return {"result": False, "message": e}
    finally:
        pg_db.close()

class TelegramPushBot:
    def __init__(self):
        """
        初始化 TelegramPushBot 类，创建 telegram.Bot 对象
        """
        proxy_url = os.getenv("TELEGRAM_PROXY")
        if proxy_url:
            request = HTTPXRequest(proxy_url=proxy_url)
            logger.info(f"Telegram: 使用代理 {proxy_url}")
        else:
            request = None
            logger.info("Telegram: 未使用代理")

        self.bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), request=request)

    def search_chat_id(self, user_uuid) -> str:
        """
        根据用户 UUID 查找对应的 chat_id
        """
        result = search(user_uuid=user_uuid)
        chat_id = None
        if result["is_in_the_database"]:
            chat_id = result["chat_id"]
        return chat_id

    async def push_bot(self, user_uuid, text, desp=None):
        """
        使用 python-telegram-bot 库发送消息到 Telegram

        :param user_uuid: 用户 UUID
        :param text: 消息内容
        :param desp: 消息描述
        """
        try:
            # 异步发送消息
            chat_id = self.search_chat_id(user_uuid)
            await self.bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Telegram: Successfully sent message to {user_uuid}")
            return True
        except Exception as e:
            logger.error(f"Telegram: Error sending message to {user_uuid}: {e}")
            return False
