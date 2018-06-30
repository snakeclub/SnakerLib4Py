#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : base_service_fw.py


import copy
import time
import threading
from enum import Enum
from abc import ABC, abstractmethod  # 利用abc模块实现抽象类
from generic_enum import EnumLogLevel
from generic import ExceptionTools, CResult, StringTools, DebugTools


__MoudleName__ = 'base_service_fw'
__MoudleDesc__ = '网络库的框架抽象类'
__Version__ = '0.9.0'
__Author__ = 'snaker'
__Time__ = '2018/1/21'


class EnumNetServerRunStatus(Enum):
    """
    @enum 服务器运行状态
    @enumName EnumNetServerRunStatus
    @enumDescription 服务器运行状态

    """
    Stop = 'S'  # 停止
    Running = 'R'  # 正在运行
    WaitStop = 'WS'  # 等待停止
    WaitStart = 'WR'  # 等待启动
    ForceStop = 'FS'  # 强制停止


class BaseServiceFW(ABC):
    """
    @class 网络库的框架抽象类
    @className BaseServiceFW
    @classGroup
    @classVersion 1.0.0
    @classDescription 抽象网络编程的公共方法形成框架，并提供基本的处理功能，简化网络协议编程的难度
    
    @classExample {Python} 使用参考:
        1、服务器端的使用方法，假设实现类为XService
        def server_status_info_fun(server_status, result):
            ...根据通知的服务器状态变更执行自定义处理
            return

        def server_connect_deal_fun(thread_id, server_opts, net_info, self_tag)
            ...循环通过recv_data和send_data进行连接收发处理
            return

        # 初始化服务对象
        _logger = logging.Logger()
        server = Xservice(logger=_logger, server_status_info_fun=server_status_info_fun,
            server_connect_deal_fun=server_connect_deal_fun, self_tag="TestTag")

        # 启动网络服务
        server_opts = ...
        server.start_server(server_opts=server_opts)

        # 关闭服务
        server.stop_server(is_wait=True)

        2、客户端的使用方法，假设实现类为XService
        connect_para=...
        connect_result = XService.connect_server(connect_para=connect_para)
        if connect_result.code == 0:
            # 连接成功
            send_para = ...
            data = ...
            send_result = XService.send.data(connect_result.net_info, send_para, data)
            if send_result.code == 0:
                # 获取返回结果
                recv_para = ...
                read_result = XService.recv_data(connect_result.net_info, recv_para)
                print(read_result.data)

    """

    #############################
    # 私有变量 - 子类可访问的变量
    #############################

    _server_opts = None  # 外围传入的网络服务启动参数，应为一个object对象，通过_serverOpts.xxx 获取对应的属性xxx值
    _logLevel = EnumLogLevel.INFO  # 外围传入的日志级别，根据该级别打印日志，例如传DEBUG可减少日志的输出
    # 错误码映射字典
    # 1 - 99为框架内部占用的错误码值
    _error_code_map = {
        0: u"成功",
        -1: u"异常",
        1: u"服务启动失败：服务不处于停止状态",
        2: u"服务停止失败：服务不处于运行状态",
        3: u"获取客户端连接请求超时",
        4: u"获取数据超时",
        5: u"发送数据超时"
    }

    #############################
    # 私有变量 - 只用于框架内部处理的变量
    #############################

    # 外围传入的日志对象，服务过程中通过该函数写日志
    _logger = None

    # 外围传入的网络服务状态变更通知函数，函数实现的第1个参数为当前状态，第2个参数为错误信息result对象，含code和msg
    __server_status_info_fun = None

    # 外围传入的网络服务与客户端连接后对连接的处理线程函数:
    # 函数实现的第1个参数为线程ID，第2个参数为服务启动参数，第3个为连接信息
    # 需注意实现上应在每次循环时查询服务器关闭状态，如果遇到则结束处理
    __server_connect_deal_fun = None

    __self_tag = ""  # 自定义标识，用于发起端传入自身的识别标识
    __server_run_status = EnumNetServerRunStatus.Stop  # 服务端服务运行情况
    __server_run_status_lock = threading.RLock()  # 服务端状态变更的同步锁
    __server_connect_thread_id = 1  # 服务端的链接线程ID序列
    __server_connect_thread_list = {}  # 服务端正在运行的连接线程列表
    __server_connect_thread_list_lock = threading.RLock()  # 连接线程列表变更的同步锁

    #############################
    # 私有函数 - 子类可直接使用的函数
    #############################

    def _write_log(self, log_level=EnumLogLevel.INFO, log_str=''):
        """
        @fun 通用的日志登记函数
        @funName _write_log
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 通用的日志登记函数，调用初始化实例的日志打印函数输出日志

        @funParam {EnumLogLevel} log_level 打印的日志级别
        @funParam {string} log_str 要打印的日志内容

        """
        if self._logger is None:
            return
        else:
            if log_level.DEBUG:
                self._logger.debug(log_str)
            elif log_level.WARNING:
                self._logger.warning(log_str)
            elif log_level.ERROR:
                self._logger.error(log_str)
            elif log_level.CRITICAL:
                self._logger.critical(log_str)
            else:
                self._logger.info(log_str)

    def _server_status_change(self, server_status, result):
        """
        @fun 通用的服务器状态修改函数
        @funName _server_status_change
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 进行服务器的状态变更，并调用server_status_info_fun通知调用者
        
        @funParam {EnumNetServerRunStatus} server_status 要修改的服务器状态
        @funParam {generic.CResult} result 通用执行结果对象，其中自定义属性self_tag为发起方识别标识

        """
        self.__server_run_status = server_status
        if self.__server_status_info_fun is None:
            return
        else:
            result.self_tag = self.__self_tag
            self.__server_status_info_fun(server_status, result)

    #############################
    # 私有函数 -  框架内部处理函数
    #############################

    def __server_connect_thread_end(self, thread_id):
        """
        @fun 服务端连接线程结束清除线程池记录
        @funName __server_connect_thread_end
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 在服务端连接线程处理结束时调用，将线程ID从线程池记录中删除

        @funParam {int} thread_id 线程ID

        """
        self.__server_connect_thread_list_lock.acquire()
        try:
            del self.__server_connect_thread_list[thread_id]
        except:
            pass
        finally:
            self.__server_connect_thread_list_lock.release()

    def __server_connect_thread_clear(self):
        """
        @fun 删除服务端连接线程池记录
        @funName __server_connect_thread_clear
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 删除服务端连接线程池记录

        """
        self.__server_connect_thread_list_lock.acquire()
        try:
            self.__server_connect_thread_list.clear()
        except:
            pass
        finally:
            self.__server_connect_thread_list_lock.release()

    def __server_connect_thread_add(self, thread_id, thread_obj):
        """
        @fun 服务端连接线程池增加线程记录
        @funName __server_connect_thread_add
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 服务端启动一个新连接线程时，通过该函数新增线程池记录

        @funParam {int} thread_id 线程ID
        @funParam {Thread} thread_obj 线程对象

        """
        self.__server_connect_thread_list_lock.acquire()
        try:
            self.__server_connect_thread_list[thread_id] = thread_obj
        except:
            pass
        finally:
            self.__server_connect_thread_list_lock.release()

    def __start_server_thread_fun(self, tid, server_opts):
        """
        @fun 启动网络服务的监听线程函数
        @funName __start_server_thread_fun
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 启动网络服务的监听线程，步骤如下:
            1、启动监听服务_start_server_without_accept
            2、循环获取连接_accept_one
            3、每一个连接启动一个处理线程__server_connect_thread_fun
            4、本线程结束就代表网络服务停止
        
        @funParam {int} tid 线程id
        @funParam {object} server_opts 服务启动参数

        """
        DebugTools.debug_print(u'服务监听线程进入')
        _result = CResult(code=0, msg=u'成功')
        with ExceptionTools.ignored_cresult(result_obj=_result,
                                            logger=self._logger, self_log_msg=u'启动网络服务出现异常：'):
            # 统一的异常处理
            self._write_log(self._log_level, u'正在启动网络服务……')
            self._write_log(self._log_level,
                            u'启动参数：\n%s' % StringTools.format_obj_property_str(server_opts, is_deal_subobj=True))
            # 启动服务，但不接受连接
            _result = self._start_server_without_accept(server_opts)
            _server_info = _result.net_info
            if _result.code != 0:
                # 启动失败
                self._write_log(EnumLogLevel.ERROR, u'启动网络服务失败:%s - %s' % (str(_result.code), _result.msg))
                return
            # 启动成功，更新状态
            self._write_log(self._log_level, u'启动网络服务成功，开始监听客户端连接')
            self._server_status_change(EnumNetServerRunStatus.Running, _result)

            # 开始进入监听进程
            DebugTools.debug_print(u'服务监听线程循环处理')
            while True:
                if self.__server_run_status == EnumNetServerRunStatus.WaitStop:
                    # 收到指令等待停止
                    DebugTools.debug_print(u'服务监听线程收到指令等待停止')
                    while True:
                        if self.__server_run_status == EnumNetServerRunStatus.ForceStop:
                            # 过程中又被要求强制退出
                            break
                        if len(self.__server_connect_thread_list.keys()) > 0:
                            time.sleep(0.1)
                            continue
                        else:
                            # 线程已全部停止
                            break
                    break
                elif self.__server_run_status == EnumNetServerRunStatus.ForceStop:
                    # 收到指令马上停止
                    DebugTools.debug_print(u'服务监听线程收到指令马上停止')
                    break
                else:
                    # 正常监听下一个请求
                    DebugTools.debug_print(u'服务监听线程正常监听下一请求')
                    _accept_result = self._accept_one(server_opts, _server_info)
                    if _accept_result.code == 0:
                        # 获取到一个连接，创建线程
                        self.__server_connect_thread_id = self.__server_connect_thread_id + 1
                        _thread_id = self.__server_connect_thread_id
                        _new_thread = threading.Thread(
                            target=self.__server_connect_thread_fun,
                            args=(_thread_id, server_opts, _accept_result.net_info),
                            name='Thread-ConnectDeal' + str(_thread_id)
                        )
                        self.__server_connect_thread_add(_thread_id, _new_thread)
                        _new_thread.setDaemon(True)
                        _new_thread.start()
                    elif _accept_result.code != 3:
                        # 不是超时的其他获取错误，打印信息
                        self._write_log(EnumLogLevel.ERROR,
                                        u'网络服务获取网络请求出现错误：%s\n%s'
                                        % (_accept_result.msg, _accept_result.trace_str))
                    else:
                        DebugTools.debug_print(u'服务监听线程获取客户端连接超时')

                    # 继续下一个请求
                    continue

        # 线程结束就代表服务已关闭
        self.__server_connect_thread_clear()
        self._server_status_change(EnumNetServerRunStatus.Stop, _result)
        DebugTools.debug_print(u'服务监听线程结束')

    def __server_connect_thread_fun(self, thread_id, server_opts, net_info):
        """
        @fun 调用外围传入的网络连接处理线程的封装函数
        @funName __server_connect_thread_fun
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 该函数的主要目的是屏蔽调用程序的网络连接处理函数的异常

        @funParam {int} thread_id 线程ID
        @funParam {object} server_opts 网络服务的启动参数
        @funParam {object} net_info 网络的接入参数（例如socket对象）

        """
        with ExceptionTools.ignored_all(logger=self._logger,
                                        self_log_msg=u'网络服务出现异常', force_log_level=EnumLogLevel.ERROR):
            self.__server_connect_deal_fun(thread_id, server_opts, net_info, self.__self_tag)
        # 结束处理
        self.__server_connect_thread_end(thread_id)

    #############################
    # 公共属性
    # __slots__ = ('_server_opts', '__self_tag','__server_run_status') #可以通过该函数限定实例不可以动态绑定其他属性，这里不做限制
    #############################

    @property
    def log_level(self):
        """
        @property {get} 获取正常日志输出级别
        @propertyName log_level
        @propertyDescription 获取正常日志输出级别

        """
        return self._log_level

    @log_level.setter
    def log_level(self, value):
        """
        @property {set} 设置正常日志输出级别
        @propertyName log_level
        @propertyDescription 设置正常日志输出级别

        """
        self._log_level = value

    '''
    @property ServerOpts 获取服务器启动参数
    @demo
        opts = serverobj.ServerOpts
    '''

    @property
    def server_opts(self):
        """
        @property {get} 获取服务器启动参数
        @propertyName server_opts
        @propertyDescription 获取服务器启动参数

        @propertyExample {Python} 示例名:
            opts = serverobj.ServerOpts

        """
        return copy.deepcopy(self._server_opts)

    @property
    def self_tag(self):
        """
        @property {get} 获取调用方自定义标识
        @propertyName self_tag
        @propertyDescription 获取调用方自定义标识

        """
        return self.__self_tag

    @property
    def server_run_status(self):
        """
        @property {get} 获取服务端服务当前状态
        @propertyName server_run_status
        @propertyDescription 获取服务端服务当前状态

        """
        return self.__server_run_status

    @property
    def server_run_status_desc(self):
        """
        @property {get} 获取服务端服务当前状态的描述
        @propertyName server_run_status_desc

        """
        if self.__server_run_status == EnumNetServerRunStatus.Stop:
            return u"停止"
        elif self.__server_run_status == EnumNetServerRunStatus.WaitStop:
            return u"等待停止"
        elif self.__server_run_status == EnumNetServerRunStatus.WaitStart:
            return u"等待启动"
        elif self.__server_run_status == EnumNetServerRunStatus.ForceStop:
            return u"强制停止"
        else:
            return u"正在运行"

    #############################
    # 公共函数
    #############################

    def __init__(self, logger=None, server_status_info_fun=None, server_connect_deal_fun=None, self_tag='',
                 log_level=EnumLogLevel.INFO):
        """
        @fun 构造函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 构造函数
        
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
                net_info - 具体实现的连接信息（例如Socket对象）
                self_tag - 用于发起端传入自身的识别标识
            需注意实现上应在每次循环时查询服务器关闭状态，如果判断到服务器已关闭，应结束处理.
        @funParam {string} self_tag 自定义标识
        @funParam {EnumLogLevel} log_level 处理中正常日志的输出级别，默认为INFO，如果不想输出过多日志可以设置为DEBUG

        """
        self._logger = logger
        self.__server_status_info_fun = server_status_info_fun
        self.__server_connect_deal_fun = server_connect_deal_fun
        self.__self_tag = self_tag
        self._log_level = log_level

    def start_server(self, server_opts):
        """
        @fun 启动网络服务
        @funName start_server
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 根据传入的服务器参数，启动网络服务监听线程，注意服务必须处于停止状态才能启动
        
        @funParam {object} server_opts 启动服务器参数，由框架的实际实现类进行定义:
            子类通过_serverOpts.xxx获取具体的属性值
        
        @funReturn {generic.CResult} 启动结果，result.code：0-成功，1-服务不属于停止状态，不能启动，-1-异常

        """
        _result = CResult(code=0, msg=u'成功')
        with ExceptionTools.ignored_cresult(_result,
                                            logger=self._logger,
                                            self_log_msg=u'启动网络服务异常失败:',
                                            force_log_level=EnumLogLevel.ERROR):
            self._server_opts = server_opts
            # 先获取锁，拿到最准确的服务状态
            self.__server_run_status_lock.acquire()
            try:
                if self.__server_run_status != EnumNetServerRunStatus.Stop:
                    # 不属于停止状态，不能启动
                    _result.code = 1
                    _result.msg = self._error_code_map[1]
                    return _result

                # 执行启动服务的动作，通过线程方式启动，避免调用方等待
                self._server_status_change(EnumNetServerRunStatus.WaitStart, _result)
                _listen_thread = threading.Thread(
                    target=self.__start_server_thread_fun,
                    args=(1, server_opts),
                    name='Thread-ServerListen'
                )
                _listen_thread.setDaemon(True)
                _listen_thread.start()
            finally:
                # 释放锁
                self.__server_run_status_lock.release()
        # 返回结果
        return _result

    def stop_server(self, is_wait=True):
        """
        @fun 关闭网络服务
        @funName stop_server
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 关闭网络服务，设置网络服务为WaitStop-等待停止状态或ForceStop-强制停止状态，:
            由监听和处理线程内部执行关闭处理
        
        @funParam {bool} is_wait 是否等待服务器所有线程都处理完成后再关闭，True-等待所有线程完成处理，False-强制关闭
        
        @funReturn {generic.CResult} 停止结果，result.code：0-成功，2-停止服务失败：服务不处于运行状态，-1-异常

        """
        _result = CResult(code=0, msg=u'成功')
        with ExceptionTools.ignored_cresult(_result,
                                            logger=self._logger,
                                            self_log_msg=u'停止网络服务异常失败:',
                                            force_log_level=EnumLogLevel.ERROR):
            self.__server_run_status_lock.acquire()
            try:
                _status = EnumNetServerRunStatus.WaitStop
                if not is_wait:
                    _status = EnumNetServerRunStatus.ForceStop

                if self.__server_run_status == EnumNetServerRunStatus.Running:
                    # 运行状态，处理设置等待关闭状态
                    self._write_log(self._log_level, u"正在关闭服务")
                    self._server_status_change(_status, _result)
                elif self.__server_run_status == EnumNetServerRunStatus.WaitStop \
                        and _status == EnumNetServerRunStatus.ForceStop:
                    self._write_log(self._log_level, u"正在强制关闭服务")
                    self._server_status_change(_status, _result)
                else:
                    # 不属于运行状态，不能处理
                    _result.code = 2
                    _result.msg = self._error_code_map[2]
                    return _result
            finally:
                self.__server_run_status_lock.release()
        # 等待服务关闭
        while True:
            if self.__server_run_status == EnumNetServerRunStatus.Stop:
                break
            time.sleep(0.1)
        # 返回结果
        return _result

    #############################
    # 外部系统必须实现的接口对象（内部处理函数）
    #############################

    @abstractmethod  # 定义抽象方法，无需实现功能
    def _start_server_without_accept(self, server_opts):
        """
        @fun 启动网络服务但不接受连接
        @funName _start_server_without_accept
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 启动服务但不接受请求服务，该方法只做到启动端口层面，轮询监听不在该方法中实现:
            注意该该函数必须捕获并处理异常
        
        @funParam {object} server_opts 参数说明
        
        @funReturn {generic.CResult} 启动结果:
            result.code ：0-成功，其他值为失败
            result.net_info ：启动后的服务端网络连接信息对象，该对象将传给后续的监听线程（_AcceptOne）

        """
        # 子类必须定义该功能
        pass

    @abstractmethod  # 定义抽象方法，无需实现功能
    def _accept_one(self, server_opts, net_info):
        """
        @fun 监听接受一个请求并返回
        @funName _accept_one
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 提供监听并获取到请求连接返回的方法；注意该该函数必须捕获并处理异常
        
        @funParam {objcet} server_opts 网络服务启动参数
        @funParam {objcet} net_info 网络连接信息对象，_start_server_without_accept中获取到的结果
        
        @funReturn {generic.CResult} 获取网络连接结果:
            result.code ：0-成功，3-获取客户端连接请求超时
            result.net_info ：客户端连接信息对象，该对象将传给后续单个连接处理的线程

        """
        # 子类必须定义该功能
        pass

    # 外部系统必须实现的接口对象（公共函数）

    @staticmethod
    @abstractmethod  # 定义抽象方法，无需实现功能
    def recv_data(net_info, recv_para):
        """
        @fun 从网络连接获取数据
        @funName recv_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 从指定的网络连接中读取数据
        
        @funParam {object} net_info 要读取数据的网络信息对象（例如socket对象）
        @funParam {object} recv_para 读取数据的参数（例如长度、超时时间等，由实现类自定义）
        
        @funReturn {generic.CResult} 数据获取结果:
            result.code ：0-成功，4-获取数据超时，其他为获取失败
            result.data ：获取到的数据对象（具体类型和定义，由实现类自定义）
            result.recv_time : datetime 实际开始接受数据时间

        """
        # 子类必须定义该功能
        pass

    @staticmethod
    @abstractmethod  # 定义抽象方法，无需实现功能
    def send_data(net_info, send_para, data):
        """
        @fun 向网络连接写入数据
        @funName send_data
        @funGroup
        @funVersion
        @funDescription 向指定的网络连接发送数据
        
        @funParam {object} net_info 要写入数据的网络信息对象（例如socket对象）
        @funParam {object} send_para 写入数据的参数（例如长度、超时时间等，由实现类自定义）
        @funParam {object} data 要写入的数据对象（具体类型和定义，由实现类自定义）

        @funReturn {generic.CResult} 发送结果:
            result.code ：0-成功，5-写入数据超时，其他为写入失败
            result.send_time : datetime 实际发送完成时间

        """
        # 子类必须定义该功能
        pass

    @staticmethod
    @abstractmethod  # 定义抽象方法，无需实现功能
    def close_connect(net_info):
        """
        @fun 关闭网络连接
        @funName close_connect
        @funGroup
        @funVersion
        @funDescription 关闭指定的网络连接，注意该该函数必须捕获并处理异常
        
        @funParam {object} net_info 需要关闭的网络连接信息对象
        
        @funReturn {generic.CResult} 关闭结果
            result.code ：0-成功，其他值为失败
        
        """
        # 子类必须定义该功能
        pass

    @staticmethod
    @abstractmethod  # 定义抽象方法，无需实现功能
    def connect_server(connect_para):
        """
        @fun 客户端连接服务器函数
        @funName connect_server
        @funGroup
        @funVersion
        @funDescription 客户端通过该函数连接服务器端
        
        @funParam {object} connect_para 需要连接服务器的参数（例如IP、端口、超时时间等，由实现类自定义）
        
        @funReturn {generic.CResult} 连接结果:
            result.code ：0-成功，其他值为失败
            result.net_info ： 连接后的网络信息对象

        """
        # 子类必须定义该功能
        pass

    @abstractmethod
    def get_server_info(self, para_name):
        """
        @fun 获取服务器信息
        @funName get_server_info
        @funGroup
        @funVersion
        @funDescription 通用的获取服务器信息函数，根据传入的参数获取参数值（具体可以获取什么参数由实现类自定义）
        
        @funParam {string} para_name 参数名
        
        @funReturn {object} 返回具体的参数值对象（实现类自定义）
        
        """
        pass

    @staticmethod
    @abstractmethod
    def get_client_info(net_info, para_name):
        """
        @fun 获取客户端连接信息
        @funName get_client_info
        @funGroup
        @funVersion
        @funDescription 获取指定客户端连接的信息，根据传入的参数获取参数值（具体可以获取什么参数由实现类自定义）
        
        @funParam {object} net_info 客户端网络连接信息对象
        @funParam {string} para_name 参数名
        
        @funReturn {object} 返回具体的参数值对象（实现类自定义）
        
        """
        pass


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))
