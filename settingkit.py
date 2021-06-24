# -*- coding: utf-8 -*-
# @author: Ya Kazama <kazamaya.y@gmail.com>
# @date  2020-10-10 13:55:28
"""
加载配置文件（以“py”结尾的文件），配置文件分为默认配置、用户配置两种。
同名KEY会被覆盖，加载顺序为：默认配置，用户配置
"""

import os
import sys


DEFAULT_KEYS = [
    '__builtins__', '__doc__', '__file__', '__name__', '__package__'
]


def _resolve_name(name, package, level):
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in range(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError(
                'attempted relative import beyond top-level package'
            )
    return "%s.%s" % (package[:dot], name)


def re_import(name, package=None):
    """
    重载模块。不存在，使用__import__()导入；存在，使用reload()重载
    参考：importlib
    """
    if name in sys.modules.keys():
        reload(sys.modules[name])
    else:
        if name.startswith('.'):
            if not package:
                raise TypeError(
                    "relative imports require the 'package' argument"
                )
            level = 0
            for character in name:
                if character != '.':
                    break
                level += 1
            name = _resolve_name(name[level:], package, level)
        __import__(name)
    return sys.modules[name]


def _isinstance(key):
    if isinstance(key, type(sys)):
        key = key.__name__
    return key


def _super_strip(value):
    while True:
        old_value = value
        value = value.strip(' ')
        value = value.strip('"')
        if old_value == value:
            break
    return value


def _parse_raw(raw):
    if not raw:
        return

    if raw[0] == "(":
        obj_type = raw[1:raw.index(")")]
        obj_value = raw[raw.index(")") + 1:]
        if obj_type == "BOOL" or obj_type == "B":
            obj = True if obj_value == "1" else False
        elif obj_type == "INT" or obj_type == "I":
            obj = int(obj_value)
        elif obj_type == "STR" or obj_type == "S":
            obj = obj_value
        else:
            obj = obj_value
    else:
        obj = raw
    return obj


def _parse_type_str(type_str):
    """
    转换string类型

    特殊：nginx语法中 if、for 语法，括号在其后，也会被解析。
    """
    type_obj = type_str

    if not type_str:
        return type_obj

    if type_str[0] != "(":
        return type_obj

    type_str_header = type_str[1:type_str.index(")")]
    type_str_body = type_str[type_str.index(")") + 1:]
    if type_str_header == "BOOL" or type_str_header == "B":
        type_obj = True if type_str_body == "1" else False
    elif type_str_header == "INT" or type_str_header == "I":
        type_obj = int(type_str_body)
    else:
        type_obj = type_str_body

    return type_obj


def _parse_kv_str_as_dict(kv_str, parse_type_str=True):
    """
    将指定格式的字符串解析为字典。格式：K1=V1&K2=V2&K3=V31,V32
    """
    kv_dict = {}

    if not kv_str:
        return kv_dict

    for v in kv_str.split("&"):
        kv = v.strip(" ").split("=")
        if len(kv) > 2:
            kv = [kv[0], '='.join(kv[1:])]

        elif len(kv) == 2:
            v_splited = kv[-1].split(',')
            if len(v_splited) > 1:
                kv = [kv[0], v_splited]
        else:
            continue

        if kv[0] in ["if", "for"]:
            parse_type_str = False

        _v = _parse_type_str(kv[1]) if parse_type_str else kv[1]
        if kv[0] not in kv_dict.keys():
            kv_dict[kv[0]] = _v
        else:
            kv_dict[kv[0]] = [kv_dict[kv[0]]] + [_v]

    return kv_dict


class Settings(object):
    """
    加载配置文件。传入时，使用“.”分隔路径。
        config.global_settings：等同于 config/golbal_settings.py

    注意事项：
    1. 加载顺序（先后顺序）：默认配置 > 用户配置 | 环境变量
        根据loca_settings()、load_enviroment()函数执行先后顺序而定
    2. 不同的数据类型，其值处理方式不同，如下。
        list,tuple  会自动追加并去重
        dict        更新（参考dict.update()函数）
        string      替换,覆盖

    Example 1:
        global_settings = "config.settings"
        user_settings = "config.user_settings"

        settings = Settings(global_settings)
        settings.load_settings(user_settings)
        settings.load_enviroment(prefix="STK_ITEM_")

    Example 2:
        global_settings = "config.settings"
        user_settings = "config.user_settings"

        settings = Settings()
        settings.global_settings(global_settings)
        settings.load_settings(user_settings)
        settings.load_enviroment(prefix="STK_ITEM_")
    """
    def __init__(self, global_settings=None):
        self.GLOBAL_SETTINGS = global_settings
        self.USER_SETTINGS = None
        if global_settings:
            self.global_settings(global_settings)
        self.list_or_tuple_cover = False
        self.dict_cover = False

    def _settings(self, mod):
        if mod in sys.modules.keys():
            del sys.modules[mod]
        mod = re_import(mod)
        for setting in dir(mod):
            if setting not in DEFAULT_KEYS:
                val = getattr(self, setting, None)
                _val = getattr(mod, setting, None)
                print("val", setting, val)
                print("_val", setting, _val)
                if isinstance(val, list) and isinstance(_val, list):
                    if self.list_or_tuple_cover:
                        val = list(set(_val))
                    val = list(set(val + _val))
                elif isinstance(val, tuple) and isinstance(_val, tuple):
                    if self.list_or_tuple_cover:
                        val = list(set(_val))
                    val = tuple(set(val + _val))
                elif isinstance(val, dict) and isinstance(_val, dict):
                    if self.dict_cover:
                        val = _val
                    val.update(_val)
                else:
                    val = _val
                self.__setattr__(setting, val)

    def global_settings(self, global_settings=None):
        """
        加载默认配置
        """
        if global_settings:
            self.GLOBAL_SETTINGS = _isinstance(global_settings)
            self._settings(self.GLOBAL_SETTINGS)

    def load_settings(self,
                      user_settings=None,
                      list_or_tuple_cover=False,
                      dict_cover=False):
        """
        加载用户配置

        list_or_tuple_cover: 是否替换现有值，当数据类型为list、tuple时生效
        dict_cover: 是否替换现有值，当数据类型为dict时生效
        """
        self.USER_SETTINGS = user_settings
        self.list_or_tuple_cover = list_or_tuple_cover
        self.dict_cover = dict_cover

        if isinstance(self.USER_SETTINGS, (list, tuple)):
            for s in self.USER_SETTINGS:
                s = _isinstance(s)
                if s.endswith('.py'):
                    s = s.split('.py')[0]
                # load user settings
                self._settings(s)
        elif isinstance(self.USER_SETTINGS, str):
            self._settings(self.USER_SETTINGS)
        elif isinstance(self.USER_SETTINGS, type(sys)):
            self.USER_SETTINGS = _isinstance(self.USER_SETTINGS)
            self._settings(self.USER_SETTINGS)

    def load_enviroment(self, prefix="STK_ITEM_"):
        """
        加载环境变量，变量参考如下。

        STK_ITEM_KEY_0="K1=V1&K2=V2&K3=V31,V32"

        prefix: 环境变量前缀
        """
        for k, v in os.environ.items():
            if not k.startswith(prefix):
                continue

            item_name = k[len(prefix):]
            item_raw = _super_strip(v)

            item = _parse_raw(item_raw)
            if not isinstance(item, (bool, int)):
                item = _parse_kv_str_as_dict(item if item else "")
            self.__setattr__(item_name, item)

    def reload(self, module):
        if module in sys.modules[module]:
            reload(sys.modules[module])

    def __getattr__(self, name):
        val = getattr(self.__dict__, name, None)
        self.__dict__[name] = val
        return val

    def __setattr__(self, name, value):
        self.__dict__.pop(name, None)
        super(Settings, self).__setattr__(name, value)

    def __delattr__(self, name):
        super(Settings, self).__delattr__(name)
        self.__dict__.pop(name, None)


settings = Settings


def initialize(st_default=None,
               st_user=None,
               st_enviroment_prefix="STK_ITEM_",
               **kwargs):
    """
    加载顺序：
        默认配置
        用户配置
        环境变量
    """
    list_or_tuple_cover = kwargs.pop('list_or_tuple_cover', False)
    dict_cover = kwargs.pop('dict_cover', False)

    st = Settings()
    st.global_settings(st_default)
    st.load_settings(st_user, list_or_tuple_cover, dict_cover)
    st.load_enviroment(st_enviroment_prefix)
    print("settingkit_initialize_ok")
    return st

__all__ = []

