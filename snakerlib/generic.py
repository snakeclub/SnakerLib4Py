#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : generic.py


import sys
import os
import shutil
import traceback
import copy
import re
import json
import logging
import logging.config
from random import Random
from contextlib import contextmanager
from .generic_enum import EnumLogLevel


__MoudleName__ = 'generic'
__MoudleDesc__ = u'通用工具模块'
__Version__ = '0.9.0'
__Author__ = u'snaker'
__Time__ = '2018/1/13'


# 全局变量
# 是否启动调试的开关变量
DEBUG_TOOLS_SWITCH_ON = False


# 全局变量
# 用于生成DEBUG工具日志类
DEBUG_TOOLS_JSON_PARA = u'''{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "DebugToolsFormatter": {
            "format": "[%(asctime)s][PID:%(process)d][TID:%(thread)d]%(message)s"
        }
    },

    "handlers": {
        "DebugToolsConsoleHandler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "DebugToolsFormatter",
            "stream": "ext://sys.stdout"
        }
    },

    "loggers": {
        "DebugToolsConsole": {
            "level": "DEBUG",
            "handlers": ["DebugToolsConsoleHandler"]
        }
    },

    "root": {
        "level": "DEBUG",
        "handlers": []
    }
}
'''


# 全局变量
# 调试日志类
DEBUG_TOOLS_LOGGER = None


class DebugTools(object):
    """
    @class 通用调试类
    @className DebugTools
    @classGroup
    @classVersion 1.0.0
    @classDescription 用于输出各类调试信息

    @classExample {Python} 参考示例:
        1、在主程序的入口设置启动调试
        DebugTools.set_debug(True)

        2、在需要输出调试的地方，传入要输出的变量
        DebugTools.debug_print(abc,10,'ddf',{'a':33,'b':'33'},name=NullObj(),cb=CResult())

    """

    @staticmethod
    def set_debug(set_on):
        """
        @fun 启动debug
        @funName set_debug_on
        @funGroup
        @funVersion
        @funDescription 启动debug信息输出

        @funParam {bool} set_on 是否启动调试

        """
        global DEBUG_TOOLS_SWITCH_ON
        global DEBUG_TOOLS_LOGGER
        if set_on:
            if not DEBUG_TOOLS_SWITCH_ON:
                # 创建输出日志类
                if DEBUG_TOOLS_LOGGER is None:
                    DebugTools.__create_logger()
                DEBUG_TOOLS_SWITCH_ON = True
        else:
            if DEBUG_TOOLS_SWITCH_ON:
                DEBUG_TOOLS_SWITCH_ON = False

    @staticmethod
    def debug_print(*args, **kwargs):
        """
        @fun 打印调试信息
        @funName print
        @funGroup
        @funVersion
        @funDescription 打印传入的多个对象

        """
        global DEBUG_TOOLS_SWITCH_ON
        global DEBUG_TOOLS_LOGGER
        if not DEBUG_TOOLS_SWITCH_ON:
            # 未启动调试
            return
        # 输出打印信息，先准备整体信息
        _print_info = u'[%s][%s][行:%s]DEBUG INFO:\n%s' % (
            os.path.split(os.path.realpath(sys._getframe().f_back.f_code.co_filename))[1],
            sys._getframe().f_back.f_code.co_name,
            sys._getframe().f_back.f_lineno,
            '\n'.join(DebugTools.__get_print_str_seq(args, kwargs))
        )
        DEBUG_TOOLS_LOGGER.debug(_print_info)

    @staticmethod
    def __create_logger():
        """
        @fun 创建logger日志类
        @funName __create_logger
        @funGroup
        @funVersion
        @funDescription 内部函数，创建debug日志类

        """
        global DEBUG_TOOLS_LOGGER
        global DEBUG_TOOLS_JSON_PARA
        if DEBUG_TOOLS_LOGGER is None:
            _json_config = json.loads(DEBUG_TOOLS_JSON_PARA)
            logging.config.dictConfig(_json_config)
            DEBUG_TOOLS_LOGGER = logging.getLogger('DebugToolsConsole')

    @staticmethod
    def __get_print_str(var_obj):
        """
        @fun 获取对象的打印字符串
        @funName __get_print_str
        @funGroup
        @funVersion
        @funDescription 获取对象的打印字符串

        @funParam {object} var_obj 要打印的对象

        @funReturn {string} 打印的字符串

        """
        _print_str = '[type=%s]%s%s' % (
            str(type(var_obj)),
            ('' if not hasattr(var_obj, '__str__') else str(var_obj)),
            ('' if not hasattr(var_obj, '__dict__')
             else StringTools.format_obj_property_str(var_obj, is_deal_subobj=True, c_level=2))
        )
        return _print_str

    @staticmethod
    def __get_print_str_seq(args, kwargs):
        """
        @fun 返回对象清单打印序列
        @funName __get_print_str_seq
        @funGroup
        @funVersion
        @funDescription 返回对象清单打印序列，利用yield逐个输出

        @funParam {truple} args 要打印的对象数组
        @funParam {dict} kwargs keyvalue的对象字典

        @funReturn {iterable} 每次迭代返回一个打印值

        """
        for _obj in args:
            yield '%s[key=]%s' % (
                '    ',
                DebugTools.__get_print_str(_obj)
            )

        for _key in kwargs:
            yield '%s[key=%s]%s' % (
                '    ',
                _key,
                DebugTools.__get_print_str(kwargs[_key])
            )

        return


