# -*- coding: utf-8 -*-
"""
@author: WhyFear
@software: pycharm
@file: TelegramBot.py
@time: 2019/5/5 0005 19:51
@desc:
"""
import re
import os
import uuid
import logging
import requests
import telegram
from dotenv import load_dotenv

from PushDatabase import pg_db, User, search

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

load_dotenv(encoding='utf8')
token = os.getenv("TELEGRAM_BOT_TOKEN")
tele_bot = telegram.Bot(token=token)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

NORMAL, CHANGE_UUID = range(2)  # 状态码
FLAG = NORMAL


# ----------------------------------------------------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------------------------------------------------
def start(update, context):
    text = """
    "Thanks for using Pakro's Push Bot!"
    /help
    /bop
    /newuser
    /myuuid
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def help(update, context):
    text = """
使用示例:
https://push.pakro.top/?UUID={UUID}&text={HELLO}&desp={WORLD}&to={telegram}
:UUID:必填, 您的唯一凭证
:text:必填, 消息内容
:desp:选填, 消息描述
:to:选填, 有三个参数 1.telegram 2.wechat 3.all  默认为telegram
notice: '{}'不需要填, 填了会报错
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def new_user(update, context):
    chat_id = update.effective_chat.id
    is_new_user = True  # 是新用户

    result = search(telegram_chat_id=chat_id)  # 在数据库中查找是否有该用户,没有就生成新的
    if result["is_in_the_database"]:
        is_new_user = False

    if is_new_user:
        new_uuid = str(uuid.uuid4())
        register_result = register(new_uuid, chat_id)
        if register_result["result"]:
            text = """欢迎使用Pakro's Push Bot, 请保管好您的UUID\n%s\n具体使用方法请看 /help""" % new_uuid
        else:
            text = "未知错误, 请重试。如果出现多次请联系管理员"
    else:  # 老用户
        user_uuid = result["user_uuid"]
        text = """似乎您已经注册过了, 是否忘记了你的UUID?\n%s\n请妥善保管好您的UUID""" % user_uuid

    context.bot.send_message(chat_id=chat_id, text=text)


def my_uuid(update, context):
    chat_id = update.effective_chat.id
    is_new_user = True  # 是新用户

    result = search(telegram_chat_id=chat_id)  # 在数据库中查找是否有该用户,没有就生成新的
    if result["is_in_the_database"]:
        is_new_user = False

    if is_new_user:
        text = """似乎您是新用户, 请使用 /newuser 命令注册\n如果有什么不明白, 请多使用 /help 命令"""
    else:
        user_uuid = result["user_uuid"]
        text = """您的UUID如下：\n%s\n请妥善保管好您的UUID""" % user_uuid
    context.bot.send_message(chat_id=chat_id, text=text)


def push_message(chat_id, text):
    """
    主动向用户推送消息
    :param chat_id: 用户id
    :param text: 推送的消息内容
    :return: no return
    """
    tele_bot.send_message(chat_id=chat_id, text=text)


def echo(update, context):
    """所有用户发送的非指令消息都在这里"""
    global FLAG
    if FLAG == CHANGE_UUID:
        FLAG = NORMAL
        change_uuid(update, context)


def bop(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text="正在收集中....")

    def get_url():
        contents = requests.get('https://random.dog/woof.json').json()
        dog_url = contents['url']
        return dog_url

    def get_image_url():
        allowed_extension = ['jpg', 'jpeg', 'png']
        file_extension = ''
        dog_url = None
        while file_extension not in allowed_extension:
            dog_url = get_url()
            file_extension = re.search("([^.]*)$", dog_url).group(1).lower()
        return dog_url

    url = get_image_url()
    if not url:
        url = get_image_url()

    bot.send_photo(chat_id=chat_id, photo=url)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Sorry, I didn't understand that command:\n" + update.message.text)


def error_handler(update, context, error):
    """Log Errors caused by Updates."""
    logging.error('Update "%s" caused error "%s"', update, error)
    update.message.reply_text('對不起，似乎服务器出现问题了，正在处理。。。')


