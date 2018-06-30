#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : tcpip_service_test.py


import unittest
import time
from simple_log import *
from net_service.tcpip_service import *
from generic import *


__MoudleName__ = 'tcpip_service_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/1/24'


_TEMPDIR = "../Temp/"


class TcpIpServiceTestCase(unittest.TestCase):
    # 服务端处理函数定义
    def server_status_info_fun(self, server_status, result):
        self.filelog.write_log("INFO",
                               ("[服务端]"+result.self_tag+"服务状态变更："
                                + str(server_status)
                                + "   结果code："
                                + str(result.code)
                                + "  描述："
                                + result.msg), call_level=0)
        return

    def server_connect_deal_fun(self, thread_id, server_opts, net_info, self_tag):
        self.filelog.write_log("INFO", ("[服务端"
                                        + self_tag
                                        + "][" + str(thread_id)
                                        + "]收到客户端连接："
                                        + StringTools.format_obj_property_str(deal_obj=net_info, is_deal_subobj=True)),
                               call_level=0)

        # 获取客户端发送的信息，先获取前4个字节
        _read_result = TcpIpService.recv_data(net_info, 4)
        if _read_result.code != 0:
            # 获取失败
            self.filelog.write_log("INFO", ("[服务端]获取客户端数据报文头失败，关闭连接："
                                            + str(_read_result.code) + "-" + _read_result.msg), call_level=0)
            TcpIpService.close_connect(net_info)
            return

        _next_read = int.from_bytes(_read_result.data, byteorder='big', signed=False)
        self.filelog.write_log("INFO", "[服务端]获取到客户端4个字节的后续数据长度：" + str(_next_read),
                               call_level=0)

        # 获取后面的数据
        _read_result = TcpIpService.recv_data(net_info, _next_read)
        if _read_result.code != 0:
            # 获取失败
            self.filelog.write_log("INFO", ("[服务端]获取客户端数据报文体失败，关闭连接："
                                            + str(_read_result.code) + "-" + _read_result.msg), call_level=0)
            TcpIpService.close_connect(net_info)
            return

        _read_str = str(_read_result.data, "utf-8")
        self.filelog.write_log("INFO", "[服务端]获取到客户端报文体数据：" + _read_str, call_level=0)

        if _read_str == "servernoresponse":
            # 隔30秒不响应
            time.sleep(30)

        # 返回内容，先组包
        _ret_str = "处理成功"
        _send_body = bytes(_ret_str, "utf-8")
        _send_head = len(_send_body).to_bytes(4, byteorder='big', signed=False)

        # 发送报文头
        _send_result = TcpIpService.send_data(net_info, 4, _send_head)
        if _send_result.code != 0:
            self.filelog.write_log("INFO", ("[服务端]返回客户端数据报文头失败，关闭连接："
                                            + str(_send_result.code) + "-" + _send_result.msg), call_level=0)
            TcpIpService.close_connect(net_info)
            return

        self.filelog.write_log("INFO", "[服务端]返回客户端4个字节的后续数据长度：" + str(len(_send_body)),
                               call_level=0)
        _send_result = TcpIpService.send_data(net_info, None, _send_body)
        if _send_result.code != 0:
            self.filelog.write_log("INFO", ("[服务端]返回客户端数据报文体失败，关闭连接："
                                            + str(_send_result.code) + "-" + _send_result.msg), call_level=0)
            TcpIpService.close_connect(net_info)
            return
        self.filelog.write_log("INFO", "[服务端]返回客户端报文体数据：" + _ret_str, call_level=0)

        # 处理完成，关闭连接
        _close_result = TcpIpService.close_connect(net_info)
        if _close_result.code != 0:
            self.filelog.write_log("INFO", ("[服务端]关闭客户端连接失败："
                                            + str(_close_result.code) + "-" + _close_result.msg), call_level=0)

        self.filelog.write_log("INFO", "[服务端]关闭客户端连接", call_level=0)


    # 客户端发送代码
    def _send_text(self, net_info, str_data):
        # 准备要发送的内容
        _send_body = bytes(str_data, "utf-8")
        _send_head = len(_send_body).to_bytes(4, byteorder='big', signed=False)

        # 发送报文头
        _result = TcpIpService.send_data(net_info=net_info, send_para=4, data=_send_head)
        if _result.code != 0:
            self.filelog.write_log("INFO",
                            "[客户端]向服务器发送数据报文头失败，关闭连接：" + '\n'.join(
                                ['%s:%s' % item for item in _result.__dict__.items()]), call_level=0)
            return

        self.filelog.write_log("INFO", "[客户端]向服务器发送4个字节的后续数据长度：" + str(len(_send_body)),
                               call_level=0)
        _result = TcpIpService.send_data(net_info, len(_send_body), _send_body)
        if _result.code != 0:
            self.filelog.write_log("INFO",
                            "[客户端]向服务器发送数据报文体失败，关闭连接：" + '\n'.join(
                                ['%s:%s' % item for item in _result.__dict__.items()]), call_level=0)
            return
        self.filelog.write_log("INFO", "[客户端]向服务器发送数据报文体数据：" + str_data, call_level=0)

        # 获取返回值
        _result = TcpIpService.recv_data(net_info, 4)
        if _result.code != 0:
            # 获取失败
            self.filelog.write_log("INFO",
                            "[客户端]获取服务器端数据报文头失败，关闭连接：" + '\n'.join(
                                ['%s:%s' % item for item in _result.__dict__.items()]), call_level=0)
            return
        _next_read = int.from_bytes(_result.data, byteorder='big', signed=False)
        self.filelog.write_log("INFO", "[客户端]获取到服务器端4个字节的后续数据长度：" + str(_next_read),
                               call_level=0)
        # 获取后面的数据
        _result = TcpIpService.recv_data(net_info, _next_read)
        if _result.code != 0:
            # 获取失败
            self.filelog.write_log("INFO",
                            "[客户端]获取服务器端数据报文体失败，关闭连接：" + '\n'.join(
                                ['%s:%s' % item for item in _result.__dict__.items()]), call_level=0)
            return
        _read_str = str(_result.data, "utf-8")
        self.filelog.write_log("INFO", "[客户端]获取到服务器端报文体数据：" + _read_str, call_level=0)
        return



    # 启动测试执行的初始化
    def setUp(self):
        DebugTools.set_debug(True)

        # 准备日志对象
        self.filelog = Logger(
            conf_file_name=_TEMPDIR+'TcpIpServicelog.json',
            logger_name=EnumLoggerName.ConsoleAndFile.value,
            logfile_path=_TEMPDIR + "TcpIpServicelog/file.log",
            call_level=1,
        )
        self.filelog.set_logger_level(EnumLogLevel.DEBUG)

        # 启动TcpIpServer
        self.server = TcpIpService(
            logger=self.filelog,
            server_status_info_fun=self.server_status_info_fun,
            server_connect_deal_fun=self.server_connect_deal_fun,
            self_tag='UnitTest',
            log_level=EnumLogLevel.DEBUG
        )

        _server_opts = TcpIpService.default_tcpip_opts()
        print(str(_server_opts))
        _server_opts.host_name = "127.0.0.1"
        _server_opts.port = 9512
        self.server.start_server(server_opts=_server_opts)

    # 结束测试执行的销毁
    def tearDown(self):
        # 关闭服务器连接
        _i = 0
        while _i<10:
            time.sleep(1)
            _i = _i + 1
        self.server.stop_server(is_wait=True)


    # 测试案例1
    def test_send_text(self):
        print("案例test_SendText：测试客户端发送信息到服务器端")
        _connect_para = TcpIpService.default_tcpip_opts()
        _connect_para.host_name = "127.0.0.1"
        _connect_para.port = 9512
        _connect_result = TcpIpService.connect_server(_connect_para)
        self.assertTrue(_connect_result.code == 0,
                        ("[客户端]连接服务器失败："
                        + '\n'.join(['%s:%s' % item for item in _connect_result.__dict__.items()])))

        # 打印连接信息
        self.filelog.write_log("INFO",
                               ("[客户端]连接信息："
                                + '\n'.join(['%s:%s' % item for item in _connect_result.net_info.__dict__.items()])),
                               call_level=0)

        # 发送数据
        self._send_text(net_info=_connect_result.net_info, str_data="测试案例test_SendText数据")

        # 关闭连接
        _close_result = TcpIpService.close_connect(_connect_result.net_info)
        self.assertTrue(_close_result.code == 0,
                        ("[客户端]关闭服务器失败："
                         + '\n'.join(['%s:%s' % item for item in _close_result.__dict__.items()])))



if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    # 执行自动测试案例
    unittest.main()
