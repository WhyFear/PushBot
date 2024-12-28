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
from dotenv import load_dotenv
from flask import Flask, request, jsonify

from bottom import WeChatPushBot, TelegramPushBot

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)


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
    message["UUID"] = request.args.get('uuid')
    message["text"] = request.args.get('text')
    message["desp"] = request.args.get('desp')
    message["to"] = request.args.get('to')
    try:
        status = asyncio.run(send_message(message))
        return jsonify(status)
    except Exception as e:
        logging.warning(f'非法消息: {message}, 错误信息: {e}')


# ... 其他代码 ...

async def send_message(message) -> dict:
    """
    推送消息过去
    :param message: 见home函数
    :return:
    """
    result = dict({"status": False})
    if not message.get("UUID") or not message.get("text"):
        result["message"] = "缺少必要的参数"
        return result

    if message["to"] == "telegram":
        is_send = await TelegramPushBot.push_bot(message["UUID"], message["text"], message.get("desp"))
    elif message["to"] == "wechat":
        is_send = WeChatPushBot.wecom_app_bot(message["UUID"], message["text"], message.get("desp"))
    elif message["to"] == "all" or not message["to"]:
        is_send_telegram = await TelegramPushBot.push_bot(message["UUID"], message["text"], message.get("desp"))
        is_send_wechat = WeChatPushBot.wecom_app_bot(message["UUID"], message["text"], message.get("desp"))
        if is_send_wechat and is_send_telegram:
            is_send = True
        else:
            if not is_send_wechat and not is_send_telegram:
                result["message"] = "telegram 和 wechat 均发送失败，可能是服务器错误"
            elif not is_send_telegram:
                result["message"] = "telegram发送失败"
            elif not is_send_wechat:
                result["message"] = "wechat发送失败"
    else:
        result["message"] = "to参数错误，请修改。"

    if is_send:
        result["status"] = True
    else:
        if not result["message"]:
            result["message"] = "消息发送失败，请检查是否UUID输入错误，或者是远端服务器错误"
    return result


# ... 其他代码 ...

if __name__ == '__main__':
    load_dotenv(dotenv_path=".env", encoding="utf-8")
    app.config['JSON_AS_ASCII'] = False
