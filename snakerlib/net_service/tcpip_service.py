#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : tcpip_service.py


import socket
from datetime import datetime
import platform
from .base_service_fw import BaseServiceFW
from ..generic import NullObj, CResult, ExceptionTools, DebugTools
from ..generic_enum import EnumLogLevel


__MoudleName__ = 'tcpip_service'
__MoudleDesc__ = 'TcpIp网络协议的实现类'
__Version__ = '0.9.0'
__Author__ = 'snaker'
__Time__ = '2018/1/23'


class TcpIpNetInfo(object):
    """
    @class TcpIp的网络连接信息类
    @className TcpIpNetInfo
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 定义net_info的属性

    """

    def __init__(self, socket_obj=None, laddr=None, raddr=None, caddr=None, auto_fill=False):
        """
        @fun 初始化函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 可以在初始化函数中直接设定对应的值

        @funParam {socket} socket 网络套接字对象
        @funParam {(string,int)} laddr 套接字本地参数信息（ip,port)
        @funParam {(string,int)} raddr 套接字远程参数信息（ip,port)
        @funParam {(string,int)} caddr 套接字客户端参数新（ip,port)
        @funParam {bool} auto_fill 是否根据套接字对象获取其他参数(其他参数未传值的情况):
            True - 自动获取参数值
            False - 不自动获取参数值

        """
        self.socket = socket_obj
        if laddr is not None:
            self.laddr = laddr
        else:
            if auto_fill and socket_obj is not None:
                self.laddr = socket_obj.getsockname()
            else:
                self.laddr = ("", 0)

        if raddr is not None:
            self.raddr = raddr
        else:
            if auto_fill and socket_obj is not None:
                self.raddr = socket_obj.getpeername()
            else:
                self.raddr = ("", 0)

        if caddr is not None:
            self.caddr = caddr
        else:
            self.caddr = ("", 0)


