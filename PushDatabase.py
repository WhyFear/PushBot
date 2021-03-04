# -*- coding: utf-8 -*-
"""
@author: Zeng LH
@contact: 893843891@qq.com
@software: pycharm
@file: PushDatabase.py
@time: 2019/5/5 0005 19:31
@desc:
"""
import os
from peewee import *
from dotenv import load_dotenv

load_dotenv(encoding='utf8')

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
USERNAME = os.getenv("USERNAME")
PASSWD = os.getenv("PASSWD")
pg_db = PostgresqlDatabase('pushserverdb', **{'host': HOST, 'port': PORT, 'user': USERNAME, 'password': PASSWD})

WECHAT_KEY = os.getenv("WECHAT_KEY")
WECOM_AGENTID = os.getenv("WECOM_AGENTID")
WECOM_SECRET = os.getenv("WECOM_SECRET")
WECOM_COMPANYID = os.getenv("WECOM_COMPANYID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MY_UUID = os.getenv("MY_UUID")


class BaseModel(Model):
    class Meta:
        database = pg_db


class User(BaseModel):
    userid = AutoField(primary_key=True)  # 数据库自动递增
    UUID = UUIDField()  # 用户唯一id
    wechat = CharField(null=True)
    wecom_agent_id = CharField(null=True)
    wecom_secret = CharField(null=True)
    wecom_company_id = CharField(null=True)
    telegram = CharField(null=True)  # telegram com_id

    class Meta:
        table_name = 'user'


class Admin(BaseModel):
    """
    admin功能还未完善，暂时不启用。
    """
    adminid = AutoField(primary_key=True)
    UUID = UUIDField()

    class Meta:
        table_name = 'admin'


def search(user_uuid=None, telegram_chat_id=None, wecom_key=None) -> dict:
    """
    在数据库中查找wecom_key,com_id或者UUID,如果有查找结果说明是老用户, 否则是新用户
    :param user_uuid: uuid
    :param wecom_key:  wechat key
    :param telegram_chat_id: telegram com_id
    :return: 查找结果, 字典形式返回
    """
    result = dict({})
    result["is_in_the_database"] = False

    if telegram_chat_id is None and user_uuid is None and wecom_key is None:
        result["message"] = "请传入参数"
        return result

    pg_db.connect()
    try:
        if telegram_chat_id:
            query = User.select().where(User.telegram == telegram_chat_id)
        elif wecom_key:
            query = User.select().where(User.wechat == wecom_key)
        elif user_uuid:
            query = User.select().where(User.UUID == user_uuid)

        result["user_uuid"] = query[0].UUID  # 无视这个提醒，前面已经做了assert
        result["chat_id"] = query[0].telegram
        result["wechat_key"] = query[0].wechat
        result["wecom_agent_id"] = query[0].wecom_agent_id
        result["wecom_secret"] = query[0].wecom_secret
        result["wecom_company_id"] = query[0].wecom_company_id
        result["is_in_the_database"] = True
    except:
        result["message"] = "无此用户"
    finally:
        pg_db.close()

    return result


def init_tables():
    pg_db.connect()
    drop_tables = [User]

    u"""
    table 存在，就删除
    """
    for table in drop_tables:
        if table.table_exists():
            table.drop_table()

    creat_tables = [User]
    u"""
    如果table不存在，新建table
    """
    for table in creat_tables:
        if not table.table_exists():
            table.create_table()

    pg_db.close()
    print("数据库初始化完毕!")


def insert_data():
    """
    请勿使用此方法，改用register方法。
    """
    pg_db.connect()
    user_data = {"UUID": MY_UUID, }

    with pg_db.atomic():  # 插入数据
        Admin.create(**user_data)
        User.create(**user_data)
    pg_db.close()


def register() -> dict:
    """
    初始化时直接把我设为管理员账户
    :return:
    """
    user_dict = {"UUID": MY_UUID, "telegram": '132310224', "wechat": WECHAT_KEY,
                 "wecom_agent_id": WECOM_AGENTID, "wecom_secret": WECOM_SECRET,
                 "wecom_company_id": WECOM_COMPANYID}
    try:
        pg_db.connect()
        with pg_db.atomic():  # 插入数据
            User.create(**user_dict)
        return {"result": True}
    except Exception as e:
        return {"result": False, "message": e}
    finally:
        pg_db.close()
        print("处理完成")


if __name__ == '__main__':
    init_tables()
    register()
    pass
