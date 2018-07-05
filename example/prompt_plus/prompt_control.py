#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import time

sys.path.append("../../snakerlib")
from snakerlib.simple_log import *
from snakerlib.prompt_plus import *
from snakerlib.generic import *


#############################
# 通用的logger
#############################
_logger = Logger(conf_file_name=None, logger_name=EnumLoggerName.Console.value,
                 config_type=EnumLoggerConfigType.JSON_STR)

#############################
# 处理函数的定义
#############################


def on_abort(message=''):
    """Ctrl + C : abort,取消本次输入"""
    print('on_abort: %s' % message)
    return 'on_abort done!'


def on_exit(message=''):
    """Ctrl + D : exit,关闭命令行"""
    print('on_exit: %s' % message)
    return 'on_exit done!'


def default_cmd_dealfun(message='', cmd='', cmd_para=''):
    """默认命令处理函数"""
    print('cmd not define: message[%s], cmd[%s], cmd_para[%s]' % (message, cmd, cmd_para))
    return 'default_cmd_dealfun done!'


def dir_cmd_dealfun(message='', cmd='', cmd_para=''):
    """dir命令的处理函数"""
    print('dir: message[%s], cmd[%s], cmd_para[%s]' % (message, cmd, cmd_para))
    return 'dir_cmd_dealfun done!'


def common_cmd_dealfun(message='', cmd='', cmd_para=''):
    """通用命令处理函数，持续10秒每秒输出一个wait的信息"""
    print('common: message[%s], cmd[%s], cmd_para[%s]' % (message, cmd, cmd_para))
    if cmd == 'wait':
        _i = 0
        while _i < 10:
            _logger.info('wait ' + str(_i))
            _i = _i + 1
            time.sleep(1)
    return 'common_cmd_dealfun done!'


def help_cmd_dealfun(message='', cmd='', cmd_para=''):
    """帮助命令，输出提示信息"""
    return cmd_para_descript


#############################
# 定义命令行参数
#############################
cmd_para_descript = u"""可使用的命令清单如下：
\thelp
\tdir para1=value11 para2=value21
\tcomshort -a value1a -b -c 或 -bc
\tcomlong -abc value1abc -bcd -ci
\tcommix para1=value11 para2=value21 -a value1a -b -c -abc value1abc -bcd -ci
\twait (持续10秒)
"""

test_cmd_para = {
    'help': {
        'deal_fun': help_cmd_dealfun,
        'name_para': None,
        'short_para': None,
        'long_para': None
    },
    'dir': {
        'deal_fun': dir_cmd_dealfun,
        'name_para': {
            'para1': ['value11', 'value12'],
            'para2': ['value21', 'value22']
        },
        'short_para': dict(),
        'long_para': dict()
    },
    'comshort': {
        'deal_fun': common_cmd_dealfun,
        'name_para': None,
        'short_para': {
            'a': ['value1a', 'value2a'],
            'b': None,
            'c': []
        },
        'long_para': dict()
    },
    'comlong': {
        'deal_fun': common_cmd_dealfun,
        'name_para': None,
        'short_para': None,
        'long_para': {
            'abc': ['value1abc', 'value2abc'],
            'bcd': None,
            'ci': []
        }
    },
    'commix': {
        'deal_fun': common_cmd_dealfun,
        'name_para': {
            'para1': ['value11', 'value12'],
            'para2': ['value21', 'value22']
        },
        'short_para': {
            'a': ['value1a', 'value2a'],
            'b': None,
            'c': []
        },
        'long_para': {
            'abc': ['value1abc', 'value2abc'],
            'bcd': None,
            'ci': []
        }
    },
    'wait': {
        'deal_fun': common_cmd_dealfun,
        'name_para': None,
        'short_para': None,
        'long_para': None
    },
}


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    tips = u'命令处理服务(输入过程中可通过Ctrl+C取消输入，通过Ctrl+D退出命令行处理服务)'

    #############################
    # 外部程序自己控制命令循环
    #############################
    prompt1 = PromptPlus(
        message='请输入>',
        default='help',  # 默认输入值
        cmd_para=test_cmd_para,  # 命令定义参数
        default_dealfun=default_cmd_dealfun,  # 默认处理函数
        on_abort=on_abort,  # Ctrl + C 取消本次输入执行函数
        on_exit=on_exit  # Ctrl + D 关闭命令行执行函数
    )
    # 自己输出提示信息
    print(tips)
    # 循环使用prompt_once一个获取命令和执行
    while True:
        prompt1_result = prompt1.prompt_once(default='help')
        print('prompt1_result: %s', prompt1_result.msg)
        if prompt1_result.code == 2:
            break
    # 结束提示循环
    print('prompt1 stop！')

    #############################
    # 自动命令循环模式-同步
    #############################
    prompt1.start_prompt_service(
        tips=tips + '\n当前模式为同步模式',
        is_async=False,
        is_print_async_execute_info=True
    )

    #############################
    # 自动命令循环模式-异步
    #############################
    prompt1.start_prompt_service(
        tips=tips + '\n当前模式为异步模式',
        is_async=True,
        is_print_async_execute_info=True
    )
