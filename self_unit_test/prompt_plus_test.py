#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : prompt_plus_test.py

from simple_log import *
from prompt_plus import *
from generic import *

from prompt_toolkit import prompt, Prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
from prompt_toolkit.patch_stdout import patch_stdout

# 通用的logger
_logger = Logger(conf_file_name=None, logger_name=EnumLoggerName.Console.value, config_type=EnumLoggerConfigType.JSON_STR)

__MoudleName__ = 'prompt_plus_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/2/22'


def on_abort(message=''):
    print('on_abort: %s' % message)
    return 'on_abort done!'


def on_exit(message=''):
    print('on_exit: %s' % message)
    return 'on_exit done!'


def default_cmd_dealfun(message='', cmd='', cmd_para=''):
    print('cmd not define: message[%s], cmd[%s], cmd_para[%s]' % (message, cmd, cmd_para))
    return 'default_cmd_dealfun done!'


def dir_cmd_dealfun(message='', cmd='', cmd_para=''):
    print('dir: message[%s], cmd[%s], cmd_para[%s]' % (message, cmd, cmd_para))
    return 'dir_cmd_dealfun done!'


def common_cmd_dealfun(message='', cmd='', cmd_para=''):
    print('common: message[%s], cmd[%s], cmd_para[%s]' % (message, cmd, cmd_para))
    if cmd == 'mix':
        _i = 0
        while _i < 10:
            _logger.info('wait ' + str(_i))
            _i = _i + 1
            time.sleep(1)
    return 'common_cmd_dealfun done!'

cmd_para = {
    'dir': {
        'deal_fun': dir_cmd_dealfun,
        'name_para': {
            'para1': ['value11', 'value12'],
            'para2': ['value21', 'value22']
        },
        'short_para': dict(),
        'long_para': dict()
    },
    'dict': {
        'deal_fun': common_cmd_dealfun,
        'name_para': None,
        'short_para': {
            'a': ['value1a', 'value2a'],
            'b': None,
            'c': []
        },
        'long_para': dict()
    },
    'cmd': {
        'deal_fun': common_cmd_dealfun,
        'name_para': None,
        'short_para': None,
        'long_para': {
            'abc': ['value1abc', 'value2abc'],
            'bcd': None,
            'ci': []
        }
    },
    'mix': {
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
    }
}


def test_normal():
    _prompt = PromptPlus(
        message='mytest>', cmd_para=cmd_para, ignore_case=False, default_dealfun=default_cmd_dealfun,
        on_abort=on_abort, on_exit=on_exit, logger=_logger, multiline=True,
        enable_history_search=True,
        enable_cmd_auto_complete=True
    )
    # _result = _prompt.prompt_once('newtest>', default='dir', is_password=False)
    # print(StringTools.format_obj_property_str(deal_obj=_result, is_deal_subobj=True, max_level=1))

    _prompt.start_prompt_service(
        tips=u'命令处理服务(输入过程中可通过Ctrl+C取消输入，通过Ctrl+D退出命令行处理服务)',
        is_async=False
    )

def test_async():
    _prompt = PromptPlus(
        message='mytest>', cmd_para=cmd_para, ignore_case=False, default_dealfun=default_cmd_dealfun,
        on_abort=on_abort, on_exit=on_exit, logger=_logger, multiline=False,
        enable_history_search=True,
        enable_cmd_auto_complete=True
    )

    _prompt.start_prompt_service(
        tips=u'命令处理服务(输入过程中可通过Ctrl+C取消输入，通过Ctrl+D退出命令行处理服务)',
        is_async=True,
        is_print_async_execute_info=True
    )



if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    DebugTools.set_debug(True)

    # test_normal()
    # 测试颜色命令： mix  para1=abc para2="dd" para3=bcd "para1=ddd" -abc dddd aaaa -avbcde


    # cd C:\Users\hi.li\Desktop\工作\技术研究\Python\snakerlib\self_unit_test
    # python prompt_plus_test.py
    test_async()