class TcpIpService(BaseServiceFW):
    """
    @class TcpIp协议服务
    @className TcpIpService
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 继承BaseServiceFW类的TcpIp协议处理实现类，提供使用TcpIp协议进行网络通讯的基础支持:
        基础的服务功能及使用方法主要参考BaseServiceFW类，继承类参考本源码注释

    """

    #############################
    # 实现类的自有函数（公共函数）
    #############################

    @staticmethod
    def default_tcpip_opts():
        """
        @fun 默认TcpIp参数（可用于server_opts及connect_opts）
        @funName default_tcpip_opts
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 返回具有默认值的server_opts对象

        """
        _server_opts = NullObj()
        _server_opts.host_name = ""  # 主机名或IP地址
        _server_opts.port = 8080  # 监听端口
        _server_opts.max_connect = 20  # 允许最大连接数
        _server_opts.recv_timeout = 10000  # 数据接收的超时时间，单位为毫秒
        _server_opts.send_timeout = 10000  # 数据发送的超时时间，单位为毫秒
        _server_opts.accept_timeout = 3000  # 获取客户端连接的监听超时时间，单位为毫秒
        _server_opts.recv_buffer_size = None  # 连接接收缓冲区大小，单位为字节，None代表使用系统默认缓冲区值
        _server_opts.send_buffer_size = None  # 连接发送缓冲区大小，单位为字节，None代表使用系统默认缓冲区值
        return _server_opts

    @staticmethod
    def set_timeout(net_info, recv_timeout=None, send_timeout=None):
        """
        @fun 设置连接超时时间
        @funName set_timeout
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 设置连接超时时间，目前仅支持设置recv_timeout, send_timeout需研究如何设置

        @funParam {TcpIpNetInfo} net_info 网络连接信息对象(TcpIpNetInfo对象)
        @funParam {int} recv_timeout 接收超时时间，单位为毫秒，None代表不设置
        @funParam {int} send_timeout 发送超时时间，单位为毫秒，None代表不设置

        """
        _sysstr = platform.system()
        if recv_timeout is not None:
            net_info.socket.settimeout(recv_timeout / 1000)
        if _sysstr == "Windows":
            if recv_timeout is not None:
                net_info.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, recv_timeout)
            if send_timeout is not None:
                net_info.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, send_timeout)

    @staticmethod
    def set_buffer_size(net_info, recv_buffer_size=None, send_buffer_size=None):
        """
        @fun 设置缓冲区大小
        @funName set_buffer_size
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 设置缓冲区大小

        @funParam {TcpIpNetInfo} net_info 网络连接信息对象(TcpIpNetInfo对象)
        @funParam {int} recv_buffer_size 连接接收缓冲区大小，单位为字节，None代表不设置
        @funParam {int} send_buffer_size 连接发送缓冲区大小，单位为字节，None代表不设置

        """
        if recv_buffer_size is not None:
            net_info.socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                recv_buffer_size
            )

        if send_buffer_size is not None:
            net_info.socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_SNDBUF,
                send_buffer_size
            )

    #############################
    # 实现继承框架的抽象函数（私有函数）
    #############################

    def _start_server_without_accept(self, server_opts):
        """
        @fun 启动网络服务但不接受连接
        @funName _start_server_without_accept
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 启动服务但不接受请求服务，该方法只做到启动端口层面，轮询监听不在该方法中实现

        @funParam {object} server_opts 网络服务启动参数:
            可以通过TcpIpService.default_tcpip_opts()获取到默认的参数对象，再进行修改

        @funReturn {generic.CResult} 启动结果
            result.code ：0-成功，其他值为失败
            result.net_info ：启动后的服务端网络连接信息对象（TcpIpNetInfo类），将传给后续的监听线程（_accept_one）

        """
        _result = CResult(code='0', msg=u'成功')
        _result.net_info = None
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                logger=self._logger,
                self_log_msg=u'启动网络服务异常:',
                force_log_level=EnumLogLevel.ERROR
        ):
            _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _server_socket.bind((server_opts.host_name, server_opts.port))
            _server_socket.listen(server_opts.max_connect)
            # 设置超时时间
            TcpIpService.set_timeout(TcpIpNetInfo(socket_obj=_server_socket), recv_timeout=server_opts.accept_timeout)
            _result.net_info = TcpIpNetInfo(socket_obj=_server_socket, laddr=(server_opts.host_name, server_opts.port))
        # 返回结果
        return _result

    def _accept_one(self, server_opts, net_info):
        """
        @fun 监听接受一个请求并返回
        @funName _accept_one
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 提供监听并获取到请求连接返回的方法；注意该该函数必须捕获并处理异常

        @funParam {object} server_opts 网络服务启动参数，从_start_server_without_accept中传入
        @funParam {object} net_info 网络连接信息对象(TcpIpNetInfo对象)，_start_server_without_accept中获取到的结果

        @funReturn {generic.CResult} 获取网络连接结果:
            result.code ：0-成功，3-获取客户端连接请求超时
            result.net_info ：客户端连接信息对象（TcpIpNetInfo类），该对象将传给后续单个连接处理的线程

        """
        _result = CResult(code='0', msg=u'成功')
        _result.net_info = None
        _error_map = {
            socket.timeout: (3, self._error_code_map[3])
        }
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                expect=(socket.timeout),
                error_map=_error_map,
                expect_no_log=True,
                expect_use_error_map=True,
                logger=self._logger,
                self_log_msg=u'获取客户端请求异常:',
                force_log_level=None
        ):
            DebugTools.debug_print(u'服务端accept超时时间：' + str(net_info.socket.gettimeout()))
            _csocket, _addr = net_info.socket.accept()  # 接收客户端连接，返回客户端和地址
            _result.net_info = TcpIpNetInfo(socket_obj=_csocket, laddr=_csocket.getsockname(),
                                            raddr=_csocket.getpeername(), caddr=_addr)
            # 设置超时时间
            TcpIpService.set_timeout(
                net_info=_result.net_info,
                recv_timeout=server_opts.recv_timeout,
                send_timeout=server_opts.send_timeout
            )
            # 设置缓冲区大小
            TcpIpService.set_buffer_size(
                net_info=_result.net_info,
                recv_buffer_size=server_opts.recv_buffer_size,
                send_buffer_size=server_opts.send_buffer_size
            )
            self._write_log(self._log_level, "接收到客户端连接：" + str(_addr) + str(_csocket))
        # 返回结果
        return _result

    #############################
    # 实现继承框架的抽象函数（公共函数）
    #############################

    @staticmethod
    def recv_data(net_info, recv_para):
        """
        @fun 从网络连接获取数据
        @funName recv_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 从指定的网络连接中读取数据

        @funParam {object} net_info 要读取数据的网络信息对象（TcpIpNetInfo类）
        @funParam {int} recv_para 读取数据的参数（字节长度）
        @funParam {datetime} recv_time 函数内部会改写的数据开始接收时间，调用代码可通过该变量获取实际开始接受数据时间

        @funReturn {generic.CResult} 数据获取结果:
            result.code ：0-成功，4-获取数据超时，其他为获取失败
            result.data ：获取到的数据对象（bytes字节数组）
            result.recv_time : datetime 实际开始接受数据时间

        """
        _result = CResult(code='0', msg=u'成功')
        _result.data = None
        _result.recv_time = None
        _error_map = {
            socket.timeout: (4, u"获取数据超时")
        }
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                error_map=_error_map,
                logger=None,
                self_log_msg=u'获取数据异常:',
                force_log_level=EnumLogLevel.ERROR
        ):
            _result.data = net_info.socket.recv(recv_para)
            _result.recv_time = datetime.now()
            if len(_result.data) < recv_para:
                _result.code = 4
                _result.msg = '获取数据超时（预计获取%s字节，实际获取%s字节）' % (
                    str(recv_para), str(len(_result.data))
                )
        # 返回结果
        return _result

    @staticmethod
    def send_data(net_info, send_para, data):
        """
        @fun 向网络连接写入数据
        @funName send_data
        @funGroup
        @funVersion
        @funDescription 向指定的网络连接发送数据

        @funParam {object} net_info 要写入数据的网络信息对象（TcpIpNetInfo类）
        @funParam {object} send_para 写入数据的参数（暂无用，直接传None即可）
        @funParam {bytes[]} data 要写入的数据对象（bytes字节数组）

        @funReturn {generic.CResult} 发送结果:
            result.code ：0-成功，5-写入数据超时，其他为写入失败
            result.send_time : datetime 实际发送完成时间

        """
        _result = CResult(code='0', msg=u'成功')
        _result.send_time = None
        _error_map = {
            socket.timeout: (5, u"发送数据超时")
        }
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                error_map=_error_map,
                logger=None,
                self_log_msg=u'发送数据异常:',
                force_log_level=EnumLogLevel.ERROR
        ):
            net_info.socket.send(data)
            _result.send_time = datetime.now()
        # 返回结果
        return _result

    @staticmethod
    def close_connect(net_info):
        """
        @fun 关闭网络连接
        @funName close_connect
        @funGroup
        @funVersion
        @funDescription 关闭指定的网络连接，注意该该函数必须捕获并处理异常

        @funParam {object} net_info 需要关闭的网络连接信息对象(TcpIpNetInfo类)

        @funReturn {generic.CResult} 关闭结果
            result.code ：0-成功，其他值为失败
        """
        _result = CResult(code='0', msg=u'成功')
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                logger=None,
                self_log_msg=u'关闭连接异常:',
                force_log_level=EnumLogLevel.ERROR
        ):
            net_info.socket.close()
        # 返回结果
        return _result

    @staticmethod
    def connect_server(connect_para):
        """
        @fun 客户端连接服务器函数
        @funName connect_server
        @funGroup
        @funVersion
        @funDescription 客户端通过该函数连接服务器端

        @funParam {object} connect_para 需要连接服务器的参数:
            可以通过TcpIpService.default_tcpip_opts()获取到默认的参数对象，再进行修改

        @funReturn {generic.CResult} 连接结果:
            result.code ：0-成功，其他值为失败
            result.net_info ： 连接后的网络信息对象(TcpIpNetInfo对象)

        """
        _result = CResult(code='0', msg=u'成功')
        _result.net_info = None
        with ExceptionTools.ignored_cresult(
                result_obj=_result,
                logger=None,
                self_log_msg=u'连接服务器异常:',
                force_log_level=EnumLogLevel.ERROR
        ):
            _tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 分配 TCP 客户端套接字
            _tcp_client_socket.connect((connect_para.host_name, connect_para.port))  # 主动连接
            _result.net_info = TcpIpNetInfo(
                socket_obj=_tcp_client_socket,
                laddr=_tcp_client_socket.getsockname(),
                raddr=_tcp_client_socket.getpeername(),
                caddr=(connect_para.host_name, connect_para.port)
            )
            # 设置超时时间
            TcpIpService.set_timeout(
                net_info=_result.net_info,
                recv_timeout=connect_para.recv_timeout,
                send_timeout=connect_para.send_timeout
            )
            # 设置缓冲区大小
            TcpIpService.set_buffer_size(
                net_info=_result.net_info,
                recv_buffer_size=connect_para.recv_buffer_size,
                send_buffer_size=connect_para.send_buffer_size
            )
        # 反馈结果
        return _result

    def get_server_info(self, para_name):
        """
        @fun 获取服务器信息
        @funName get_server_info
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 通用的获取服务器信息函数，根据传入的参数获取参数值

        @funParam {string} para_name 参数名，以下为参数名和参数值的对应
            ServerIp : string 服务IP
            ServerPort : int 监听端口

        @funReturn {object} 返回具体的参数值对象，如果没有值传None

        """
        if para_name == "ServerIp":
            return self._server_opts.host_name
        elif para_name == "ServerPort":
            return self._server_opts.port
        else:
            return None

    @staticmethod
    def get_client_info(net_info, para_name):
        """
        @fun 获取客户端连接信息
        @funName get_client_info
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 获取指定客户端连接的信息，根据传入的参数获取参数值

        @funParam {object} net_info 客户端网络连接信息对象(TcpIpNetInfo对象)
        @funParam {string} para_name 参数名，以下为参数名和参数值的对应:
            ClientIp : string 对端IP
            ClientPort : int 对端端口
            LocalIp : string 本地IP
            LocalPort : int 本地端口
            RemoteIp : string 远端IP
            RemotePort : int 远端端口

        @funReturn {object} 返回具体的参数值对象，如果没有值传None

        """
        if para_name == "ClientIp":
            return net_info.caddr[0]
        elif para_name == "ClientPort":
            return net_info.caddr[1]
        elif para_name == "LocalIp":
            return net_info.laddr[0]
        elif para_name == "LocalPort":
            return net_info.laddr[1]
        elif para_name == "RemoteIp":
            return net_info.raddr[0]
        elif para_name == "RemotePort":
            return net_info.raddr[1]
        else:
            return None

if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))
