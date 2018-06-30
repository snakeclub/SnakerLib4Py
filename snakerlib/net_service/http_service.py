#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : http_service.py


from datetime import datetime
from time import mktime
from enum import Enum
from wsgiref.handlers import format_date_time
from net_service.tcpip_service import *
from generic import *


__MoudleName__ = 'http_service'
__MoudleDesc__ = 'Http协议的实现类'
__Version__ = '0.9.0'
__Author__ = 'snaker'
__Time__ = '2018/1/24'


class EnumHttpResquestType(Enum):
    """
    @enum Http协议请求类型
    @enumName EnumHttpResquestType
    @enumDescription Http协议请求类型

    """
    POST = 'POST'  # POST方法
    GET = 'GET'  # GET方法
    OPTIONS = 'OPTIONS'
    HEAD = 'HEAD'
    PUT = 'PUT'
    DELETE = 'DELETE'
    TRACE = 'TRACE'


class EnumHttpHeadType(Enum):
    """
    @enum http协议头类型
    @enumName EnumHttpHeadType
    @enumDescription http协议头类型

    """
    Request = 'Request'  # 请求报文
    Response = 'Response'  # 响应报文


class HttpService(TcpIpService):
    """
    @class Http协议实现类
    @className HttpService
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 继承TcpIpService类的HTTP协议处理实现类，提供使用HTTP协议进行网络通讯的基础支持:
        基础的服务功能及使用方法主要参考BaseServiceFW和TcpIpService类，继承类参考本源码注释

    """

    #############################
    # HttpService类特有的成员
    #############################

    @staticmethod
    def set_default_head_dict(request_para_list=dict(), response_para_list=dict(), ver='HTTP1.1',
                              req_type=EnumHttpResquestType.POST.value, url='', stat_code='200', stat_msg='OK'):
        """
        @fun 设置全局默认报文头
        @funName set_default_head_dict
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 设置了默认的报文头后，可以在调用send_data时无需生成和传入head_dict对象

        @funParam {dict} request_para_list 请求报文头参数字典，例如:
            request_para_list = {
                "Date": HttpService.get_http_datetime_format(datetime.now()),
                "Content-Length": "0"
            }
        @funParam {dict} response_para_list 响应报文头参数字典，例如:
            response_para_list = {
                "Date": HttpService.get_http_datetime_format(datetime.now()),
                "Content-Length":"0"
            }
        @funParam {string} ver Http协议的版本，例如'HTTP1.1'
        @funParam {string} req_type 请求类型，仅请求报文使用，可以用EnumHttpResquestType.POST.value传入
        @funParam {string} url 请求的url地址，仅请求报文使用
        @funParam {string} stat_code Http响应码，例如成功为200
        @funParam {string} stat_msg Http响应信息，例如成功为OK

        """
        RunTools.set_global_var(
            "__HttpServiceRequestHeadDict",
            HttpService.create_http_head(head_type=EnumHttpHeadType.Request, para_list=request_para_list,
                                         ver=ver, req_type=req_type, url=url, stat_code=stat_code, stat_msg=stat_msg)
        )
        RunTools.set_global_var(
            "__HttpServiceResponseHeadDict",
            HttpService.create_http_head(head_type=EnumHttpHeadType.Response, para_list=response_para_list,
                                         ver=ver, req_type=req_type, url=url, stat_code=stat_code, stat_msg=stat_msg)
        )

    @staticmethod
    def get_http_datetime_format(datetime_obj):
        """
        @fun 将指定的datetime转换为HTTP协议的日期格式
        @funName get_http_datetime_format
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 将指定的datetime转换为HTTP协议的日期格式

        @funParam {datetime} datetime_obj 要转换的日期对象，例如datetime.now()

        @funReturn {string} 返回的打印格式字符串，例如Wed, 22 Oct 2008 10:52:40 GMT

        """
        _stamp = mktime(datetime_obj.timetuple())
        return format_date_time(_stamp)  # --> Wed, 22 Oct 2008 10:52:40 GMT

    @staticmethod
    def create_http_head(head_type=EnumHttpHeadType.Request, para_list=dict(), ver='HTTP1.1',
                         req_type=EnumHttpResquestType.POST.value, url='', stat_code='200', stat_msg='OK'):
        """
        @fun 创建Http报文头对象
        @funName create_http_head
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {EnumHttpHeadType} head_type 报文头类型
        @funParam {dict} para_list 要加入的报文头参数字典，例如：
            para_list = {
                "Date":HttpService.get_http_datetime_format(datetime.now()),
                "Content-Length":"0"
            }
        @funParam {string} ver Http协议的版本，例如'HTTP1.1'
        @funParam {string} req_type 请求类型，'POST'、'GET'等，仅请求报文使用:
            可以使用EnumHttpResquestType.POST.value来简化调用
        @funParam {string} url 请求的url地址，仅请求报文使用
        @funParam {string} stat_code Http响应码，例如成功为200，仅响应报文使用
        @funParam {string} stat_msg Http响应新，例如成功为OK，仅响应报文使用

        @funReturn {object} Http报文头对象，格式为:
            head_dict.para = dict()
            head_dict.para['Request'] - 请求行,为一个对象，具有几个属性:
                req_type: string 请求方法GET POST等
                url：请求的URL
                ver：协议版本
            head_dict.para['Response'] - 响应行，为一个对象，具有几个属性:
                ver：协议版本
                stat_code：状态值，200等
                stat_msg：状态消息，OK等
            head_dict.para[para_key] - 其余字典key为头部字段名，value为字符串格式的头部字段值
            head_dict.upper_map = {} ： 处理辅助对象，与head_dict对应的大写映射字典，key为字段名的大写格式，value为字段名的获取格式

        """
        _head_dict = NullObj()
        _head_dict.para = dict()
        _head_dict.upper_map = dict()
        _head_dict.para[head_type.value] = NullObj()
        _head_dict.upper_map[head_type.value.upper()] = head_type.value
        _head_dict.para[head_type.value].ver = ver

        if head_type == EnumHttpHeadType.Request:
            # 请求
            _head_dict.para[head_type.value].req_type = req_type
            _head_dict.para[head_type.value].url = url
        else:
            # 响应
            _head_dict.para[head_type.value].stat_code = stat_code
            _head_dict.para[head_type.value].stat_msg = stat_msg

        # 其他报文体
        for _key in para_list:
            if _key != head_type.value:
                _head_dict.para[_key] = para_list[_key]
                _head_dict.upper_map[_key.upper()] = _key
        return _head_dict

    @staticmethod
    def get_http_head_str(head_dict):
        """
        @fun 获取Http报文头的发送字符串
        @funName get_http_head_str
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 转换为待发送的报文头字符串，用于显示或最终发送

        @funParam {object} head_dict http报文头对象（说明参考create_http_head的注释）

        @funReturn {string} 满足HTTP协议的报文头字符串

        """
        # 组织发送报文头
        _send_str = ''
        if EnumHttpHeadType.Response.value in head_dict.para.keys():
            # 返回值
            _send_str = '%s %s %s\r\n' % (
                head_dict.para[EnumHttpHeadType.Response.value].ver,
                head_dict.para[EnumHttpHeadType.Response.value].stat_code,
                head_dict.para[EnumHttpHeadType.Response.value].stat_msg
            )
        else:
            # 请求
            _send_str = '%s %s %s\r\n' % (
                head_dict.para[EnumHttpHeadType.Request.value].req_type,
                head_dict.para[EnumHttpHeadType.Request.value].url,
                head_dict.para[EnumHttpHeadType.Request.value].ver
            )
        for _key in head_dict.para:
            if _key not in (EnumHttpHeadType.Request.value, EnumHttpHeadType.Response.value):
                _send_str = _send_str + '%s:%s\r\n' % (_key, head_dict.para[_key])
        # 增加一个空行
        _send_str = _send_str + "\r\n"
        return _send_str

    @staticmethod
    def get_http_head(net_info):
        """
        @fun 从网络中获取HTTP报文头
        @funName get_http_head
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 按照HTTP协议，逐个字符获取报文头内容，直到报文头收取完整
        
        @funParam {object} net_info 网络连接信息（TcpIpNetInfo类）
        
        @funReturn {generic.CResult} 数据获取结果:
            result.code ：0-成功，4-获取数据超时，其他为获取失败
            result.head_dict ：获取到的报文头对象（说明参考create_http_head的注释）
            result.recv_time : datetime 实际开始接受时间
        
        """
        _result = CResult(code=0, msg=u'成功')
        _result.head_dict = NullObj()
        _result.head_dict.para = dict()
        _result.head_dict.upper_map = dict()
        _result.recv_time = None
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                logger=None,
                self_log_msg=u'循环获取HTTP报文头异常：',
                force_log_level=EnumLogLevel.ERROR
        ):
            # 循环获取所有报文头内容
            _get_line_bytes = b''
            while True:
                _read_result = TcpIpService.recv_data(net_info=net_info, recv_para=1)
                _result.recv_time = _read_result.recv_time
                if _read_result.code != 0:
                    # 出现异常，直接返回失败
                    _read_result.copy_to(_result)
                    return _result

                # 获取成功，判断是否回车换行
                if str(_read_result.data, 'ascii') == '\r':
                    continue
                elif str(_read_result.data, 'ascii') == '\n':
                    # 一行结束，开始处理行数据
                    if len(_get_line_bytes) == 0:
                        # 已到报文头结尾
                        return _result
                    elif len(_result.head_dict.para) == 0:
                        # 是第1行
                        _str_array = str(_get_line_bytes, 'ascii').split(' ')
                        if _str_array[0].upper()[0:4] == 'HTTP':
                            # 响应报文
                            _res_obj = NullObj()
                            _res_obj.ver = _str_array[0]
                            _res_obj.stat_code = _str_array[1]
                            _res_obj.stat_msg = _str_array[2]
                            _result.head_dict.para[EnumHttpHeadType.Response.value] = _res_obj
                            _result.head_dict.upper_map[EnumHttpHeadType.Response.value.upper()] \
                                = EnumHttpHeadType.Response.value
                        else:
                            # 请求报文
                            _req_obj = NullObj()
                            _req_obj.req_type = _str_array[0]
                            _req_obj.url = ''
                            _req_obj.ver = ''
                            if len(_str_array) > 1:
                                _req_obj.url = _str_array[1]
                            if len(_str_array) > 2:
                                _req_obj.ver = _str_array[2]
                            _result.head_dict.para[EnumHttpHeadType.Request.value] = _req_obj
                            _result.head_dict.upper_map[EnumHttpHeadType.Request.value.upper()] \
                                = EnumHttpHeadType.Request.value
                    else:
                        # 其他行
                        _str = str(_get_line_bytes, 'ascii')
                        _index = _str.find(':')
                        if _index == -1:
                            _result.head_dict.para[_str] = ""
                            _result.head_dict.upper_map[_str.upper()] = _str
                        else:
                            _result.head_dict.para[_str[0:_index]] = _str[_index + 1:]
                            _result.head_dict.upper_map[_str[0:_index].upper()] = _str[0:_index]
                    # 继续获取下一行
                    _get_line_bytes = b''
                    continue
                else:
                    # 继续加到行里
                    _get_line_bytes = _get_line_bytes + _read_result.data
        # 返回结果
        return _result

    @staticmethod
    def get_http_body(net_info, head_dict):
        """
        @fun 获取HTTP报文体数据
        @funName get_http_body
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 根据报文头的长度获取后续的报文体内容

        @funParam {object} net_info 网络连接信息（TcpIpNetInfo类）
        @funParam {object} head_dict Http报文头对象（说明参考create_http_head的注释）

        @funReturn {generic.CResult} 数据获取结果:
            result.code ：0-成功，4-获取数据超时，其他为获取失败
            result.body ：获取到的报文数据（bytes）
            result.recv_time : datetime 实际开始接受时间

        """
        _result = CResult(code=0, msg=u'成功')
        _result.body = None
        _result.recv_time = None
        _body_len = 0
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                logger=None,
                self_log_msg=u'获取HTTP报文体异常：',
                force_log_level=EnumLogLevel.ERROR
        ):
            if "Content-Length".upper() in head_dict.upper_map.keys():
                _body_len = int(head_dict.para[head_dict.upper_map["Content-Length".upper()]])
            if _body_len == 0:
                return _result
            _read_result = TcpIpService.recv_data(net_info, _body_len)
            _result.recv_time = _read_result.recv_time
            if _read_result.code != 0:
                _read_result.copy_to(_result)
            else:
                _result.body = _read_result.data
        # 返回结果
        return _result

    @staticmethod
    def send_http_head_and_body(net_info, head_dict, body=None):
        """
        @fun 发送HTTP报文头和报文体
        @funName send_http_head_and_body
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {object} net_info 网络连接信息（TcpIpNetInfo类）
        @funParam {object} head_dict Http报文头对象（说明参考create_http_head的注释）
        @funParam {bytes[]} body 要发送的http内容字节数组

        @funReturn {generic.CResult} 数据发送结果:
            result.code ：0-成功，5-写入数据超时，其他为写入失败
            result.send_time : datetime 实际发送完成时间

        """
        _result = CResult(code=0, msg=u'成功')
        _result.send_time = None
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                logger=None,
                self_log_msg=u'发送Http报文异常：',
                force_log_level=EnumLogLevel.ERROR
        ):
            # 判断报文体长度
            if "Content-Length".upper() in head_dict.upper_map.keys():
                head_dict.para[head_dict.upper_map["Content-Length".upper()]] = str(len(body))
            else:
                head_dict.para["Content-Length"] = str(len(body))
                head_dict.upper_map["Content-Length".upper()] = "Content-Length"
            _send_str = HttpService.get_http_head_str(head_dict)
            # 发送报文头
            _send_bytes = bytes(_send_str, "ascii")
            _send_result = TcpIpService.send_data(net_info, len(_send_bytes), _send_bytes)
            _result.send_time = _send_result.send_time
            if _send_result.code != 0:
                _send_result.copy_to(_result)
                return _result
            # 发送报文体
            if body is not None:
                _send_result = TcpIpService.send_data(net_info, len(body), body)
            return _send_result

        # 异常情况返回结果
        return _result

    @staticmethod
    def easy_send_http(server_opts, head_dict, body):
        """
        @fun 向服务器发送HTTP报文并收取返回报文的简易函数
        @funName easy_send_http
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 同时实现了与服务器的短连接
        
        @funParam {object} server_opts 网络服务启动参数:
            可以从HttpService.default_tcpip_opts()获取到默认的参数对象，再进行修改
        @funParam {object} head_dict Http报文头对象（说明参考create_http_head的注释）
        @funParam {bytes[]} body 要发送的http内容字节数组
        
        @funReturn {generic.CResult} 发送结果
            result.code ：0-成功，其他为发送失败
            result.head_dict ：返回报文的报文头对象（说明参考create_http_head的注释）
            result.body ：bytes，返回报文的报文体数据字节数组
            result.send_time : datetime 实际发送完成时间
            result.recv_time : datetime 实际开始接受时间
        
        """
        _result = CResult(code=0, msg=u'成功')
        _result.head_dict = None
        _result.body = None
        _result.send_time = None
        _result.recv_time = None
        _connect_result = None
        try:
            # 连接服务端
            _connect_result = HttpService.connect_server(server_opts)
            if _connect_result.code != 0:
                _connect_result.copy_to(_result)
                return _result

            # 发送
            _send_result = HttpService.send_http_head_and_body(_connect_result.net_info, head_dict, body)
            _result.send_time = _send_result.send_time
            if _send_result.code != 0:
                _send_result.copy_to(_result)
                return _result

            # 接收结果
            _recv_result = HttpService.get_http_head(_connect_result.net_info)
            _result.recv_time = _recv_result.recv_time
            if _recv_result.code != 0:
                _recv_result.copy_to(_result)
                return _result

            _result.head_dict = copy.deepcopy(_recv_result.head_dict)
            _recv_result = HttpService.get_http_body(_connect_result.net_info, _result.head_dict)
            _result.recv_time = _recv_result.recv_time
            if _recv_result.code != 0:
                _recv_result.copy_to(_result)
                return _result
            _result.body = copy.deepcopy(_recv_result.body)
            return _result
        finally:
            # 关闭连接
            if _connect_result.code == 0:
                HttpService.close_connect(_connect_result.net_info)

    #############################
    # 重载recv_data和send_data
    #############################

    @staticmethod
    def recv_data(net_info, recv_para=None):
        """
        @fun 从网络连接获取数据
        @funName recv_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 从指定的网络连接中读取数据

        @funParam {object} net_info 要读取数据的网络信息对象（TcpIpNetInfo类）
        @funParam {int} recv_para 读取数据的参数，暂时无用，可以传None

        @funReturn {generic.CResult} 数据获取结果:
            result.code ：0-成功，4-获取数据超时，其他为获取失败
            result.data ：获取到的数据对象:
                result.data.head_dict - 获取到的报文头(说明参考create_http_head的注释)
                result.data.body - 获取到的报文数据(bytes[])
            result.recv_time : datetime 实际开始接受数据时间

        """
        _result = CResult(code=0, msg=u'成功')
        _result.data = NullObj()
        _result.recv_time = None

        # 获取报文头
        _temp_result = HttpService.get_http_head(net_info=net_info)
        if _temp_result.code != 0:
            _temp_result.copy_to(_result)
            return _result
        _result.data.head_dict = copy.deepcopy(_temp_result.head_dict)

        # 获取报文体
        _temp_result = HttpService.get_http_body(net_info=net_info, head_dict=_result.data.head_dict)
        _result.recv_time = _temp_result.recv_time
        if _temp_result.code != 0:
            _temp_result.copy_to(_result)
            return _result
        _result.data.body = copy.deepcopy(_temp_result.body)

        # 返回函数
        return _result

    @staticmethod
    def send_data(net_info, send_para=dict(), data=None):
        """
        @fun 向网络连接发送数据
        @funName send_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 向指定的网络连接发送数据
        @funExcepiton:
            异常类名 异常说明

        @funParam {TcpIpNetInfo} net_info 要发送数据的网络信息对象（TcpIpNetInfo类）
        @funParam {dict} send_para 发送数据的参数，按以下顺序从字典获取参数生成报文头对象:
            1、获取head_dict，值为报文头对象，如果存在head_dict则不再处理后续的参数
            2、获取head_type 报文头类型，"Request"-请求报文，"Response"-响应报文:
                如果不传代表"Request"，此时将用全局默认报文头的参数发送
            3、获取para_list 要加入的报文头参数字典，例如：
                para_list = {
                    "Date":HttpService.get_http_datetime_format(datetime.now()),
                    "Content-Length":"0"
                }
        @funParam {byte[]} data 要发送的数据对象（bytes字节数组）

        @funReturn {generic.CResult} 数据发送结果:
            result.code ：0-成功，5-发送数据超时，其他为发送失败
            result.head_dict : 生成的报文头
            result.send_time : datetime 实际发送完成时间

        """
        # 先生成报文头
        _head_dict = None
        if not hasattr(send_para, "keys"):
            send_para = dict()

        if "head_dict" in send_para.keys():
            _head_dict = send_para["head_dict"]
        else:
            # 用默认的报文头
            _head_type = EnumHttpHeadType.Request.value
            if "head_type" in send_para.keys():
                _head_type = send_para["head_type"]
            # 从全局变量获取
            if _head_type == EnumHttpHeadType.Request.value:
                _head_dict = RunTools.get_global_var('__HttpServiceRequestHeadDict')
            else:
                _head_dict = RunTools.get_global_var('__HttpServiceResponseHeadDict')
            # 如果没有设置全局变量，重新生成报文头
            if _head_dict is None:
                _head_dict = HttpService.create_http_head(head_type=EnumHttpHeadType(_head_type))
            # 设置参数
            if "para_list" in send_para.keys():
                # 处理参数
                for _key in send_para["para_list"]:
                    if _key not in (EnumHttpHeadType.Request.value, EnumHttpHeadType.Response.value):
                        _head_dict.para[_key] = send_para["para_list"][_key]
                        _head_dict.upper_map[_key.upper()] = _key

        # 发送报文
        _result = HttpService.send_http_head_and_body(net_info=net_info, head_dict=_head_dict, body=data)
        _result.head_dict = _head_dict
        return _result

    #############################
    # 利用TcpIpService服务处理底层的代码
    #############################

    _server_http_deal_fun = None  # 处理HTTP请求的内部函数，保存外部传入的HTTP服务端处理函数定义

    # TODO(snaker): 后续改进增加长连接模式的支持
    def __server_connect_deal_fun_http(self, thread_id, server_opts, net_info, self_tag):
        """
        @fun 封装Http协议的收报和发报处理函数，让外围只需关注收到后的数据及需返回的数据
        @funName __server_connect_deal_fun_http
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 每个连接执行该函数获取数据及返回数据，完成后关闭连接并退出:
            暂时不支持长连接模式，后续可改进增加该支持
        
        @funParam {int} thread_id 线程ID
        @funParam {object} server_opts 服务器参数，属性值参考HttpService.default_tcpip_opts()
        @funParam {TcpIpNetInfo} net_info 网络信息对象（TcpIpNetInfo类）
        @funParam {string} self_tag 用于发起端传入自身的识别标识
        
        """
        # 获取报文头
        _result = self.get_http_head(net_info=net_info)
        if _result.code != 0:
            self._write_log(
                EnumLogLevel.ERROR,
                "[HTTP标准服务][%s]获取客户端报文头失败：%s%s\r\n%s" % (
                    str(thread_id),
                    str(_result.code),
                    _result.msg,
                    _result.trace_str
                )
            )
            # 关闭连接
            self.close_connect(net_info=net_info)
            return
        # 保存报文头并打印
        _getdata = NullObj()
        _getdata.head_dict = _result.head_dict
        self._write_log(
            self._log_level,
            "[HTTP标准服务][%s]获取到客户端报文头：\r\n%s" % (
                str(thread_id),
                HttpService.get_http_head_str(_getdata.head_dict)
            )
        )
        # 获取报文体
        _result = self.get_http_body(net_info=net_info, head_dict=_getdata.head_dict)
        if _result.code != 0:
            self._write_log(
                EnumLogLevel.ERROR,
                "[HTTP标准服务][%s]获取客户端报文体失败：%s%s\r\n%s" % (
                    str(thread_id),
                    str(_result.code),
                    _result.msg,
                    _result.trace_str
                )
            )
            # 关闭连接
            self.close_connect(net_info=net_info)
            return

        _getdata.body = _result.body
        self._write_log(
            self._log_level,
            "[HTTP标准服务][%s]获取到客户端报文体，字节长度：%s" % (
                str(thread_id),
                str(len(_getdata.body))
            )
        )

        # 初始化返回值
        _respone_data = NullObj()
        try:
            _respone_data = self._server_http_deal_fun(net_info=net_info, get_data=_getdata, self_tag=self_tag)
        except:
            self._write_log(
                EnumLogLevel.ERROR,
                "[HTTP标准服务][%s]执行Http处理函数异常：%s\r\n%s" % (
                    str(thread_id),
                    str(sys.exc_info()),
                    traceback.format_exc()
                )
            )
            _head_dict = HttpService.create_http_head(head_type=EnumHttpHeadType.Response,
                                                      stat_code="500", stat_msg="Internal Server Error")
            _head_dict.para["Date"] = HttpService.get_http_datetime_format(datetime.now())
            _head_dict.upper_map["DATE"] = "Date"
            _respone_data.send_para = dict()
            _respone_data.send_para["head_dict"] = _head_dict
            _respone_data.body = None

        # 发送返回的报文信息
        if _respone_data is not None:
            _result = HttpService.send_data(net_info=net_info,
                                            send_para=_respone_data.send_para, data=_respone_data.body)
            if _result.code != 0:
                self._write_log(
                    EnumLogLevel.ERROR,
                    "[HTTP标准服务][%s]向客户端返回报文失败：%s%s\r\n%s" % (
                        str(thread_id),
                        str(_result.code),
                        _result.msg,
                        _result.trace_str
                    )
                )
            else:
                self._write_log(
                    self._log_level,
                    "[HTTP标准服务][%s]向客户端返回报文成功，报文体数据长度：%s   返回报文头：\r\n%s" % (
                        str(thread_id),
                        _result.head_dict.para[_result.head_dict.upper_map["Content-Length".upper()]],
                        HttpService.get_http_head_str(_result.head_dict)
                    )
                )

        # 关闭连接
        self.close_connect(net_info=net_info)
        return

    def __init__(self, logger=None, server_status_info_fun=None,
                 server_connect_deal_fun=None, self_tag="", log_level=EnumLogLevel.INFO, server_http_deal_fun=None):
        """
        @fun 重写HTTP协议的构造函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 该构造函数在通用框架的基础上增加了server_http_deal_Fun入参，用于简化HTTP协议的服务端处理
        
        @funParam {object} logger 日志对象，服务过程中通过该函数写日志:
            可以为标准的logging日志库对象，也可以为simple_log对象，但要求对象实现:
            标准的info、debug、warning、error、critical五个日志方法
        @funParam {fun} server_status_info_fun 外围传入的网络服务状态变更通知函数对象，当网络服务状态发生变更时通过:
            该函数通知调用方；形式为fun(server_status, result):
            其中server_status为服务器状态EnumNetServerRunStatus，
            result为CResult通用执行结果对象，自定义属性self_tag为发起方识别标识
        @funParam {fun} server_connect_deal_fun 外围传入的网络服务与客户端连接后对连接的处理线程函数对象，在该函数中:
            实现服务器端具体的通讯处理（如循环收报文、返回报文等）；
            形式为fun(thread_id, server_opts, net_info, self_tag):
                thread_id - 线程ID
                server_opts -服务的启动参数
                net_info - 具体实现的连接信息（TcpIpNetInfo对象）
                self_tag - 用于发起端传入自身的识别标识
            需注意实现上应在每次循环时查询服务器关闭状态，如果判断到服务器已关闭，应结束处理.
        @funParam {string} self_tag 自定义标识
        @funParam {EnumLogLevel} log_level 处理中正常日志的输出级别，默认为INFO，如果不想输出过多日志可以设置为DEBUG
        @funParam {fun} server_http_deal_fun 外围传入的获取到HTTP请求数据后的处理函数，使用该参数无需自行实现循环获取
            和发送报文的逻辑，函数格式为fun(net_info=None, get_data=object, self_tag=''):
                net_info：客户端的网络连接对象（TcpIpNetInfo）
                get_data：请求数据对象（get_data.head_dict - http头对象, get_data.body - 要发送的bytes[]数据）
                函数返回值为respone_data对象（respone_data.send_para, respone_data.body
                    send_para的参数格式参照send_data函数），如果为None则代表无需发送返回报文
            注意：使用该参数时server_connect_deal_fun无效（如果希望能控制底层逻辑的情况下则使用server_connect_deal_fun）

        """
        self._server_http_deal_fun = server_http_deal_fun
        if server_http_deal_fun is not None:
            # 将处理函数替换为封装好的内部函数，简化处理
            TcpIpService.__init__(self, logger=logger,
                                  server_status_info_fun=server_status_info_fun,
                                  server_connect_deal_fun=self.__server_connect_deal_fun_http,
                                  self_tag=self_tag, log_level=log_level)
        else:
            # 按照标准tcpip的模式处理，自行处理数据获取部分
            TcpIpService.__init__(self, logger=logger,
                                  server_status_info_fun=server_status_info_fun,
                                  server_connect_deal_fun=server_connect_deal_fun,
                                  self_tag=self_tag, log_level=log_level)


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))
