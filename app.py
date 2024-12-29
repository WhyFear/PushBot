# -*- coding: utf-8 -*-
"""
@author: WhyFear
@software: pycharm
@file: Main.py
@time: 2019/5/5 0005 17:05
@desc:
"""
import asyncio
import logging

from flask import Flask, request, jsonify

from bottom import WeChatPushBot
from bottom.TelegramPushBot import TelegramPushBot as tpb

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)


class MessageSender:
    """
    消息发送器基类
    """

    async def send(self, message):
        raise NotImplementedError


class TelegramMessageSender(MessageSender):
    """
    Telegram 消息发送器
    """

    def __init__(self):
        """
        :param self: TelegramMessageSender 对象
        :return: 无
        :rtype: None
        :desc: 初始化 TelegramMessageSender 对象
        """
        self.telegram_bot = tpb()

    async def send(self, message):
        """
        Sends a message to a Telegram user using the Telegram bot.

        :param message: A dictionary containing the message details with keys:
                        - "UUID": User UUID
                        - "text": Message content
                        - "desp": (optional) Message description
        :return: A tuple (is_send, error) where:
                - is_send: True if the message was sent successfully, False otherwise
                - error: None if successful, or an error message if an exception occurred
        """
        try:
            # 使用 asyncio.create_task 提交 push_bot 任务到事件循环中，并使用 await 等待任务完成
            is_send = await asyncio.create_task(
                self.telegram_bot.push_bot(message["UUID"], message["text"], message.get("desp"))
            )
            if is_send:
                logger.info(f"Telegram 消息发送成功: {message}")
            else:
                logger.warning(f"Telegram 消息发送失败: {message}")
            return is_send, None
        except Exception as e:
            logger.exception(f"Telegram 消息发送失败: {message}, 错误: {e}")
            return False, f"Telegram 消息发送失败: {e}"


class WeChatMessageSender(MessageSender):
    """
    WeChat 消息发送器
    """

    async def send(self, message):
        try:
            is_send = await asyncio.wait_for(
                WeChatPushBot.wecom_app_bot(message["UUID"], message["text"], message.get("desp")), timeout=TIMEOUT)
            if is_send:
                logger.info(f"WeChat 消息发送成功: {message}")
                return True, None  # 发送成功，返回 (True, None)
            else:
                logger.warning(f"WeChat 消息发送失败: {message}")
                return False, "WeChat消息发送失败, 未知错误"  # 发送失败返回错误信息
        except asyncio.TimeoutError:
            logger.error(f"WeChat消息发送超时: {message}")
            return False, "WeChat消息发送超时"
        except Exception as e:
            logger.exception(f"WeChat 消息发送失败: {message}, 错误: {e}")
            return False, f"WeChat 消息发送失败: {e}"


class AllMessageSender(MessageSender):
    """
    同时发送所有已注册的消息
    """

    async def send(self, message):
        tasks = [sender().send(message) for sender in MessageSenderFactory.get_all_senders()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results


class MessageSenderFactory:
    """
    消息发送器工厂类
    """
    _senders = {}

    @classmethod
    def register_sender(cls, name, sender_class):
        """
        注册消息发送器
        """
        cls._senders[name] = sender_class

    @classmethod
    def get_sender(cls, name):
        """
        获取消息发送器
        """
        if name == "all" or not name:
            return AllMessageSender()

        sender_class = cls._senders.get(name)
        if sender_class:
            return sender_class()
        else:
            return None

    @classmethod
    def get_all_senders(cls):
        """
        获取所有已注册的消息发送器类
        """
        return cls._senders.values()


@app.route('/', methods=["GET", "POST"])
def home():
    """
    #todo post功能完善
    :UUID: 用户唯一ID
    :text: 待发送消息
    :desp: 消息描述,可不填
    :to: 发送到:wechat、telegram或者all, 默认telegram
    :return:
    """
    message = dict({})
    if request.method == "POST":
        # 尝试获取 JSON 数据
        data = request.get_json()
        message["UUID"] = data.get('uuid')
        message["text"] = data.get('text')
        message["desp"] = data.get('desp')
        message["to"] = data.get('to')
    else:  # GET 请求
        message["UUID"] = request.args.get('uuid')
        message["text"] = request.args.get('text')
        message["desp"] = request.args.get('desp')
        message["to"] = request.args.get('to')
    try:
        status = asyncio.run(send_message(message))
        return jsonify(status)
    except Exception as e:
        logging.exception(f'非法消息: {message}, 错误信息: {e}')
        return jsonify({"status": False, "message": f"An error occurred: {e}"})


async def send_message(message) -> dict:
    """
    推送消息过去
    :param message: 见home函数
    :return:
    """
    if not message.get("UUID") or not message.get("text"):
        return {"status": False, "message": "缺少必要的参数"}

    sender = MessageSenderFactory.get_sender(message["to"])
    if sender:
        task = asyncio.create_task(sender.send(message))
        return await process_send_result(task)
    else:
        return {"status": False, "message": f"不支持的消息类型: {message['to']}"}


async def process_send_result(task):
    """
    处理发送结果
    """
    result = {"status": False}
    send_result = await task

    if isinstance(send_result, list):  # 多个结果
        error_messages = []
        all_success = True
        for res in send_result:
            if isinstance(res, Exception):
                all_success = False
                error_messages.append(str(res))
            elif isinstance(res, tuple):
                is_success, error_message = res
                if not is_success:
                    all_success = False
                    # error_message有可能为None
                    error_messages.append(error_message if error_message else "未知错误")
            else:
                all_success = False
                error_messages.append("未知错误")

        if all_success:
            result["status"] = True
        else:
            result["message"] = "以下消息发送失败: " + ", ".join(error_messages)
    elif isinstance(send_result, tuple):  # 单个发送方
        is_send, error_message = send_result
        if is_send:
            result["status"] = True
        else:
            result["message"] = error_message or "消息发送失败，请检查是否 UUID 输入错误，或者是远端服务器错误"
    else:  # 异常情况
        result["message"] = "未知的返回结果格式"

    return result


# 设置超时时间（秒）
TIMEOUT = 10

# 注册消息发送器
MessageSenderFactory.register_sender("telegram", TelegramMessageSender)
MessageSenderFactory.register_sender("wechat", WeChatMessageSender)