class ExceptionTools(object):
    """
    @class 异常处理工具
    @className ExceptionTools
    @classGroup generic
    @classVersion 1.0.0
    @classDescription 提供便捷的异常处理模式

    @classExample {Python} 示例名:
        类使用参考示例

    """

    @staticmethod
    @contextmanager
    def ignored(expect=(), logger=None, self_log_msg='', force_log_level=None):
        """
        @fun 忽略指定异常
        @funName ignored
        @funGroup
        @funVersion
        @funDescription 简化异常捕获代码，利用该函数忽略指定的异常，详细说明如下：
            1、对于指定忽略的异常，忽略不处理（如果指定logger则会进行日志输出，使用WARNING级别）
            2、对于非指定的异常，仍抛出异常（如果指定logger则会进行日志输出，使用ERROR级别）
            3、输出的日志为self_log_msg+'\n'+trace_str

        @funParam {tuple} expect 需要忽略的异常列表，例如(ZeroDivisionError, ValueError)
        @funParam {object} logger 日志对象，如果为None代表不需要输出日志，传入对象需满足:
            1、标准logging的logger对象
            2、自定义的日志类对象，但应实现warning、error的标准方法
        @funParam {string} self_log_msg 需要输出的自定义日志信息
        @funParam {EnumLogLevel} force_log_level 强制遇到所有异常统一按指定的日志级别输出

        @funExample {Python} 使用参考示例:
            with ignored((ZeroDivisionError, ValueError), logger, '执行XX出现异常'):
                count = 1 / 0
                count = count + 10000

        """
        try:
            yield
        except expect:
            # 匹配到指定异常，输出日志
            _log_level = EnumLogLevel.WARNING
            if force_log_level is not None:
                _log_level = force_log_level
            ExceptionTools.__print_log(logger=logger, self_log_msg=self_log_msg,
                                       trace_str=traceback.format_exc(), log_level=_log_level)
            pass
        except:
            # 其他异常，输出日志并抛出异常
            _log_level = EnumLogLevel.ERROR
            if force_log_level is not None:
                _log_level = force_log_level
            ExceptionTools.__print_log(logger=logger, self_log_msg=self_log_msg,
                                       trace_str=traceback.format_exc(), log_level=_log_level)
            raise sys.exc_info()[1]

    @staticmethod
    @contextmanager
    def ignored_all(unexpect=(), logger=None, self_log_msg='', force_log_level=None):
        """
        @fun 忽略除指定以外的所有异常
        @funName ignored_all
        @funGroup
        @funVersion
        @funDescription 简化异常捕获代码，利用该函数忽略指定以外的所有异常，详细说明如下：
            1、对于指定以外的异常，忽略不处理（如果指定logger则会进行日志输出，使用WARNING级别）
            2、对于指定的异常，仍抛出异常（如果指定logger则会进行日志输出，使用ERROR级别）
            3、输出的日志为self_log_msg+'\n'+trace_str

        @funParam {tuple} unexpect 指定不能忽略的异常列表，例如(ZeroDivisionError, ValueError)
        @funParam {object} logger 日志对象，如果为None代表不需要输出日志，传入对象需满足:
            1、标准logging的logger对象
            2、自定义的日志类对象，但应实现warning、error的标准方法
        @funParam {string} self_log_msg 需要输出的自定义日志信息
        @funParam {EnumLogLevel} force_log_level 强制遇到所有异常统一按指定的日志级别输出

        @funExample {Python} 使用参考示例:
            with ignored_all((ZeroDivisionError, ValueError), logger, '执行XX出现异常'):
                count = 1 / 0
                count = count + 10000

        """
        try:
            yield
        except unexpect:
            # 匹配到指定异常，输出日志并抛出异常
            _log_level = EnumLogLevel.ERROR
            if force_log_level is not None:
                _log_level = force_log_level
            ExceptionTools.__print_log(logger=logger, self_log_msg=self_log_msg,
                                       trace_str=traceback.format_exc(), log_level=_log_level)
            raise sys.exc_info()[1]
        except:
            # 其他异常，输出日志并忽略
            _log_level = EnumLogLevel.WARNING
            if force_log_level is not None:
                _log_level = force_log_level
            ExceptionTools.__print_log(logger=logger, self_log_msg=self_log_msg,
                                       trace_str=traceback.format_exc(), log_level=_log_level)
            pass

    @staticmethod
    @contextmanager
    def ignored_cresult(result_obj=None, error_map={}, expect=(), expect_no_log=False, expect_use_error_map=True,
                        logger=None, self_log_msg='', force_log_level=None):
        """
        @fun 忽略异常并设置CResult对象
        @funName ignored_CResult
        @funGroup
        @funVersion
        @funDescription 简化异常捕获代码，利用该函数忽略指定的异常，并设置传入的通用结果对象，详细说明如下：
            1、对于指定忽略的异常，忽略不处理，结果为成功（如果指定logger则会进行日志输出，使用WARNING级别）
            2、对于非指定的异常，不抛出异常，结果为失败（如果指定logger则会进行日志输出，使用ERROR级别）
            3、输出的日志为self_log_msg+'\n'+trace_str
            4、根据error_map的映射关系设置错误码和错误信息

        @funParam {CResult} result_obj 需要设置的错误类对象
        @funParam {dict} error_map 用来设置错误类对象的映射表，具体说明如下：
            1、key为异常类，value为(code, msg)的错误码、错误描述二元组
            2、应有一个'DEFAULT'的key，代表没有匹配上的异常映射，默认value为(-1,u'未知异常')
            3、应有一个'SUCESS'的key，代表成功的映射，默认value为(0,u'成功')
        @funParam {tuple} expect 需要忽略的异常列表，例如(ZeroDivisionError, ValueError)
        @funParam {bool} expect_no_log 忽略异常列表是否不打印日志
        @funParam {bool} expect_use_error_map 忽略异常列表所匹配到的异常，所返回错误码是否使用错误码映射表:
            如果在映射表中匹配上则返回映射表的错误码；匹配不上则返回成功
        @funParam {object} logger 日志对象，如果为None代表不需要输出日志，传入对象需满足:
            1、标准logging的logger对象
            2、自定义的日志类对象，但应实现warning、error的标准方法
        @funParam {string} self_log_msg 需要输出的自定义日志信息
        @funParam {EnumLogLevel} force_log_level 强制遇到所有异常统一按指定的日志级别输出

        @funExample {Python} 使用参考示例:
            result = CResult()
            with ExceptionTools.ignored_CResult(result_obj=result, error_map={},expect=(),logger=None,self_log_msg=''):
                i = 1/0
                i = i + 1000
            print(str(result))

        """
        _error_map = copy.deepcopy(error_map)
        try:
            # 初始化对象
            if result_obj is None:
                result_obj = CResult(code=0, msg=u'成功')
            # 确保映射表中有默认值
            if 'SUCESS' not in _error_map.keys():
                _error_map['SUCESS'] = (0, u'成功')
            if 'DEFAULT' not in _error_map.keys():
                _error_map['DEFAULT'] = (-1, u'未知异常')
            # 预设执行结果
            result_obj.code = _error_map['SUCESS'][0]
            result_obj.msg = _error_map['SUCESS'][1]
            result_obj.error = None
            result_obj.trace_str = ''
            # 执行with对应的脚本
            yield
        except expect:
            # 匹配到指定异常，输出日志
            if not expect_no_log:
                _log_level = EnumLogLevel.WARNING
                if force_log_level is not None:
                    _log_level = force_log_level
                ExceptionTools.__print_log(logger=logger, self_log_msg=self_log_msg,
                                           trace_str=traceback.format_exc(), log_level=_log_level)
            # 按成功处理
            result_obj.error = sys.exc_info()
            result_obj.trace_str = traceback.format_exc()
            if expect_use_error_map and result_obj.error[0] in _error_map.keys():
                result_obj.code = _error_map[result_obj.error[0]][0]
                result_obj.msg = _error_map[result_obj.error[0]][1]
            else:
                result_obj.code = _error_map['SUCESS'][0]
                result_obj.msg = _error_map['SUCESS'][1]
                result_obj.error = None
                result_obj.trace_str = ''
            pass
        except:
            # 其他异常，输出日志，获取失败信息
            result_obj.error = sys.exc_info()
            result_obj.trace_str = traceback.format_exc()
            if result_obj.error[0] in _error_map.keys():
                result_obj.code = _error_map[result_obj.error[0]][0]
                result_obj.msg = _error_map[result_obj.error[0]][1]
            else:
                result_obj.code = _error_map['DEFAULT'][0]
                result_obj.msg = _error_map['DEFAULT'][1]
            _log_level = EnumLogLevel.ERROR
            if force_log_level is not None:
                _log_level = force_log_level
            ExceptionTools.__print_log(logger=logger, self_log_msg=self_log_msg,
                                       trace_str=result_obj.trace_str, log_level=_log_level)
            pass

    # 内部函数定义
    @staticmethod
    def __print_log(logger=None, self_log_msg='', trace_str='', log_level=EnumLogLevel.WARNING):
        """
        @fun 内部进行日志输出处理
        @funName __print_log
        @funGroup
        @funVersion
        @funDescription 调用日志对象进行日志输出处理

        @funParam {object} logger 日志对象，如果为None代表不需要输出日志，传入对象需满足:
            1、标准logging的logger对象
            2、自定义的日志类对象，但应实现warning、error等的标准方法
        @funParam {string} self_log_msg 需要输出的自定义日志信息
        @funParam {string} trace_str 错误追踪堆栈日志，异常时的traceback.format_exc()
        @funParam {EnumLogLevel} log_level 需要输出的自定义日志级别

        """
        if logger is not None:
            # 要输出的日志内容
            _log_str = ''
            if len(self_log_msg) > 0:
                _log_str = self_log_msg + '\n' + trace_str
            else:
                _log_str = trace_str
            # 输出日志
            RunTools.writelog_by_level(logger=logger, log_str=_log_str, log_level=log_level)


