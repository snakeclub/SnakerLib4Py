#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : redirect_stdout.py


import sys
import threading
import traceback
from enum import Enum


__MoudleName__ = 'redirect_stdout'
__MoudleDesc__ = '重定向标准界面输出的处理模块'
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/2/27'


class EnumOriginalStdoutWriteType(Enum):
    """
    @enum 对原始的stdout的输出方式
    @enumName EnumOriginalStdoutWriteType
    @enumDescription 描述

    """
    Before = 'Before'  # 在重定向前输出
    After = 'After'  # 在重定向处理后输出
    NoWrite = 'NoWrite'  # 不输出


class EnumRedirectOutputHandlerType(Enum):
    """
    @enum 重定向输出句柄类型
    @enumName EnumRedirectOutputHandlerType
    @enumDescription 描述

    """
    Consloe = 'Consloe'  # 屏幕输出句柄
    File = 'File'  # 文件输出句柄
    String = 'String'  # 文本对象输出句柄
    StringList = 'StringList'  # 文本数组输出句柄


class RedirectOutputHandler(object):
    """
    @class 输出重定向句柄
    @className RedirectOutputHandler
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 定义RedirectOutput所需输出的句柄，实现真正的输出逻辑，使用方法有两类：
        1、直接使用该类生成默认的重定向句柄对象
        2、继承该类，重载write和flush函数

    """

    #############################
    # 私有变量
    #############################
    _handler_type = None  # 句柄类型
    _ouput_obj = ''  # 输出对象
    _encoding = ''  # 编码方式

    #############################
    # 公共函数
    #############################
    def __init__(self, handler_type=EnumRedirectOutputHandlerType.Consloe, ouput_obj=None,
                 is_flush=False, encoding='utf-8'):
        """
        @fun 构造函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {EnumRedirectOutputHandlerType} handler_type 句柄类型
        @funParam {object} ouput_obj 输出对象，根据handler_type不同传入不同参数
            Consloe ： 无需传入
            File ： string, 传入文件名路径
            String ：list[0]=string，传入初始字符串，后续在该基础上逐步扩展（注意，是一个长度为1的数组）
            StringList ： list()，传入初始字符对象列表

        """
        self._handler_type = handler_type
        self._ouput_obj = ouput_obj
        self._encoding = encoding
        if is_flush:
            self.flush()

    def write(self, data):
        """
        @fun 输出函数（实现标准输出必须包括的函数）
        @funName write
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} data 要输出的文本

        """
        if self._handler_type == EnumRedirectOutputHandlerType.Consloe:
            sys.__stdout__.write(data)
        elif self._handler_type == EnumRedirectOutputHandlerType.String:
            self._ouput_obj += data + '\n'  # 需后续判断是否需要加换行
        elif self._handler_type == EnumRedirectOutputHandlerType.StringList:
            self._ouput_obj.extend(data)
        else:
            # 文件模式，追加到结尾
            try:
                with open(file=self._ouput_obj, mode='a+', encoding=self._encoding) as _file:
                    _file.write(data + '\n')
            except:
                # 出现异常，输出异常信息到界面
                sys.stderr.write(traceback.format_exc())

    def flush(self):
        """
        @fun 清空输入缓存（实现标准输出必须包括的函数）
        @funName flush
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        """
        if self._handler_type == EnumRedirectOutputHandlerType.Consloe:
            sys.__stdout__.flush()
        elif self._handler_type == EnumRedirectOutputHandlerType.String:
            self._ouput_obj = ''
        elif self._handler_type == EnumRedirectOutputHandlerType.StringList:
            self._ouput_obj.clear()
        else:
            # 文件模式，覆盖文件
            try:
                with open(file=self._ouput_obj, mode='w', encoding=self._encoding) as _file:
                    pass
            except Exception:
                # 出现异常，输出异常信息到界面
                sys.stderr.write(traceback.format_exc())


class RedirectOutput(object):
    """
    @class 输出重定向类
    @className RedirectOutput
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 类功能描述

    @classExample {Python} 示例名:
        类使用参考示例

        https://www.cnblogs.com/turtle-fly/p/3280519.html

    """

    #############################
    # 内部变量
    #############################
    _buffer = ''
    _original_stdout = None
    _original_stdout_write_type = None
    _write_lock = threading.RLock()  # 进行输出信息处理的线程锁，支持多线程
    _run_in_bg_thread = False  # 是否通过后台线程执行（快速返回）
    _output_handlers = list()  # 重定向输出句柄清单

    #############################
    # 公共函数
    #############################

    def __init__(self, auto_start=False, original_stdout=None,
                 original_stdout_write_type=EnumOriginalStdoutWriteType.NoWrite,
                 run_in_bg_thread=False, output_handlers=list()
                 ):
        """
        @fun 构造函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {object} original_stdout 初始输出对象，如果为None则记录为sys.stdout
        @funParam {EnumOriginalStdoutWriteType} original_stdout_write_type 对原始的stdout的输出方式

        @funReturn {返回值类型} 返回值说明

        @funExample {代码格式} 示例名:
            函数使用参考示例

        """
        self._buffer = ''
        if original_stdout is None:
            self._original_stdout = sys.stdout
        else:
            self._original_stdout = original_stdout
        self._original_stdout_write_type = original_stdout_write_type
        self._run_in_bg_thread = run_in_bg_thread
        self._output_handlers = output_handlers
        if auto_start:
            # 自动启动输出重定向
            self.start_redirect()

    def write(self, data):
        """
        @fun 输出函数（实现标准输出必须包括的函数）
        @funName write
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} data 要输出的文本

        """
        self._buffer += data
        pass

    def flush(self):
        """
        @fun 清空输入缓存（实现标准输出必须包括的函数）
        @funName flush
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        """
        self._buffer = ''

    def start_redirect(self):
        """
        @fun 启动重定向
        @funName start_redirct
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 该功能与sys.stdout = RedirectOutput()相同

        """
        sys.stdout = self

    def stop_redirect(self):
        """
        @fun 停止重定向
        @funName stop_redirct
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 该功能恢复输出对象为原对象

        """
        sys.stdout = self._original_stdout


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    print(sys.stdin)
    sys.stdin = None
    print(sys.stdin)

    print(sys.__stdin__)
