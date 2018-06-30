#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : simple_stream_test.py


from simple_stream import *
from simple_log import *
from generic import *


__MoudleName__ = 'simple_stream_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/2/6'


# 通用的logger
_logger = Logger(conf_file_name=None, logger_name=EnumLoggerName.Console.value, config_type=EnumLoggerConfigType.JSON_STR)


# 通用的流通知函数
def dealer_exception_fun(stream_tag='', stream_obj=None, deal_obj=None, position=0,
                         dealer_handle=None, error_obj=None, trace_str=''):
    _logger.info(
        'dealer_exception_fun\nstream_tag: %s\nstream_obj: %s\ndeal_obj: %s\nposition: %s\ndealer_handle: %s\nerror_obj: %s\ntrace_str: %s' % (
            stream_tag,
            StringTools.format_obj_property_str(stream_obj, is_deal_subobj=True),
            str(deal_obj),
            str(position),
            str(dealer_handle),
            str(error_obj),
            trace_str
        )
    )


def stream_closed_fun(stream_tag='', stream_obj=None, position=0, closed_status=None):
    _logger.info(
        'stream_closed_fun\nstream_tag: %s\nstream_obj: %s\nposition: %s\nclosed_status: %s' % (
            stream_tag,
            StringTools.format_obj_property_str(stream_obj, is_deal_subobj=True),
            str(position),
            closed_status.value
        )
    )


# 字符流的处理函数定义
def string_stream_dealer_1(deal_obj, position):
    _logger.info('string_stream_dealer_1: position:%s : %s' % (str(position), deal_obj))


def string_stream_dealer_2(deal_obj, position):
    _logger.info('string_stream_dealer_2: position:%s : %s' % (str(position), deal_obj))


def string_stream_dealer_x(deal_obj, position):
    _logger.info('string_stream_dealer_x: position:%s : %s' % (str(position), deal_obj))
    if deal_obj == '中':
        _logger.info('测试抛出异常')
        raise TabError(u'测试异常')


def string_stream_dealer_x1(deal_obj, position):
    _logger.info('string_stream_dealer_x1: position:%s : %s' % (str(position), deal_obj))
    # 暂停半秒，用于测试暂停、恢复、关闭
    time.sleep(0.2)


@StringStream.stream_decorator(stop_by_excepiton=False, logger=_logger, dealer_exception_fun=dealer_exception_fun, stream_closed_fun=stream_closed_fun,
                         stream_tag='stream_dealer', is_sync=True, seek_position=None,
                         move_next_step=None, move_forward_step=None)
def string_stream_dealer_3(deal_obj=None, position=0, str_obj='', my_para=''):
    _logger.info('string_stream_dealer_3: my_para : %s\n str_obj : %s' % (my_para, str_obj))
    _logger.info('string_stream_dealer_3: position:%s : %s' % (str(position), deal_obj))


@StringStream.stream_decorator(stop_by_excepiton=False, logger=_logger, dealer_exception_fun=dealer_exception_fun, stream_closed_fun=stream_closed_fun,
                         stream_tag='stream_dealer', is_sync=True, seek_position=None,
                         move_next_step=None, move_forward_step=None)
def string_stream_dealer_4(deal_obj=None, position=0, str_obj='', my_para=''):
    _logger.info('string_stream_dealer_4: position:%s : %s' % (str(position), deal_obj))
    if deal_obj == '中':
        _logger.info('测试抛出异常不中断')
        raise TabError(u'测试异常')


@StringStream.stream_decorator(stop_by_excepiton=True, logger=_logger, dealer_exception_fun=dealer_exception_fun, stream_closed_fun=stream_closed_fun,
                         stream_tag='stream_dealer', is_sync=True, seek_position=None,
                         move_next_step=None, move_forward_step=None)
def string_stream_dealer_5(deal_obj=None, position=0, str_obj='', my_para=''):
    _logger.info('string_stream_dealer_5: position:%s : %s' % (str(position), deal_obj))
    if deal_obj == '中':
        _logger.info('测试抛出异常中断')
        raise TabError(u'测试异常')


@StringStream.stream_decorator(stop_by_excepiton=False, logger=_logger, dealer_exception_fun=dealer_exception_fun, stream_closed_fun=stream_closed_fun,
                         stream_tag='stream_dealer', is_sync=True, seek_position=6,
                         move_next_step=None, move_forward_step=None)
def string_stream_dealer_6(deal_obj=None, position=0, str_obj='', my_para=''):
    _logger.info('string_stream_dealer_6: position:%s : %s' % (str(position), deal_obj))