def test(update, context):
    """
    重新生成UUID
    :param bottom:
    :param update:
    :return:
    """
    chat_id = update.effective_chat.id
    is_new_user = True  # 是新用户

    result = search(telegram_chat_id=chat_id)  # 在数据库中查找是否有该用户,没有就生成新的
    if result["is_in_the_database"]:
        is_new_user = False

    if is_new_user:
        new_uuid = str(uuid.uuid4())
        register_result = register(new_uuid, chat_id)
        if register_result["result"]:
            text = """欢迎使用Pakro's Push Bot, 请保管好您的UUID\n%s\n具体使用方法请看 /help""" % new_uuid
        else:
            text = "未知错误, 请重试。如果出现多次请联系管理员"
        context.bot.send_message(chat_id=chat_id, text=text)
    else:  # 老用户
        user_uuid = result["user_uuid"]
        text = """似乎您已经注册过了, 是否忘记了你的UUID?\n%s\n请妥善保管好您的UUID""" % user_uuid
        key1 = telegram.InlineKeyboardButton(
            '我想要重新生成UUID', callback_data='generate_new_uuid')
        keyboard = telegram.InlineKeyboardMarkup([[key1]])
        update.message.reply_text(text, reply_markup=keyboard)


def my_callback_query(update, context):
    if update.callback_query.data == 'generate_new_uuid':
        context.bot.answerCallbackQuery(
            callback_query_id=update.callback_query.id, text="请稍候")

        # Update Feature with Inline Keyboard
        keyboard = [
            [telegram.InlineKeyboardButton("我想要系统为我生成新的UUID", callback_data='system_generate_new_uuid')],
            [telegram.InlineKeyboardButton("我想要自己输入一个新的UUID", callback_data='user_generate_new_uuid')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)

        context.bot.editMessageText(
            message_id=update.callback_query.message.message_id,
            chat_id=update.callback_query.message.chat.id,
            text="重新注册流程...",
            reply_markup=reply_markup
        )
    if update.callback_query.data == 'system_generate_new_uuid':
        new_uuid = str(uuid.uuid4())
        register_result = {"result": True}  # todo 存入数据库
        if register_result["result"]:
            text = """注册成功！欢迎使用Pakro's Push Bot, 请保管好您的UUID\n%s\n具体使用方法请看 /help""" % new_uuid
        else:
            text = "未知错误, 请重试。如果出现多次请联系管理员"
        context.bot.editMessageText(
            message_id=update.callback_query.message.message_id,
            chat_id=update.callback_query.message.chat.id,
            text=text,
        )
    if update.callback_query.data == 'user_generate_new_uuid':
        context.bot.editMessageText(
            message_id=update.callback_query.message.message_id,
            chat_id=update.callback_query.message.chat.id,
            text="请输入UUID, 注意: 格式不符合将会失败!",
        )
        global FLAG
        FLAG = CHANGE_UUID


def change_uuid(update, context):
    """
    将用户发来的UUID存入数据库。
    :return:
    """
    user_uuid = update.message.text
    try:
        uuid.UUID('{%s}' % user_uuid)
        update.message.reply_text("uuid有效！")
    except:
        global FLAG
        FLAG = CHANGE_UUID
        update.message.reply_text(user_uuid + "不是一个有效的UUID！请重新输入\n放弃请输入 /stop_register")


def stop_register(update, context):
    """

    :param update:
    :param context:
    :return:
    """
    global FLAG
    FLAG = NORMAL
    update.message.reply_text("注册流程结束！")


# ----------------------------------------------------------------------------------------------------------------------

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


def main():
    updater = Updater(token=token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('newuser', new_user))  # 新用户注册
    dp.add_handler(CommandHandler('myuuid', my_uuid))  # 老用户查看UUID
    dp.add_handler(CommandHandler('bop', bop))  # puppy图片
    dp.add_handler(CommandHandler('stop_register', stop_register))
    dp.add_handler(CommandHandler("test", test))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    dp.add_handler(CallbackQueryHandler(my_callback_query))
    dp.add_handler(MessageHandler(Filters.command, unknown))  # 未知命令,文档中要求，必须在所有handler最后。
    dp.add_error_handler(error_handler)
    # push_bot(user_uuid=os.getenv("MY_UUID"),
    #          text="Bot start successfully! Welcome!")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
