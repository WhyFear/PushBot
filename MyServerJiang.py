# -*- coding: utf-8 -*-
"""
@author: WhyFear
@software: pycharm
@file: MyServerJiang.py
@time: 2019/5/5 0005 17:05
@desc:
"""
import logging
from multiprocessing import Process

from flask import Flask, request, jsonify

from bottom import WeChatBot, TelegramBot

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
    message["UUID"] = request.args.get('UUID')
    message["text"] = request.args.get('text')
    message["desp"] = request.args.get('desp')
    message["to"] = request.args.get('to')
    try:
        status = send_message(message)
        return jsonify(status)
    except Exception as e:
        logging.warning(f'非法消息: {message}, 错误信息: {e}')


@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    """
    :return: echostr
    """
    result = dict({"status": False})
    try:
        wechat_key = request.args.get('wechat_key')
        text = request.args.get('text')
        desp = request.args.get('desp')
        if desp:
            send_text = """%s\n%s""" % (text, desp)
        else:
            send_text = text
        result["status"] = WeChatBot.push_message(wechat_key, send_text)
    except Exception as e:
        logger.warning(e)
        return e
    finally:
        return result


# @app.route('/register')
def register_html():
    """
    通过网页链接注册用户, 鉴权还没有做.
    暂时不要使用
    :key: 管理员密码
    :UUID: 用户唯一ID
    :return:
    """

    def register(user) -> dict:
        message = dict({})
        message["status"] = False
        if user["admin_password"] is None or user["UUID"] is None:
            message["message"] = "缺少必要的参数!"
            return message

    user_dict = dict({})
    user_dict["admin_password"] = request.args.get('key')
    user_dict["UUID"] = request.args.get('UUID')
    status = register(user_dict)
    return jsonify(status)


def send_message(message) -> dict:
    """
    推送消息过去
    :param message: 见home函数
    :return:
    """
    result = dict({"status": False})
    is_send = False
    if message["UUID"] and message["text"]:  # 如果没有这两个参数，直接返回
        if message["to"] == "telegram":
            if "desp" in message:
                is_send = TelegramBot.push_bot(message["UUID"], message["text"], message["desp"])
            else:
                is_send = TelegramBot.push_bot(message["UUID"], message["text"])
        elif message["to"] == "wechat":
            if "desp" in message:
                is_send = WeChatBot.wecom_app_bot(message["UUID"], message["text"], message["desp"])
            else:
                is_send = WeChatBot.wecom_app_bot(message["UUID"], message["text"])
        elif message["to"] == "all" or not message["to"]:  # 默认发送到all
            if "desp" in message:
                is_send_telegram = TelegramBot.push_bot(message["UUID"], message["text"], message["desp"])
                is_send_wechat = WeChatBot.wecom_app_bot(message["UUID"], message["text"], message["desp"])
            else:
                is_send_telegram = TelegramBot.push_bot(message["UUID"], message["text"])
                is_send_wechat = WeChatBot.wecom_app_bot(message["UUID"], message["text"])

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
    else:
        result["message"] = "缺少必要的参数"
    # todo 返回错误信息时 传递真正错误
    return result


def main(host, port):
    app.config['JSON_AS_ASCII'] = False
    app.run(port=port, host=host)


if __name__ == '__main__':
    host_ip = ['127.0.0.1', '0.0.0.0']
    server_port = "1234"
    server_main = Process(target=main, args=(host_ip[0], server_port))
    bot_main = Process(target=TelegramBot.main)
    server_main.start()
    bot_main.start()
    server_main.join()
    bot_main.join()