@StringStream.stream_decorator(stop_by_excepiton=False, logger=_logger, dealer_exception_fun=dealer_exception_fun, stream_closed_fun=stream_closed_fun,
                         stream_tag='stream_dealer', is_sync=False, seek_position=None,
                         move_next_step=None, move_forward_step=None)
def string_stream_dealer_7(deal_obj=None, position=0, str_obj='', my_para=''):
    _logger.info('string_stream_dealer_7: position:%s : %s' % (str(position), deal_obj))


def test_string_stream_1():
    # 修饰符方式
    _logger.info('修饰符方式-同步-正常情况')
    string_stream_dealer_3(None, 0, str_obj=u'test my string 加上中文', my_para='my_para3')

    _logger.info('修饰符方式-同步-异常但不中止')
    string_stream_dealer_4(None, 0, str_obj=u'test my string 加上中文', my_para='my_para4')

    _logger.info('修饰符方式-同步-异常中止')
    string_stream_dealer_5(None, 0, str_obj=u'test my string 加上中文', my_para='my_para5')

    _logger.info('修饰符方式-同步-跳转到指定位置')
    string_stream_dealer_6(None, 0, str_obj=u'test my string 加上中文', my_para='my_para6')

    _logger.info('修饰符方式-异步-正常情况')
    string_stream_dealer_7(None, 0, str_obj=u'test my string 加上中文', my_para='my_para7')
    _logger.info('修饰符方式-异步-正常情况-检查是否异步处理')
    # 为避免程序结束，等待10秒
    time.sleep(10)


def test_string_stream_2():
    _logger.info('非修饰符方式-同步-正常情况')
    _stream1 = StringStream(stop_by_excepiton=False, logger=_logger, dealer_exception_fun=dealer_exception_fun, stream_closed_fun=stream_closed_fun)
    _stream1.add_dealer(string_stream_dealer_1, string_stream_dealer_2)
    _stream1.start_stream(stream_tag='string_stream1', is_sync=True, is_pause=False,
                     seek_position=None, move_next_step=None, move_forward_step=None, str_obj='test string stream 包括中文')

    _logger.info('非修饰符方式-同步-跳转到指定位置')
    _stream1.start_stream(stream_tag='string_stream2', is_sync=True, is_pause=False,
                          seek_position=5, move_next_step=None, move_forward_step=None,
                          str_obj='test string stream 包括中文')

    _logger.info('非修饰符方式-同步-异常但不中止')
    _stream1.add_dealer(string_stream_dealer_x)
    _stream1.del_dealer(string_stream_dealer_1, string_stream_dealer_2)
    _stream1.start_stream(stream_tag='string_stream3', is_sync=True, is_pause=False,
                          seek_position=None, move_next_step=None, move_forward_step=None,
                          str_obj='test中文')

    _logger.info('非修饰符方式-同步-异常中止')
    _stream2 = StringStream(stop_by_excepiton=True, logger=_logger, dealer_exception_fun=dealer_exception_fun,
                            stream_closed_fun=stream_closed_fun)
    _stream2.add_dealer(string_stream_dealer_x)
    _stream2.start_stream(stream_tag='string_stream4', is_sync=True, is_pause=False,
                          seek_position=None, move_next_step=None, move_forward_step=None,
                          str_obj='test中文')


def test_string_stream_3():
    _logger.info('非修饰符方式-异步-正常情况')
    _stream1 = StringStream(stop_by_excepiton=False, logger=_logger, dealer_exception_fun=dealer_exception_fun,
                            stream_closed_fun=stream_closed_fun)
    _stream1.add_dealer(string_stream_dealer_1)
    _stream1.start_stream(stream_tag='string_stream1', is_sync=False, is_pause=False,
                          seek_position=None, move_next_step=None, move_forward_step=None,
                          str_obj='test string stream 包括中文')
    time.sleep(5)

    _logger.info('非修饰符方式-异步-暂停及关闭')
    _stream1.clear_dealer()
    _stream1.add_dealer(string_stream_dealer_x1)
    _stream1.start_stream(stream_tag='string_stream1', is_sync=False, is_pause=False,
                          seek_position=None, move_next_step=None, move_forward_step=None,
                          str_obj='test string stream 包括中文')
    _stream1.pause_stream('string_stream1')
    _logger.info('已暂停')
    time.sleep(2)
    _logger.info('重新恢复')
    _stream1.resume_stream('string_stream1')
    time.sleep(2)
    _logger.info('关闭流')

    try:
        _stream1.stop_stream('string_stream1')
    except:
        _logger.error(str(sys.exc_info()))
        pass

    time.sleep(5)



if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    test_string_stream_1()

    # test_string_stream_2()

    # test_string_stream_3()
