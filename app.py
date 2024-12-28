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

from asgiref.sync import async_to_sync
from dotenv import load_dotenv
from flask import Flask, request, jsonify

from bottom import WeChatPushBot
from bottom.TelegramPushBot import TelegramPushBot as tpb

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 设置超时时间（秒）
TIMEOUT = 10

# 创建 TelegramPushBot 实例
telegram_bot = tpb()


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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(send_message(message))
        loop.close()
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
    result = dict({"status": False})
    if not message.get("UUID") or not message.get("text"):
        result["message"] = "缺少必要的参数"
        return result

    if message["to"] == "telegram":
        try:
            # 使用全局的 telegram_bot 实例发送消息
            is_send = await asyncio.wait_for(
                telegram_bot.push_bot(message["UUID"], message["text"], message.get("desp")), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            result["message"] = "Telegram消息发送超时"
            return result
        except Exception as e:
            result["message"] = f"Telegram 消息发送失败: {e}"
            return result
    elif message["to"] == "wechat":
        try:
            is_send = await asyncio.wait_for(
                WeChatPushBot.wecom_app_bot(message["UUID"], message["text"], message.get("desp")), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            result["message"] = "WeChat消息发送超时"
            return result
        except Exception as e:
            result["message"] = f"WeChat 消息发送失败: {e}"
            return result
    elif message["to"] == "all" or not message["to"]:
        is_send_telegram = False
        is_send_wechat = False
        try:
            # 使用全局的 telegram_bot 实例发送消息
            is_send_telegram, is_send_wechat = await asyncio.gather(
                asyncio.wait_for(
                    telegram_bot.push_bot(message["UUID"], message["text"], message.get("desp")), timeout=TIMEOUT),
                asyncio.wait_for(
                    WeChatPushBot.wecom_app_bot(message["UUID"], message["text"], message.get("desp")), timeout=TIMEOUT)
            )
        except asyncio.TimeoutError:
            result["message"] = "消息发送超时"
            return result
        except Exception as e:
            result["message"] = f"消息发送失败: {e}"
            return result
        if is_send_wechat and is_send_telegram:
            is_send = True
        else:
            if not is_send_wechat and not is_send_telegram:
                result["message"] = "Telegram 和 WeChat 均发送失败，可能是服务器错误"
            elif not is_send_telegram:
                result["message"] = "Telegram 发送失败"
            elif not is_send_wechat:
                result["message"] = "WeChat 发送失败"
    else:
        result["message"] = "to 参数错误，请修改。"
        return result

    if is_send:
        result["status"] = True
    else:
        if not result["message"]:
            result["message"] = "消息发送失败，请检查是否 UUID 输入错误，或者是远端服务器错误"
    return result


if __name__ == '__main__':
    load_dotenv(dotenv_path=".env", encoding="utf-8")
    app.config['JSON_AS_ASCII'] = False
