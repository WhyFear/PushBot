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
import logging
from dotenv import load_dotenv
from bottom import WeChatPushBot

load_dotenv(encoding='utf-8')  # 读取本地变量
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
MY_UUID = os.getenv("MY_UUID")


def push_message_to_users():
    """
    推送消息给企业微信的指定成员，也可以推送给所有成员，为了用户误操作时不重复进行io操作，多写了很多冗余代码来保证循环
    :return: no return
    """

    def input_to_list(users_list, send_to=None):
        """
        将用户输入的数字信息转换为列表格式
        :param send_to:
        :param users_list:
        :return:
        """
        to_user = "@all"
        if not send_to:
            send_to = input("\n请输入您想要推送的对象编号，以逗号分隔，错误输入会被忽略：").split(',')
        if "0" not in send_to:
            temp_list = []
            for str_num in send_to:
                try:
                    # 使用 int 转换前先去除空格
                    num = int(str_num.strip())
                    temp_list.append(users_list[num])
                except (ValueError, IndexError):
                    print(f"无效的编号：{str_num}")
                except Exception as e:
                    print(f"发生错误：{e}")
            to_user = "|".join(temp_list)
        return to_user

    user_list = WeChatPushBot.get_user_list(MY_UUID)  # 获取员工列表是重io操作，后续的操作应该尽量不会让用户退出

    if not user_list:
        print("没有获取到员工信息")
        return

    user_list.insert(0, "@all")
    for i, user in enumerate(user_list):
        print(f"{i}: {user}")  # 打印所有员工信息

    to_user = input_to_list(user_list)
    message = input("\n请输入您想要发送的消息：")

    if WeChatPushBot.wecom_app_bot(user_uuid=MY_UUID, text=message, to_user=to_user):
        print("发送成功")
    else:
        print("未知错误")


if __name__ == '__main__':
    push_message_to_users()
