#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : generic_test.py

from generic import DebugTools, ExceptionTools, StringTools
from self_unit_test.generic_out_test import test_debugtools
from simple_log import *

__MoudleName__ = 'generic_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/1/29'


def test_debugtools_1():
    # 测试DebugTools  -  跨模块的打印 - 增加日志类的干扰
    _TEMP_DIR = '../Temp/generic_test/'
    _logger = Logger(conf_file_name=_TEMP_DIR + 'test_debugtools_1.json',
                     logger_name=EnumLoggerName.ConsoleAndFile.value,
                     logfile_path=_TEMP_DIR + 'log/test_debugtools_1.log')
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_debugtools_1:write_log:DEBUG:1:界面应显示本日志，文件不应显示本日志')
    _logger.write_log(log_level=EnumLogLevel.INFO,
                      log_str='test_debugtools_1:write_log:INFO:2:界面应显示本日志，文件应显示本日志')
    del _logger

    DebugTools.set_debug(True)
    DebugTools.debug_print("自己本模块的打印")
    test_debugtools()
    return


def test_excepitontools_1():
    # 测试异常工具的处理机制
    _TEMP_DIR = '../Temp/generic_test/'
    _logger2 = Logger(
        conf_file_name=_TEMP_DIR + 'test_excepitontools_1.json',
        logger_name=EnumLoggerName.ConsoleAndFile.value,
        logfile_path=_TEMP_DIR + 'log/test_excepitontools_1.log',
        call_level=1
    )
    _logger2.set_level(log_level=EnumLogLevel.DEBUG)
    _logger2.write_log(log_level=EnumLogLevel.INFO, log_str='test log', call_level=0)

    with ExceptionTools.ignored_all(logger=_logger2, self_log_msg='测试异常处理：'):
        print("test_excepitontools_1 step 1")
        print("test_excepitontools_1 step 2")
        print("test_excepitontools_1 step 3")
        1/0
        print("test_excepitontools_1 step 4 - 不应打印")
        print("test_excepitontools_1 step 5 - 不应打印")

    print("test_excepitontools_1 step 6 - 退出后的打印信息")

    del _logger2



if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    test_debugtools_1()

    test_excepitontools_1()