class FileTools(object):
    """
    @class 文件处理工具
    @className FileTools
    @classGroup generic
    @classVersion 1.0.0
    @classDescription 提供各类文件、目录相关的常用工具函数（静态方法）

    """

    @staticmethod
    def get_exefile_fullname():
        """
        @fun 获得执行主程序文件名（含路径）
        @funName get_exefile_fullname
        @funGroup
        @funVersion
        @funDescription 获得执行主程序文件名（含路径）

        @funReturn {string} 执行主程序文件名（含路径）

        @funExample {Python} 使用参考示例:
            filepath = FileTools.get_exefile_fullname()

        """
        return os.path.realpath(sys.argv[0])

    @staticmethod
    def get_exefile_name():
        """
        @fun 获得执行主程序文件名（不含路径，含扩展名）
        @funName get_exefile_name
        @funGroup
        @funVersion
        @funDescription 获得执行主程序文件名（不含路径，含扩展名）

        @funReturn {string} 文件名（不含路径，含扩展名）

        @funExample {Python} 使用参考示例:
            filepath = FileTools.get_exefile_name()

        """
        return os.path.split(os.path.realpath(sys.argv[0]))[1]

    @staticmethod
    def get_exefile_name_no_ext():
        """
        @fun 获得执行主程序文件名（不含路径，不含扩展名）
        @funName get_exefile_name_no_ext
        @funGroup
        @funVersion
        @funDescription 获得执行主程序文件名（不含路径，不含扩展名）
        @funExcepiton:

        @funReturn {string} 文件名（不含路径，不含扩展名）

        @funExample {Python} 使用参考示例:
            filepath = FileTools.get_exefile_name_no_ext()

        """
        _filename = os.path.split(os.path.realpath(sys.argv[0]))[1]
        _dot_index = _filename.rfind(".")
        if _dot_index == -1:
            return _filename
        else:
            return _filename[0:_dot_index]

    @staticmethod
    def get_exefile_path():
        """
        @fun 获得执行主程序的路径（不含文件名）
        @funName get_exefile_path
        @funGroup
        @funVersion
        @funDescription 获得执行主程序的路径（不含文件名）

        @funReturn {string} 程序路径（不含文件名，最后一个字符不为路径分隔符）

        @funExample {Python} 使用参考示例:
            filepath = FileTools.get_exefile_path()

        """
        return os.path.split(os.path.realpath(sys.argv[0]))[0]

    @staticmethod
    def create_dir(path):
        """
        @fun 创建指定的路径
        @funName create_dir
        @funGroup
        @funVersion
        @funDescription 创建指定的路径
        @funExcepiton:
            FileExistsError 路径存在的情况抛出文件存在异常

        @funParam {string} path 需要创建的路径

        @funExample {Python} 使用参考示例:
            FileTools.create_dir("c:/test/")

        """
        os.makedirs(path)

    @staticmethod
    def get_filelist(path='', regex_str='', is_fullname=True):
        """
        @fun 获取指定目录下的文件清单
        @funName get_filelist
        @funGroup
        @funVersion
        @funDescription 获取指定目录下的文件清单
        @funExcepiton:
            FileNotFoundError 当path不存在的情况下，会抛出该异常

        @funParam {string} path 需要获取文件的目录
        @funParam {string} regex_str 需匹配文件名的正则表达式（''代表无需匹配）
        @funParam {bool} is_fullname 结果的文件名是否包含路径

        @funReturn {string[]} 文件清单数组

        @funExample {Python} 参考示例:
            filelist = FileTools.get_filelist(path='c:\\')

        """
        _filelist = []
        _file_names = os.listdir(path)
        _pattern = None
        if len(regex_str) > 0:
            _pattern = re.compile(regex_str)
        for fn in _file_names:
            _full_filename = os.path.join(path, fn)
            if os.path.isfile(_full_filename):
                _temp_filename = fn
                if is_fullname:
                    _temp_filename = _full_filename
                if _pattern is not None:
                    if _pattern.match(fn):
                        _filelist.append(_temp_filename)
                else:
                    _filelist.append(_temp_filename)
        return _filelist

    @staticmethod
    def get_dirlist(path='', regex_str='', is_fullpath=True):
        """
        @fun 获取指定目录下的子目录清单
        @funName get_dirlist
        @funGroup
        @funVersion
        @funDescription 获取指定目录下的子目录清单
        @funExcepiton:
            FileNotFoundError 当path不存在的情况下，会抛出该异常

        @funParam {string} path 需要获取子目录的目录
        @funParam {string} regex_str 需匹配目录名的正则表达式（''代表无需匹配）
        @funParam {bool} is_fullpath 结果的目录名是否包含路径

        @funReturn {string[]} 目录清单数组（不带最后的分隔符）

        @funExample {代码格式} 示例名:
            函数使用参考示例

        """
        _dirlist = []
        _file_names = os.listdir(path)
        _pattern = None
        if regex_str != "":
            _pattern = re.compile(regex_str)
        for fn in _file_names:
            _full_filename = os.path.join(path, fn)
            if not os.path.isfile(_full_filename):
                _temp_filename = fn
                if is_fullpath:
                    _temp_filename = _full_filename
                if _pattern is not None:
                    if _pattern.match(fn):
                        _dirlist.append(_temp_filename)
                else:
                    _dirlist.append(_temp_filename)
        return _dirlist

    @staticmethod
    def remove_dir(path):
        """
        @fun 删除指定目录（及目录下的所有文件及目录）
        @funName remove_dir
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 删除指定目录（及目录下的所有文件及目录）
        @funExcepiton:
            FileNotFoundError 找不到指定的路径时抛出该异常
            PermissionError 没有权限时抛出该异常
            NotADirectoryError 如果给出的路径不是目录而是文件时抛出

        @funParam {string} path 需要删除的路径

        """
        shutil.rmtree(path=path, ignore_errors=False)

    @staticmethod
    def remove_file(filename):
        """
        @fun 删除指定文件
        @funName remove_file
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 删除指定文件
        @funExcepiton:
            FileNotFoundError 路径不是文件或文件不存在时抛出该异常
            PermissionError 没有权限时抛出该异常

        @funParam {string} filename 需要删除的文件路径

        """
        if os.path.isfile(filename):
            os.remove(filename)
        else:
            raise FileNotFoundError

    @staticmethod
    def remove_sub_dirs(path='', regex_str=''):
        """
        @fun 删除指定目录下的子目录（及子目录下的文件和目录）
        @funName remove_sub_dirs
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 删除指定目录下的子目录（及子目录下的文件和目录）
        @funExcepiton:
            FileNotFoundError 当path不存在的情况下，会抛出该异常
            PermissionError 没有权限时抛出该异常
            NotADirectoryError 如果给出的路径不是目录而是文件时抛出

        @funParam {string} path 需要删除的子目录的目录
        @funParam {string} regex_str 需匹配目录名的正则表达式（''代表无需匹配）

        """
        _dirs = FileTools.get_dirlist(path=path, regex_str=regex_str, is_fullpath=True)
        for _dir in _dirs:
            FileTools.remove_dir(_dir)

    @staticmethod
    def remove_files(path='', regex_str=''):
        """
        @fun 删除指定目录下的文件
        @funName remove_files
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 删除指定目录下的文件
        @funExcepiton:
            FileNotFoundError 当path不存在的情况下，会抛出该异常
            PermissionError 没有权限时抛出该异常
            NotADirectoryError 如果给出的路径不是目录而是文件时抛出

        @funParam {string} path 需要删除的文件的目录
        @funParam {string} regex_str 需匹配文件名的正则表达式（''代表无需匹配）

        """
        _files = FileTools.get_filelist(path=path, regex_str=regex_str, is_fullname=True)
        for _file in _files:
            FileTools.remove_file(_file)


