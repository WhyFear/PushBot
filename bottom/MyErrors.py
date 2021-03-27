# -*- coding: utf-8 -*-
"""
@author: Zeng LH
@contact: 893843891@qq.com
@software: pycharm
@file: MyErrors.py
@time: 2021/3/26 0026 18:53
@desc: 所有自定义错误类
"""


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class GetWecomAccessTokenErrors(Error):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
