#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : simple_log_test.py

from generic import FileTools
from simple_log import *


__MoudleName__ = 'simple_log_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/1/29'


_TEMP_DIR = '../Temp/simple_log_test/'


def test_case1():
    # 测试单日志最基本功能，日志输出，变更日志级别，修改日志格式
    # 删除临时日志
    try:
        FileTools.remove_file(_TEMP_DIR + 'test_case1.json')
    except:
        pass

    try:
        FileTools.remove_files(path=_TEMP_DIR + 'log/', regex_str='test_case1*')
    except:
        pass

    _logger = Logger(conf_file_name=_TEMP_DIR + 'test_case1.json',
                                logger_name=EnumLoggerName.ConsoleAndFile.value,
                                logfile_path=_TEMP_DIR + 'log/test_case1.log')
    # ConsoleAndFile 的配置level为DEBUG，但对应的ConsoleHandler的level为DEBUG，FileHandler的level为INFO
    # 日志是否显示会根据logger的level和handler的level，以级别比较高的匹配输出
    # 注意默认root的handler应该为空，否则无论如何都会执行root的输出，如果自己又另外指定了输出，那就会有2个相同输出日志
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case1:write_log:DEBUG:1:界面应显示本日志，文件不应显示本日志')
    _logger.debug(log_str='test_case1:write_log:DEBUG:1-1:界面应显示本日志，文件不应显示本日志')
    _logger.write_log(log_level=EnumLogLevel.INFO,
                      log_str='test_case1:write_log:INFO:2:界面应显示本日志，文件应显示本日志')
    _logger.info(log_str='test_case1:write_log:INFO:2-1:界面应显示本日志，文件应显示本日志')

    # 修改ConsoleAndFile的level为INFO，handler仍不变
    _logger.set_logger_level(log_level=EnumLogLevel.INFO)
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case1:write_log:DEBUG:3:界面不应显示本日志，文件不应显示本日志')
    _logger.write_log(log_level=EnumLogLevel.INFO,
                      log_str='test_case1:write_log:INFO:4:界面应显示本日志，文件应显示本日志')

    # 修改ConsoleAndFile的level为DEBUG, FileHandler的level为WARNING
    _logger.set_logger_level(log_level=EnumLogLevel.DEBUG)
    for _handler in _logger.base_logger.handlers:
        if _handler.name == 'FileHandler':
            _logger.set_handler_log_level(handler=_handler, log_level=EnumLogLevel.WARNING)
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case1:write_log:DEBUG:5:界面应显示本日志，文件不应显示本日志')
    _logger.write_log(log_level=EnumLogLevel.WARNING,
                      log_str='test_case1:write_log:WARNING:6:界面应显示本日志，文件应显示本日志')

    #  修改整个日志级别为INFO
    _logger.set_level(log_level=EnumLogLevel.INFO)
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case1:write_log:DEBUG:7:界面不应显示本日志，文件不应显示本日志')
    _logger.write_log(log_level=EnumLogLevel.INFO,
                      log_str='test_case1:write_log:INFO:8:界面应显示本日志，文件应显示本日志')

    # 修改日志类型为Console，日志级别应根据配置文件恢复原状态（DEBUG）
    _logger.change_logger_name(logger_name=EnumLoggerName.Console.value)
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case1:write_log:DEBUG:9:界面应显示本日志，文件不应显示本日志')

    # 修改日志输出格式
    _logger.set_logger_formater(format_str='[%(asctime)s]%(message)s')
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case1:write_log:DEBUG:9:格式发生变化，界面应显示本日志，文件不应显示本日志')

    del _logger


def test_case2():
    # 测试多个日志类相互影响的情况
    try:
        FileTools.remove_file(_TEMP_DIR + 'test_case2.json')
    except:
        pass
    try:
        FileTools.remove_file(_TEMP_DIR + 'test_case2-1.json')
    except:
        pass

    try:
        FileTools.remove_files(path=_TEMP_DIR + 'log/', regex_str='test_case2*')
    except:
        pass
    try:
        FileTools.remove_files(path=_TEMP_DIR + 'log/', regex_str='test_case2-1*')
    except:
        pass

    _logger = Logger(conf_file_name=_TEMP_DIR + 'test_case2.json',
                                logger_name=EnumLoggerName.ConsoleAndFile.value,
                                logfile_path=_TEMP_DIR + 'log/test_case2.log')
    # ConsoleAndFile 的配置level为DEBUG，但对应的ConsoleHandler的level为DEBUG，FileHandler的level为INFO
    # 日志是否显示会根据logger的level和handler的level，以级别比较高的匹配输出
    # 注意默认root的handler应该为空，否则无论如何都会执行root的输出，如果自己又另外指定了输出，那就会有2个相同输出日志
    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case2:write_log:DEBUG:1:界面应显示本日志，文件不应显示本日志')
    _logger.debug(log_str='test_case2:write_log:DEBUG:1-1:界面应显示本日志，文件不应显示本日志')
    _logger.write_log(log_level=EnumLogLevel.INFO,
                      log_str='test_case2:write_log:INFO:2:界面应显示本日志，文件应显示本日志')
    _logger.info(log_str='test_case2:write_log:INFO:2-1:界面应显示本日志，文件应显示本日志')

    # 新增logger，但与原logger的loggername一样，实际上会互相影响，同时如果handler一样，也会受影响
    _logger1 = Logger(conf_file_name=_TEMP_DIR + 'test_case2-1.json',
                     logger_name=EnumLoggerName.ConsoleAndFile.value,
                     logfile_path=_TEMP_DIR + 'log/test_case2-1.log')
    _logger1.set_level(log_level=EnumLogLevel.DEBUG)

    _logger.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case2:write_log:DEBUG:3:界面应显示本日志，文件不应显示本日志,但实际受logger1影响，也记录了日志；本应记录在日志1中，但受影响记录在日志2中')
    _logger.write_log(log_level=EnumLogLevel.INFO,
                      log_str='test_case2:write_log:INFO:4:界面应显示本日志，文件应显示本日志；本应记录在日志1中，但受影响记录在日志2中')
    _logger1.write_log(log_level=EnumLogLevel.DEBUG,
                      log_str='test_case2:write_log:DEBUG:5-1:界面应显示本日志，文件应显示本日志')
    _logger1.write_log(log_level=EnumLogLevel.INFO,
                      log_str='test_case2:write_log:INFO:6-1:界面应显示本日志，文件应显示本日志')

    del _logger

    _logger1.write_log(log_level=EnumLogLevel.DEBUG,
                       log_str='test_case2:write_log:DEBUG:6-1:界面应显示本日志，文件应显示本日志')
    _logger1.write_log(log_level=EnumLogLevel.INFO,
                       log_str='test_case2:write_log:INFO:7-1:界面应显示本日志，文件应显示本日志')

    del _logger1



if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    # 测试单日志最基本功能，日志输出，变更日志级别，修改日志格式
    test_case1()

    # 测试多个日志类相互影响的情况
    test_case2()