class StringTools(object):
    """
    @class 字符串处理通用类
    @className StringTools
    @classGroup
    @classVersion 1.0.0
    @classDescription 提供各类字符串处理相关的常用工具函数（静态方法）

    """

    @staticmethod
    def bytes_to_hex(byte_array):
        """
        @fun 将byte串转换为哈希字符串
        @funName bytes_to_hex
        @funGroup
        @funVersion
        @funDescription 将byte串转换为哈希字符串

        @funParam {byte[]} byte_array 需要转换的byte数组

        @funReturn {string} 转换后的hex字符串

        @funExample {Python} 参考示例:
            StringTools.bytes_to_hex(bytes("test string", encoding='utf-8'))

        """
        return ''.join(["%02X" % x for x in byte_array]).strip()

    @staticmethod
    def hex_to_bytes(hex_str):
        """
        @fun 将哈希字符串转换为byte数组
        @funName hex_to_bytes
        @funGroup
        @funVersion
        @funDescription 将哈希字符串转换为byte数组

        @funParam {string} hex_str 需要转换的Hex样式的字符串

        @funReturn {byte[]} byte数组

        @funExample {Python} 参考示例:
            StringTools.hex_to_bytes("A3D3F33433")

        """
        return bytes.fromhex(hex_str)

    @staticmethod
    def fill_fix_string(deal_str, fix_len, fill_char, left=True):
        """
        @fun 用指定字符填充字符串达到固定长度
        @funName fill_fix_string
        @funGroup
        @funVersion
        @funDescription 用指定字符填充字符串达到固定长度

        @funParam {string} deal_str 要处理的字符串
        @funParam {int} fix_len 返回字符串的固定长度
        @funParam {string} fill_char 填充字符(单字符)
        @funParam {bool} left 填充方向，True-左填充，False-右填充

        @funReturn {string} 如果原字符串长度已超过指定长度，则直接返回原字符串；否则返回处理后的字符串

        @funExample {Python} 参考示例:
            fix_str = StringTools.fill_fix_string('My job is', 50, ' ', False)

        """
        _str = copy.deepcopy(deal_str)
        # 生成填充串
        _mixstr = ""
        _i = 0
        while _i < fix_len - len(_str):
            _mixstr = _mixstr + fill_char
            _i = _i + 1
        # 按方向填充
        if left:
            return _mixstr + _str
        else:
            return _str + _mixstr

    @staticmethod
    def get_list_from_str(deal_str):
        """
        @fun 从字符串中提炼出数组
        @funName get_list_from_str
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 从字符串中按照python的模式提炼出数组，说明：
            1、数组内的对象根据字符的形式取得实际类型，例如：
                'text' - 字符串
                10 - 数字
                True - bool类型
            2、如果数组有嵌套，可以支持嵌套的模式

        @funParam {string} deal_str 要提炼的字符串，内部要含有[a,b,c,d,'d']这类的字符串，例如'dfdfdfd[ddd,aa,dd]'

        @funReturn {list} 抽离出来的数组

        @funExample {Python} 参考示例:
            mylist = StringTools.get_list_from_str('aaa["a", 10, [39, 4], True, 21.4]bbb')

        """
        _array = []
        _index1 = deal_str.find("[")
        _index2 = deal_str.rfind("]")  # 从后往前找
        if _index2 <= _index1:
            return _array
        _str = deal_str[_index1:_index2 + 1]
        _array = eval(_str)
        return _array

    @staticmethod
    def get_random_str(random_length=8, chars="AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789"):
        """
        @fun 随机生成固定长度的字符串
        @funName get_random_str
        @funGroup
        @funVersion
        @funDescription 随机生成固定长度的字符串

        @funParam {int} random_length 需生成的字符串长度
        @funParam {string} chars 随机抽取的字符串内容

        @funReturn {string} 返回的字符串

        @funExample {Python} 参考示例:
            randomstr = StringTools.get_random_str(10)

        """
        _str = ''
        length = len(chars) - 1
        random = Random()
        for i in range(random_length):
            _str += chars[random.randint(0, length)]
        return _str

    @staticmethod
    def get_n_index(src, sub, n=1, start=0):
        """
        查找第n次出现子字符串的位置

        @decorators staticmethod

        @param {string} src - 要处理的字符串
        @param {string} sub - 要查找的子字符串

        @param {int} [n=1] - 要查找的字符串出现次数
        @param {int} [start=0] - 查找开始位置

        @returns {int} - 返回找到的位置，如果找不到返回-1
        """
        if n < 1:
            # 已找不到了
            return -1
        index = src.find(sub, start)
        if index != -1 and n > 1:
            return StringTools.get_n_index(src, sub, n - 1, index + len(sub))
        return index

    @staticmethod
    def format_obj_property_str(deal_obj, is_deal_subobj=False, c_level=0, max_level=10, is_same_line=False):
        """
        @fun 将对象属性格式化为可打印字符串
        @funName format_obj_property_str
        @funGroup
        @funVersion
        @funDescription 将对象属性格式化为可打印字符串

        @funParam {object} obj 要格式化的对象
        @funParam {bool} is_deal_subobj 是否要打印属性对象的子属性
        @funParam {int} c_level 打印级别（根据级别调整缩进位数，每一级缩进2个空格）
        @funParam {int} max_level 最大检索级别，<=0代表不进行限制
        @funParam {bool} is_same_line 输出内容是否不换行，内部使用，如果不换行则忽略缩进

        @funReturn {string} 返回格式化后的字符串

        @funExample {Python} 参考示例:
            obj = NullObj()
            obj.aa = 1
            obj.cb = 'fdfd'
            obj.kk = NullObj()
            obj.kk.abc = 3
            obj.kk.bcd = 'dfdfd'
            print(StringTools.format_obj_property_str(obj=obj,is_deal_subobj=True))

        """
        # 先打印对象自身
        _indent_str = ''
        if not is_same_line:
            _indent_str = StringTools.fill_fix_string(
                deal_str='', fix_len=c_level * 2, fill_char=' ', left=True)
        _retstr = '%stype(%s) ' % (
            _indent_str,
            type(deal_obj)
        )
        if is_deal_subobj and (max_level <= 0 or (max_level > c_level)):
            _indent_str = StringTools.fill_fix_string(
                deal_str='', fix_len=(c_level+1) * 2, fill_char=' ', left=True)
            # 要打印子对象,区分类型进行处理
            if type(deal_obj) in (list, tuple):
                # 数组和列表
                _index = 0
                while _index < len(deal_obj):
                    _retstr = (
                        _retstr + '\n' + _indent_str
                        + '[index:' + str(_index) + '] '
                        + StringTools.format_obj_property_str(
                            deal_obj[_index], is_deal_subobj=is_deal_subobj,
                            c_level=c_level + 1, max_level=max_level, is_same_line=True
                        )
                    )
                    _index = _index + 1
            elif type(deal_obj) == dict:
                # 字典
                for _key in deal_obj.keys():
                    _retstr = (
                        _retstr + '\n' + _indent_str
                        + 'key: ' + str(_key) + 'value: '
                        + StringTools.format_obj_property_str(
                            deal_obj[_key], is_deal_subobj=is_deal_subobj,
                            c_level=c_level + 2, max_level=max_level, is_same_line=True
                        )
                    )
            else:
                # 一般对象，直接类的属性，通过dir获取，且非内置属性
                _attr_print = False
                _attr_dir = list()
                if str(deal_obj).find(' object at 0x') > 0:  # 通过str判断是否有重载处理
                    _attr_print = True
                    _attr_dir = dir(deal_obj)
                    for _item in _attr_dir:
                        if _item[0: 2] != '__' and not callable(getattr(deal_obj, _item)):
                            _retstr = (
                                _retstr + "\n" + _indent_str
                                + _item + '(attr): '
                                + StringTools.format_obj_property_str(
                                    getattr(deal_obj, _item), is_deal_subobj=is_deal_subobj,
                                    c_level=c_level + 2, max_level=max_level, is_same_line=True
                                )
                            )

                # 一般对象,object上补充的属性
                try:
                    for _item in deal_obj.__dict__.items():
                        if _attr_print and _item[0] not in _attr_dir:
                            _retstr = (
                                _retstr + "\n" + _indent_str
                                + _item[0] + '(__dict__): '
                                + StringTools.format_obj_property_str(
                                    _item[1], is_deal_subobj=is_deal_subobj,
                                    c_level=c_level + 2, max_level=max_level, is_same_line=True
                                )
                            )
                except:
                    # 可能对象没有__dict__属性
                    _retstr = _retstr + str(deal_obj)
        else:
            # 不打印子对象
            _retstr = _retstr + str(deal_obj)

        return _retstr


