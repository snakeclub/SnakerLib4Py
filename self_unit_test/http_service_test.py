#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : http_service_test.py


import unittest
from simple_log import *
from net_service.http_service import *
from generic import *


__MoudleName__ = 'http_service_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/1/26'


_TEMPDIR = "../Temp/"


class HttpServiceTestCase(unittest.TestCase):

    # 服务端处理函数定义
    def server_status_info_fun(self, server_status, result):
        self.filelog.write_log("INFO",
                               ("[服务端]" + result.self_tag + "服务状态变更："
                                + str(server_status)
                                + "   结果code："
                                + str(result.code)
                                + "  描述："
                                + result.msg), call_level=0)
        return

    def server_http_deal_fun(self, net_info=None, get_data=None, self_tag=""):
        self.filelog.write_log("INFO", ("[服务端"
                                        + self_tag
                                        + "]收到客户端连接："
                                        + StringTools.format_obj_property_str(deal_obj=net_info, is_deal_subobj=True)
                                        + "数据："
                                        + str(get_data.body,encoding='utf-8')),
                               call_level=0)
        # 返回报文
        _response_obj = NullObj()
        _response_obj.send_para = {"head_type": "Response"}
        _response_obj.body = bytes("处理成功，哈哈", encoding='utf-8')
        return _response_obj

    # 启动测试执行的初始化
    def setUp(self):
        # 准备日志对象
        self.filelog = Logger(
            conf_file_name=_TEMPDIR + 'HttpServicelog.json',
            logger_name=EnumLoggerName.ConsoleAndFile.value,
            logfile_path=_TEMPDIR + "HttpServicelog/file.log",
            call_level=1
        )

        # 设置全局默认报文头参数
        HttpService.set_default_head_dict(request_para_list=dict(), response_para_list=dict(),
                                          ver="HTTP1.0", req_type=EnumHttpResquestType.POST.value,
                                          url="", stat_code="200", stat_msg="OK")

        # 启动HttpServer
        self.server = HttpService(
            logger=self.filelog,
            server_connect_deal_fun=None,
            server_status_info_fun=self.server_status_info_fun,
            self_tag='TestFlag',
            server_http_deal_fun=self.server_http_deal_fun
        )

        _server_opts = HttpService.default_tcpip_opts()
        print(str(_server_opts))
        _server_opts.host_name = "127.0.0.1"
        _server_opts.port = 9513
        self.server.start_server(server_opts=_server_opts)

    # 结束测试执行的销毁
    def tearDown(self):
        # 关闭服务器连接
        self.server.stop_server(is_wait=True)

    # 测试案例1
    def test_SendText(self):
        print("案例test_SendText：测试客户端发送信息到服务器端")
        _connect_para = HttpService.default_tcpip_opts()
        _connect_para.host_name = "127.0.0.1"
        _connect_para.port = 9513
        _connect_result = HttpService.connect_server(_connect_para)
        self.assertTrue(_connect_result.code == 0,"[客户端]连接服务器失败：" + '\n'.join(['%s:%s' % item for item in _connect_result.__dict__.items()]))

        # 打印连接信息
        self.filelog.write_log("INFO", ("[客户端]连接信息："
                                        + StringTools.format_obj_property_str(deal_obj=_connect_result.net_info, is_deal_subobj=True)),
                               call_level=0)

        # 发送数据
        _send_result = HttpService.send_data(net_info=_connect_result.net_info,send_para=dict(),data=bytes("发送测试案例1",encoding="utf-8"))
        self.assertTrue(_send_result.code == 0,
                        "[客户端]发送测试案例1失败！错误信息："+str(_send_result.code)+"-"+_send_result.msg)

        # 收取回应信息
        _read_result = HttpService.recv_data(net_info=_connect_result.net_info)
        #print(StringTools.format_obj_property_str(deal_obj=_read_result, is_deal_subobj=True, max_level=3))
        self.assertTrue(_read_result.code == 0,
                        "[客户端]测试案例1获取回应报文失败！错误信息：" + str(_read_result.code) + "-" + _read_result.msg)
        self.filelog.write_log("INFO", ("收取到回应数据，报文头：\n"
                                        + HttpService.get_http_head_str(_read_result.data.head_dict)
                                        + "\n报文内容："
                                        + str(_read_result.data.body,"utf-8")),
                               call_level=0)

        # 关闭连接
        _close_result = HttpService.close_connect(_connect_result.net_info)
        self.assertTrue(_close_result.code == 0,
                        "[客户端]关闭服务器失败：" + '\n'.join(['%s:%s' % item for item in _connect_result.__dict__.items()]))


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