class ImportTools(object):
    """
    @class 库导入工具
    @className ImportTools
    @classGroup
    @classVersion 1.0.0
    @classDescription 提供库导入相关功能，包括动态导入库的支持

    """

    @staticmethod
    def check_moudle_imported(moudle_name):
        """
        @fun 检查模块是否已导入
        @funName check_moudle_imported
        @funGroup
        @funVersion
        @funDescription 检查指定模块名是否已导入

        @funParam {string} moudle_name 要检查的模块名，形式有以下几种:
            (1)基础库的情况，例如'sys'
            (2)子库情况，例如'generic_enum.EnumLogLevel'

        @funReturn {bool} True-模块已导入，False-模块未导入

        """
        return moudle_name in sys.modules.keys()

    @staticmethod
    def import_module(module_name, as_name=None, extend_path=None, import_member=None, is_force=False):
        """
        @fun 导入指定模块
        @funName import_module
        @funGroup
        @funVersion
        @funDescription 导入指定模块，如果不指定is_force参数强制加载，已经加载过的模块不会重新加载，:
            对使用有import_member模式的使用方式可能会存在问题

        @funParam {string} module_name 要导入的模块名
        @funParam {string} as_name 对导入的模块名设置的别名
        @funParam {string} extend_path 对于存放在非python搜索路径（sys.path）外的模块，需要指定扩展搜索路径
        @funParam {string} import_member 指定导入模块对应的成员对象，None代表不指定导入对象，"*"代表导入模块的所有对象:
            效果如from module_name import import_member
        @funParam {bool} is_force 是否强制执行导入的命令动作，True-强制再执行导入命令，Fasle-如果模块已存在则不导入

        @funReturn {Moudle} 已导入的模块对象，可以直接引用该对象执行操作

        @funExample {python} 使用参考示例:
            lib_obj = ImportTools.import_module('os')
            print(lib_obj.path.realpath(''))

        """
        if is_force or not ImportTools.check_moudle_imported(module_name):
            # 模块未导入，导入模块
            if extend_path is not None:
                # 指定了路径，组装路径
                lib_path = os.path.realpath(extend_path)
                if lib_path not in sys.path:
                    sys.path.append(lib_path)

            # 导入对象
            _exec_code = ''
            if import_member is None or import_member == '':
                # 无需指定对象导入
                _exec_code = 'import %s' % module_name
                if len(as_name) > 0:
                    _exec_code = '%s as %s' % (_exec_code, as_name)
            else:
                _exec_code = 'from %s import %s' % (module_name, import_member)

            # 执行导入动作
            exec(_exec_code)

        # 返回模块
        return sys.modules[module_name]

    @staticmethod
    def has_attr(module_obj, attr_name):
        """
        @fun 检查模块或对象是否有指定名称的属性
        @funName is_has_attr
        @funGroup
        @funVersion
        @funDescription 检查模块或对象是否有指定名称的属性

        @funParam {Moudle} module_obj 模块对象
        @funParam {string} attr_name 属性名（类名/函数名/属性名)

        @funReturn {bool} 是否包含属性，True-包含，False-不包含

        """
        return hasattr(module_obj, attr_name)

    @staticmethod
    def get_moudle_name(module_obj):
        """
        @fun 获取模块名
        @funName get_moudle_name
        @funGroup
        @funVersion
        @funDescription 获取模块名，如果模块是包中，模块名会包括包路径

        @funParam {Moudle} module_obj 模块对象

        @funReturn {string} 模块对象的名称

        """
        return module_obj.__name__


class NetTools(object):
    """
    @class 网络处理相关工具
    @className NetTools
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 提供网络处理相关的函数，包括字节转换处理等

    """

    @staticmethod
    def int_to_bytes(int_value, fix_len=4, byte_order="big", signed=True):
        """
        @fun 将整型数据转换为字节数组
        @funName int_to_bytes
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 与bytes_to_int配套使用
        @funExcepiton:
            OverflowError 整数转换出的字节数组长度超过了定义数组的长度，则产生该问题；signed为False（无符号位），但:
                要转换的整数为负数时，也会产生该异常

        @funParam {int} int_value 要转换的数字
        @funParam {int} fix_len 返回数组的长度，如果整数转换出的字节数组长度超过了该长度，则产生OverflowError
        @funParam {string} byte_order 字节顺序，值为'big'或者'little':
            big - 表示最有意义的字节放在字节数组的开头
            little - 表示最有意义的字节放在字节数组的结尾
            sys.byteorder - 保存了主机系统的字节序，可以使用这个属性获取本机顺序
        @funParam {bool} signed 确定是否使用补码来表示整数，如果值为False，并且是负数，则产生OverflowError

        @funReturn {bytes} 转换后的字节数组

        """
        return int_value.to_bytes(length=fix_len, byteorder=byte_order, signed=signed)

    '''
    @fun BytesToInt 将字节数组转换为整型数字
    @desc 与IntToBytes配套使用
    @input bytes bytesValue 要转换的字节数组
    @input byteOrder 字节序；值为"big"或者"little"，"big"表示最有意义的字节放在字节数组的开头，"little"表示最有意义的字节放在字节数组的结尾。sys.byteorder保存了主机系统的字节序
    @input bool signed 确定是否使用补码来表示整数，如果值为False，并且是负数，则产生OverflowError
    @return int 转换后的整数
    '''

    @staticmethod
    def bytes_to_int(bytes_value, byte_order="big", signed=True):
        """
        @fun 将字节数组转换为整型数字
        @funName bytes_to_int
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 与int_to_bytes配套使用
        @funExcepiton:
            OverflowError signed为False（无符号位），但要转换的整数为负数时，也会产生该异常

        @funParam {bytes} bytes_value 要转换的字节数组
        @funParam {string} byte_order 字节顺序，值为'big'或者'little':
            big - 表示最有意义的字节放在字节数组的开头
            little - 表示最有意义的字节放在字节数组的结尾
            sys.byteorder - 保存了主机系统的字节序，可以使用这个属性获取本机顺序
        @funParam {bool} signed 确定是否使用补码来表示整数，如果值为False，并且是负数，则产生OverflowError

        @funReturn {int} 转换后的整数

        """
        return int.from_bytes(bytes_value, byteorder=byte_order, signed=signed)


# 全局变量
# 用于存储打开的单进程控制文件句柄的字典（dict）
# key为文件路径，value为句柄变量
# 该变量为全局变量，以支持在不同线程间访问
SINGLE_PROCESS_PID_FILE_LIST = dict()


# 全局变量
# 用于存储全局变量的值
# key为全局变量名（string），value为全局变量的值
RUNTOOL_GLOBAL_VAR_LIST = dict()


class RunTools(object):
    """
    @class 运行参数处理通用类
    @className RunTools
    @classGroup
    @classVersion 1.0.0
    @classDescription 提供各类运行环境处理相关的常用工具函数（静态方法）

    """

    @staticmethod
    def get_kv_opts():
        """
        @fun 获取命令行输入参数
        @funName get_kv_opts
        @funGroup
        @funVersion
        @funDescription 获取Key=Value格式的命令行输入参数

        @funReturn {dict} 命令行参数字典：key为参数名，value为参数值

        @funExample {Python} 示例名:
            命令行# python ggeneric.py key1=value1 key2=value2 key3="value 3" "key 4"=value4 "key 5"="value 5"
            input_para = RunTools.get_kv_opts()

        """
        # 建立要返回的字典
        _dict = {}
        # 遍历参数
        i = 1
        _argv_count = len(sys.argv)
        while i < _argv_count:
            _pair = str(sys.argv[i]).split("=")
            _key = _pair[0]
            _value = ""
            if len(_pair) > 1:
                _value = sys.argv[i][len(_key) + 1:]
            _dict[_key] = _value
            i = i + 1
        return _dict

    @staticmethod
    def var_defined(name_str):
        """
        @fun 判断变量是否已定义
        @funName var_defined
        @funGroup
        @funVersion
        @funDescription 判断变量是否已定义

        @funParam {string} name_str 变量名（注意是名字字符串，不是传入变量）

        @funReturn {bool} 是否已定义，True-已定义，False-未定义

        """
        try:
            type(eval(name_str))
        except:
            return False
        else:
            return True

    @staticmethod
    def writelog_by_level(logger, log_str, log_level=EnumLogLevel.INFO):
        """
        @fun 根据日志级别调用日志输出
        @funName writelog_by_level
        @funGroup
        @funVersion
        @funDescription 根据日志级别调用日志类的不同方法，简化日志级别的判断处理

        @funParam {object} logger 日志对象，如果为None代表不需要输出日志，传入对象需满足:
            1、标准logging的logger对象
            2、自定义的日志类对象，但应实现warning、error的标准方法
        @funParam {string} log_str 需输出的日志内容
        @funParam {EnumLogLevel} log_level 输出日志级别

        """
        if log_level == EnumLogLevel.DEBUG:
            logger.debug(log_str)
        elif log_level == EnumLogLevel.WARNING:
            logger.warning(log_str)
        elif log_level == EnumLogLevel.ERROR:
            logger.error(log_str)
        elif log_level == EnumLogLevel.CRITICAL:
            logger.critical(log_str)
        else:
            logger.info(log_str)

    @staticmethod
    def set_global_var(key, value):
        """
        @fun 设置全局变量的值
        @funName set_global_var
        @funGroup
        @funVersion
        @funDescription 设置全局变量的值，后续可以通过Key获取到指定的值，如果如果key存在将覆盖

        @funParam {string} key 要设置的全局变量key值
        @funParam {object} value 要设置的全局变量值

        """
        global RUNTOOL_GLOBAL_VAR_LIST
        RUNTOOL_GLOBAL_VAR_LIST[key] = value

    @staticmethod
    def get_global_var(key):
        """
        @fun 获取全局变量的值
        @funName get_global_var
        @funGroup
        @funVersion
        @funDescription 根据key获取全局变量的值，如果找不到key则返回None

        @funParam {string} key 要获取的全局变量key值

        @funReturn {object} 全局变量的值，如果找不到key则返回None

        """
        global RUNTOOL_GLOBAL_VAR_LIST
        if key in RUNTOOL_GLOBAL_VAR_LIST.keys():
            return RUNTOOL_GLOBAL_VAR_LIST[key]
        else:
            return None

    @staticmethod
    def del_global_var(key):
        """
        @fun 删除指定全局变量
        @funName del_global_var
        @funGroup
        @funVersion
        @funDescription 删除key值对应的全局变量

        @funParam {string} key 要删除的全局变量key值

        """
        global RUNTOOL_GLOBAL_VAR_LIST
        if key in RUNTOOL_GLOBAL_VAR_LIST.keys():
            del RUNTOOL_GLOBAL_VAR_LIST[key]

    @staticmethod
    def del_all_global_var():
        """
        @fun 清空所有全局变量
        @funName del_all_global_var
        @funGroup
        @funVersion
        @funDescription 清空所有全局变量

        """
        global RUNTOOL_GLOBAL_VAR_LIST
        RUNTOOL_GLOBAL_VAR_LIST.clear()

    @staticmethod
    def single_process_get_lockfile(process_name='', base_path=''):
        """
        @fun 获取进程锁处理锁文件路径
        @funName single_process_get_lockfile
        @funGroup
        @funVersion
        @funDescription 进程锁处理的辅助函数，获取指定进程的锁文件名（含路径）

        @funParam {string} process_name 进程锁的进程名，默认值为''；如果为''代表获取执行程序的模块名
        @funParam {string} base_path 进程锁文件指定的路径，默认值为''；如果为''代表获取执行程序的模块文件目录

        @funReturn {string} 锁文件名（含路径）

        """
        _process_name = process_name
        _base_path = base_path
        if not len(_process_name) > 0:
            # 默认取运行的程序名
            _process_name = FileTools.get_exefile_name_no_ext()
        if not len(_base_path) > 0:
            # 默认取运行程序目录
            _base_path = FileTools.get_exefile_path() + os.sep
        else:
            _base_path = os.path.realpath(_base_path)
            if not os.path.isdir(_base_path):
                # 如果是文件的情况下，拿文件对应的目录
                _base_path = os.path.split(os.path.realpath(_base_path))[0]
            _base_path = _base_path + os.sep
        return _base_path + _process_name + ".lock"  # 要建立锁的文件名

    @staticmethod
    def single_process_del_lockfile(process_name='', base_path=''):
        """
        @fun 强制删除进程锁文件
        @funName single_process_del_lockfile
        @funGroup
        @funVersion
        @funDescription 进程锁处理的辅助函数，强制删除进程锁文件

        @funParam {string} process_name 进程锁的进程名，默认值为''；如果为''代表获取执行程序的模块名
        @funParam {string} base_path 进程锁文件指定的路径，默认值为''；如果为''代表获取执行程序的模块文件目录

        """
        try:
            _lock_file = RunTools.single_process_get_lockfile(
                process_name=process_name, base_path=base_path)
            if os.path.exists(_lock_file) and os.path.isfile(_lock_file):
                os.remove(_lock_file)
        except:
            return

    @staticmethod
    def single_process_enter(process_name='', base_path='', is_try_del_lockfile=False):
        """
        @fun 获取进程锁
        @funName single_process_enter
        @funGroup
        @funVersion
        @funDescription 获取进程锁：如果获取失败代表锁已被其他进程占有，可选择结束进程以控制同一时间只有一个进程执行

        @funParam {string} process_name 进程锁的进程名，默认值为''；如果为''代表获取执行程序的模块名
        @funParam {string} base_path 进程锁文件指定的路径，默认值为''；如果为''代表获取执行程序的模块文件目录
        @funParam {bool} is_try_del_lockfile 是否尝试先删除锁文件（可以应对强制关闭进程未自动删除锁文件的情况）

        @funReturn {bool} 是否获取进程锁成功：True - 获取成功并占用锁；False - 获取失败，应选择关闭进程

        @funExample {Python} 参考示例:
            get_process_lock = RunTools.single_process_enter("CFuntion","c:/test/")
            if not get_process_lock:
                print("已有一个进程在执行状态，结束本进程")
                exit(1)

            try:
                do something ...
            finally:
                RunTools.single_process_exit("CFuntion","c:/test/")

        """
        global SINGLE_PROCESS_PID_FILE_LIST
        if not RunTools.var_defined("SINGLE_PROCESS_PID_FILE_LIST"):
            SINGLE_PROCESS_PID_FILE_LIST = {}
        # 要建立锁的文件名
        _lock_file = RunTools.single_process_get_lockfile(
            process_name=process_name, base_path=base_path)
        # 尝试自动先删除锁文件
        if is_try_del_lockfile:
            RunTools.single_process_del_lockfile(process_name=process_name, base_path=base_path)
        # 尝试创建锁文件
        try:
            _pid = os.open(_lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            SINGLE_PROCESS_PID_FILE_LIST[_lock_file] = _pid
        except OSError:
            return False
        else:
            return True

    @staticmethod
    def single_process_exit(process_name='', base_path=''):
        """
        @fun 结束进程锁控制
        @funName single_process_exit
        @funGroup
        @funVersion
        @funDescription 结束进程锁控制:
            1、结束单进程控制，删除锁文件；
            2、注意必须在程序执行完后一定要调用这个函数，否则会导致一直锁住

        @funParam {string} process_name 进程锁的进程名，默认值为''；如果为''代表获取执行程序的模块名
        @funParam {string} base_path 进程锁文件指定的路径，默认值为''；如果为''代表获取执行程序的模块文件目录

        """
        global SINGLE_PROCESS_PID_FILE_LIST
        if not RunTools.var_defined("SINGLE_PROCESS_PID_FILE_LIST"):
            SINGLE_PROCESS_PID_FILE_LIST = {}
        # 要建立锁的文件名
        _lock_file = RunTools.single_process_get_lockfile(
            process_name=process_name, base_path=base_path)
        try:
            os.close(SINGLE_PROCESS_PID_FILE_LIST[_lock_file])
            os.remove(_lock_file)
            return
        except:
            raise sys.exc_info()[1]

    @staticmethod
    @contextmanager
    def single_process_with(process_name='', base_path='', is_try_del_lockfile=False,
                            logger=None, log_level=EnumLogLevel.WARNING, exit_code=1):
        """
        @fun 单进程控制的with简单模式
        @funName single_process_with
        @funGroup
        @funVersion
        @funDescription 封装with模式的调用方式来实现单进程控制

        @funParam {string} process_name 进程锁的进程名，默认值为''；如果为''代表获取执行程序的模块名
        @funParam {string} base_path 进程锁文件指定的路径，默认值为''；如果为''代表获取执行程序的模块文件目录
        @funParam {bool} is_try_del_lockfile 是否尝试先删除锁文件（可以应对强制关闭进程未自动删除锁文件的情况）
        @funParam {object} logger 日志对象，如果为None代表不需要输出日志，传入对象需满足:
            1、标准logging的logger对象
            2、自定义的日志类对象，但应实现warning、error等的标准方法
        @funParam {EnumLogLevel} log_level 需要输出的自定义日志级别
        @funParam {int} exit_code 控制获取进程锁失败退出的错误码定义

        @funExample {Python} 参考示例:
            with RunTools.single_process_with():
                # 以下为需要执行的程序逻辑

        """
        _get_process_lock = RunTools.single_process_enter(process_name=process_name,
                                                          base_path=base_path, is_try_del_lockfile=is_try_del_lockfile)
        if not _get_process_lock:
            if logger is not None:
                # 打印日志
                _log_str = u'已存在一个"%s"进程在执行中，结束本进程' % process_name
                RunTools.writelog_by_level(logger=logger, log_str=_log_str, log_level=log_level)
            # 退出进程
            exit(exit_code)
        try:
            yield  # 处理程序逻辑
        finally:
            # 退出进程，打印日志
            if logger is not None:
                _log_str = u'进程"%s"结束退出，释放进程锁' % process_name
                RunTools.writelog_by_level(logger=logger, log_str=_log_str, log_level=log_level)
            try:
                RunTools.single_process_exit(process_name=process_name, base_path=base_path)
            except:
                # 出现异常，写日志，同时抛出异常
                if logger is not None:
                    _log_str = u'进程"%s"结束时释放进程锁发生异常：%s' % (process_name, traceback.format_exc())
                    RunTools.writelog_by_level(logger=logger, log_str=_log_str, log_level=log_level)
                raise sys.exc_info()[1]


class NullObj(object):
    """
    @class 空对象定义类
    @className NullObj
    @classGroup
    @classVersion
    @classDescription 用于动态增加属性的使用场景

    @classExample {Python} 参考示例:
        msg_obj = NullObj()
        msg_obj.text = u'动态添加属性'

    """
    pass


class CResult(object):
    """
    @class 通用错误类
    @className CResult
    @classGroup generic
    @classVersion 0.9.0
    @classDescription 通用错误类定义，便于规范所有的错误信息返回判断标准，可直接在该类的实例对象上直接添加其他返回值

    @classExample {Python} 使用示例:
        def fun():
            result = CResult(0,"成功")
            result.job = "NewJob"
            result.k1 = 10
            return result

    """

    def __init__(self, code=0, msg=u'成功', error=None, trace_str=''):
        """
        @fun 构造函数
        @funName __init__
        @funGroup
        @funVersion
        @funDescription 设置类的基础参数

        @funParam {int} code 错误码，0代表成功，其余代表失败
        @funParam {string} msg 错误信息描述
        @funParam {array} error 发生异常时的sys.exc_info()三元组对象(type, value, traceback):
            type-从获取到的异常中得到类型名称，它是BaseException 的子类
            value-捕获到的异常实例
            traceback-异常跟踪对象，可以用traceback.print_tb()打印具体信息
        @funParam {string} trace_str 错误追踪堆栈日志，异常时的traceback.format_exc()

        """
        self.code = code
        self.msg = msg
        self.error = error
        self.trace_str = trace_str

    def copy_to(self, dest_obj):
        """
        @fun 复制结果对象的标准返回值到新对象中
        @funName copy_to
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 简单数据类型（int、string）只要共享地址即可，因为对变量重新复制会指向新的地址，
            不会影响原来的变量值；复杂数据类型（dict等）要通过deepcopy方式拷贝，避免同一内存信息改变互相影响

        @funParam {NullObj} dest_obj 要复制到的对象

        """
        dest_obj.code = self.code
        dest_obj.msg = self.msg
        dest_obj.error = copy.deepcopy(self.error)
        dest_obj.trace_str = self.trace_str


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    # 测试
    pass
