#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : parallel.py


import uuid
import sys
import traceback
import copy
from datetime import datetime
import time
import queue
import threading
import multiprocessing
import inspect
import ctypes
from enum import Enum
# 通过gevent实现协程模式，pip install gevent
import gevent
import gevent.pool


__MoudleName__ = 'parallel'
__MoudleDesc__ = '提供并行处理的各项简化技术支持，包括协程、多线程、多进程、分布多进程、线程池、进程池等'
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/3/1'


#############################
# 自定义异常类
#############################
class ParaValueError(ValueError):
    """ Inappropriate argument value (of correct type). """
    def __init__(self, *args, **kwargs):  # real signature unknown
        pass

    @staticmethod  # known case of __new__
    def __new__(*args, **kwargs):  # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


class UnsupportError(ValueError):
    """ Inappropriate argument value (of correct type). """
    def __init__(self, *args, **kwargs):  # real signature unknown
        pass

    @staticmethod  # known case of __new__
    def __new__(*args, **kwargs):  # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


class TaskPoolStopedError(ValueError):
    """ Inappropriate argument value (of correct type). """
    def __init__(self, *args, **kwargs):  # real signature unknown
        pass

    @staticmethod  # known case of __new__
    def __new__(*args, **kwargs):  # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


class OvertimeError(ValueError):
    """ Inappropriate argument value (of correct type). """
    def __init__(self, *args, **kwargs):  # real signature unknown
        pass

    @staticmethod  # known case of __new__
    def __new__(*args, **kwargs):  # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass



class EnumParallelType(Enum):
    """
    @enum 并行类型
    @enumName EnumParallelType
    @enumDescription 描述

    """
    Coroutine = 'Coroutine'  # 携程模式
    Threading = 'Threading'  # 多线程模式
    MultiProcessing = 'MultiProcessing'  # 多进程模式
    RemoteProcessing = 'RemoteProcessing'  # 远程进程模式


class ParallelTaskPool(object):
    """
    @class 并行任务池（线程、进程池）
    @className ParallelTaskPool
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 类功能描述

    @classExample {Python} 示例名:
        类使用参考示例

    """

    #############################
    # 私有变量
    #############################
    _parallel_type = None
    _pool_size = 5
    _free_task_keep_time = 10  # 空闲任务保持时长（即长期空闲的任务将被删除），单位为秒
    _task_sleep_time = 0.5  # 空闲任务的休眠时长（获取任务之间的间隔），单位为秒，0代表不休眠
    _task_overtime = 0  # 任务执行超时时间
    _overtime_deamon_sleep_time = 5  # 任务执行超时监护进程每次检查休眠时间
    _wait_task_queue = None  # 等待处理的任务队列，根据线程或进程采取不同模式
    _max_task_queue_size = 0
    _wait_stop_flag = False  # 标识是否等待线程池停止
    _stop_flag = False  # 标识线程池是否已停止
    _pause_flag = False  # 标识线程池的处理是否暂停
    # 空闲的工作线程清单，填入的是线程或进程的uuid
    # 工作线程创建后加入该空闲线程清单，取到任务进行工作处理时从空闲清单移出，完成任务后再放入
    _free_workers = list()
    # 被创建的工作线程清单，key为线程或进程的uuid，value为线程或进程对象
    # 线程创建完成后放入字典，线程执行完成（正常完成或被强制中止）从字典移出
    _generate_workers = dict()
    # 任务执行状态
    #   key为任务号（uuid）
    #   value为二维数组，格式为[放入队列的datetime，开始执行的datetime, worker_id, task_obj-任务相关参数]
    # 任务在进入队列（put）的时候就放入该字典，任务处理完成（成功、异常、超时）的时候从字典中删除
    _task_status = dict()
    # 登记任务超时的清单，解决已超时但未开始执行的情况，key为任务的uuid，value为None
    #
    _task_overtime_list = dict()
    _task_status_lock = threading.RLock()  # 任务执行状态的更新锁

    #############################
    # 私有函数
    #############################

    @staticmethod
    def _async_thread_raise(tid, exctype):
        """
        @fun 线程异常抛出异常的函数，用于异步抛出异常结束线程
        @funName _async_thread_raise
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {参数类型} 参数名 参数说明

        @funReturn {返回值类型} 返回值说明

        @funExample {代码格式} 示例名:
            函数使用参考示例

        """
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def _add_task_status(self, task_obj):
        """
        @fun 将任务对象放入状态记录中
        @funName _add_task_status
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        """
        self._task_status_lock.acquire()
        try:
            # task_job = [_id, target, args, kwargs, name, callback, exception_callback, wait_finish, task_overtime]
            self._task_status[task_obj[0]] = [datetime.now(), None, None, task_obj]
        except:
            pass
        finally:
            self._task_status_lock.release()


    def _del_task_status(self, task_id):
        """
        @fun 添加任务状态记录
        @funName _add_task_status
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {uuid} task_id 任务ID

        """
        self._task_status_lock.acquire()
        try:
            del self._task_status[task_id]
        except:
            pass
        finally:
            self._task_status_lock.release()

    def _generate_worker(self):
        """
        @fun 创建新工作线程
        @funName _generate_worker
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {参数类型} 参数名 参数说明

        @funReturn {返回值类型} 返回值说明

        @funExample {代码格式} 示例名:
            函数使用参考示例

        """
        if self._parallel_type == EnumParallelType.Threading:
            # 创建线程
            _worker_obj = threading.Thread(target=self._worker_fun)
            _worker_obj.setDaemon(True)  # 线程结束自动结束
            _worker_obj.start()  # 启动线程

    def _kill_worker(self, worker_id, task_id):
        """
        @fun 强制删除正在执行的任务工作线程
        @funName _kill_worker
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {uuid} worker_id 任务处理线程id
        @funParam {uuid} task_id 当前正在处理的任务对象ID

        """
        # 先检查任务跟worker是否一致
        self._task_status_lock.acquire()
        try:
            if task_id not in self._task_status.keys():
                # 已经处理过，任务不在清单，不处理
                return
            _task_status = self._task_status[task_id]
            if _task_status[1] != worker_id:
                # 线程和任务不对应，不处理
                return
            # 结束线程
            if self._parallel_type == EnumParallelType.Threading:
                # 线程方式处理
                _thread_obj = self._generate_workers[worker_id]
                ParallelTaskPool.stop_thread(_thread_obj.ident, OvertimeError)

            # 删除线程id
            try:
                self._free_workers.remove(worker_id)
            except:
                pass
            try:
                del self._generate_workers[worker_id]
            except:
                pass
        except:
            pass
        finally:
            self._task_status_lock.release()

    def _put_task_to_queue(self, task_obj):
        """
        @fun 将任务放入待处理队列
        @funName _put_task_to_queue
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        """
        self._add_task_status(task_obj=task_obj)
        # 放入待处理清单
        try:
            if self._parallel_type == EnumParallelType.Threading:
                self._wait_task_queue.put(task_obj)
        except:
            # 可能有超过长度的异常，从状态列表删除
            self._del_task_status(task_id=task_obj[0])
            raise sys.exc_info()


    def _get_task_from_queue(self, worker_id):
        """
        @fun 从队列中获取任务
        @funName _get_task_from_queue
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {uuid} worker_id 任务处理线程id

        @funReturn {object} 返回队列中的对象，如果获取不到返回None

        """
        self._task_status_lock.acquire()
        try:
            if self._parallel_type == EnumParallelType.Threading:
                # 线程模式的队列获取
                try:
                    _task_obj = None
                    while True:
                        _task_obj = self._wait_task_queue.get(block=False)  # 不阻塞，直接返回
                        if _task_obj[0] in self._task_overtime_list.keys():
                            # 在超时清单中，不再进行处理，继续获取下一个
                            del self._task_overtime_list[_task_obj[0]]
                            _task_obj = None
                            continue
                        else:
                            # 不在超时清单中，登记任务状态，然后直接返回
                            self._task_status[_task_obj[0]] = [datetime.now(), worker_id, _task_obj]  # 登记任务信息
                            return _task_obj
                except:
                    # 有异常代表获取不到队列数据，清理掉超时处理清单，因为清单中的任务都已经处理完成
                    self._task_overtime_list.clear()
                    return None
        finally:
            self._task_status_lock.release()

    def _worker_fun(self):
        """
        @fun 通用的任务获取及执行函数
        @funName _worker_fun
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 该函数为线程或进程执行函数，在应保持线程一直循环获取任务并执行
        @funExcepiton:
            异常类名 异常说明

        @funParam {参数类型} 参数名 参数说明

        @funReturn {返回值类型} 返回值说明

        @funExample {代码格式} 示例名:
            函数使用参考示例

        """
        _worker_id = uuid.uuid1()
        _worker_obj = None
        if self._parallel_type == EnumParallelType.Threading:
            _worker_obj = threading.current_thread()
        # 将worker信息放入实例队列
        self._generate_workers[_worker_id] == _worker_obj
        self._free_workers.append(_worker_id)
        _last_work_time = datetime.now()  # 上一次工作的时间
        # 循环进行线程处理
        try:
            while True:
                self._free_workers.remove(_worker_id)  # 先认为要进入工作，标记线程在工作
                try:
                    if self._stop_flag:
                        # 判断是否结束线程池，结束线程
                        break
                    if self._pause_flag:
                        # 判断是否暂停线程池，不抓取任务处理
                        continue

                    # 从队列中获取任务
                    _task_obj = self._get_task_from_queue(worker_id=_worker_id)
                    if _task_obj is None:
                        # 获取不到任务，检查是否满足释放线程的时间条件
                        if (datetime.now() - _last_work_time).seconds > self._free_task_keep_time:
                            # 超过释放时间
                            break
                        else:
                            # 进入下一个循环
                            continue

                    # 执行函数
                    try:
                        _res = _task_obj[1](*_task_obj[2], **_task_obj[3])
                        if _task_obj[5] is not None:
                            # 处理callback
                            try:
                                # 参数顺序：res, args, kwargs, name
                                _task_obj[5](
                                    _res,
                                    _task_obj[2],
                                    _task_obj[3],
                                    _task_obj[4]
                                )
                            except:
                                pass
                    except:
                        # 执行出现异常，处理exception_callback
                        if _task_obj[6] is not None:
                            try:
                                # 参数顺序：error, trace_str, args, kwargs, name
                                _task_obj[6](
                                    sys.exc_info(),
                                    traceback.format_exc(),
                                    _task_obj[2],
                                    _task_obj[3],
                                    _task_obj[4]
                                )
                            except:
                                pass
                    finally:
                        # 处理完成，从队列中删除状态记录，代表已完成
                        self._del_task_status(_task_obj[0])
                        _last_work_time = datetime.now()  # 登记上一次工作的时间
                finally:
                    self._free_workers.append(_worker_id)  # 完成处理，标记为空闲状态
                    if self._task_sleep_time > 0:
                        time.sleep(self._task_sleep_time)  # 休眠，准备下一次处理
        finally:
            # 关闭线程，将自己从队列中删除
            self._free_workers.remove(_worker_id)
            del self._generate_workers[_worker_id]

    def _overtime_deamon_fun(self):
        """
        @fun 监测是否存在任务超时的处理线程
        @funName _overtime_deamon_fun
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        """
        while True:
            try:
                _task_id_list = copy.deepcopy(self._task_status.keys())  # 通过复制一份清单处理，避免长期锁对象
                for _task_id in _task_id_list:
                    # 锁住状态清单获取信息
                    _start_time = None
                    _work_id = None
                    _task_overtime = None
                    _task_obj = None
                    self._task_status_lock.acquire()
                    try:
                        if _task_id not in self._task_status.keys():
                            # 已经处理完成或被清除掉，继续处理下一个
                            continue
                        _start_time = self._task_status[_task_id][0]
                        _task_overtime = self._task_status[_task_id][8]
                        _task_obj = self._task_status[_task_id]
                    finally:
                        self._task_status_lock.release()

                    # 判断是否超时
                    if _task_overtime == 0:
                        _task_overtime = self._task_overtime
                    elif self._task_overtime > 0 and self._task_overtime < _task_overtime:
                        _task_overtime = self._task_overtime
                    if _task_overtime > 0 and (datetime.now() - _start_time).seconds > _task_overtime:
                        # 该任务超时了，强制结束任务，并启动一条新的任务线程
                        self._generate_workers()

                        # 强制删除工作线程
                        self._kill_worker(worker_id=_work_id, task_id=_task_obj[0])




                    _start_time = self._task_status[_work_id][0]
                    _task_obj = self._task_status[_work_id][1]  # 先获取任务信息

                    if _task_obj[8] > 0 and _task_obj[8] < _task_overtime:
                        _task_overtime = _task_obj[8]
                    if _task_overtime > 0 and _start_time is not None and (datetime.now() - _start_time).seconds > _task_overtime:
                        # 该任务超时了，强制结束任务，并启动一条新的任务线程
                        self._generate_workers()
                        # 强制删除工作线程
                        self._kill_worker(worker_id=_work_id, task_id=_task_obj[0])

                        # 任务向外反馈超时异常

            except:
                pass
            # 继续等待下一次处理，休眠一段时间
            time.sleep(self._overtime_deamon_sleep_time)

    #############################
    # 公共函数
    #############################

    @staticmethod
    def stop_thread(thread_ident, exctype):
        """
        @fun 结束指定线程
        @funName stop_thread
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {int} thread_ident 线程的线程标识ident，例如t.ident
        @funParam {class} exctype 异常的类名，例如SystemExit

        """
        try:
            ParallelTaskPool._async_thread_raise(thread_ident, exctype)
        except:
            pass

    def __init__(self, parallel_type=EnumParallelType.Threading, pool_size=5, max_task_queue_size=0,
                 free_task_keep_time=5, task_sleep_time=0.5, task_overtime=0, overtime_deamon_sleep_time=5):
        """
        @fun 构造函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            UnsupportError 当parallel_type类型不支持的时候抛出该异常

        @funParam {EnumParallelType} parallel_type 任务池的任务类别
        @funParam {int} pool_size 任务池大小（即允许的并发数），必须为>0的整数
        @funParam {int} max_task_queue_size 任务缓存队列的最大数量（等待处理的任务数），0代表无限制
        @funParam {float} free_task_keep_time 空闲任务保持时长（即长期空闲的任务将被删除），单位为秒
        @funParam {float} task_sleep_time 空闲任务的休眠时长（获取任务之间的间隔），单位为秒，0代表不休眠
        @funParam {float} task_overtime 任务执行的超时时间，如果发现超时则强制结束线程处理，并抛出异常:
            单位为秒，0代表不监测超时
        @funParam {float} overtime_deamon_sleep_time 任务执行超时监护进程每次检查休眠时间，单位为秒

        @funReturn {返回值类型} 返回值说明

        @funExample {代码格式} 示例名:
            函数使用参考示例
            https://www.cnblogs.com/hjc4025/p/6950157.html

        """
        self._parallel_type = parallel_type
        self._pool_size = pool_size
        self._max_task_queue_size = max_task_queue_size
        self._free_task_keep_time = free_task_keep_time
        self._task_sleep_time = task_sleep_time
        self._task_overtime = task_overtime
        if task_overtime is None or task_overtime < 0:
            self._task_overtime = 0
        self._overtime_deamon_sleep_time = overtime_deamon_sleep_time
        self._stop_flag = False

        # 初始化队列
        if parallel_type == EnumParallelType.Threading:
            # 线程，用普通队列就好
            if max_task_queue_size == 0:
                self._wait_task_queue = queue.Queue()
            else:
                self._wait_task_queue = queue.Queue(maxsize=max_task_queue_size)
        else:
            # 不支持的类型，抛出异常
            raise UnsupportError('unsuport parallel_type: EnumParallelType.%s' % str(EnumParallelType.value))

        # 启动超时任务执行监控进程
        _overtime_deamon = threading.Thread(target=self._overtime_deamon_fun)
        _overtime_deamon.setDaemon(True)  # 线程结束自动结束
        _overtime_deamon.start()  # 启动线程

    def put_task(self, target=None, name=None, args=(), kwargs=None, callback=None, exception_callback=None, wait_finish=False, task_overtime=0):
        """
        @fun 将任务放入队列执行
        @funName put_task
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            TaskPoolStopedError 当任务未完成但遇到了停止标志时抛出该异常

        @funParam {func} target 目标函数
        @funParam {string} name 线程名
        @funParam {tuple} args 函数运行参数(顺序格式)
        @funParam {dict} kwargs 函数运行参数(kv格式)
        @funParam {func} callback 结果回调函数，函数定义为fun(res, args, kwargs, name)，无需返回值
            res为并发任务的返回值，无返回值则为None
            args、kwargs为函数的入参
            name为任务名
        @funParam {func} exception_callback 异常回调函数，函数定义为fun(error, trace_str, args, kwargs, name)，无需返回值
            args、kwargs为函数的入参
            name为任务名
            error为Exception类，发生异常时的sys.exc_info()三元组对象(type, value, traceback):
            trace_str 错误追踪堆栈日志，异常时的traceback.format_exc()
        @funParam {bool} wait_finish 是否等待目标函数执行完成才返回
        @funParam {float} task_overtime 任务执行的超时时间，如果发现超时则强制结束线程处理，并抛出异常:
            单位为秒，0代表不监测超时

        """
        if self._wait_stop_flag or self._stop_flag:
            # 任务池已被停止，抛出异常
            raise TaskPoolStopedError('task pool has stoped!')

        if len(self._free_workers) == 0 and len(self._generate_workers) < self._pool_size:
            # 创建新线程
            self._generate_workers()

        # 将任务放到队列
        _id = uuid.uuid1()
        _task_overtime = task_overtime
        if task_overtime is None or task_overtime < 0:
            _task_overtime = 0
        _task_job = [_id, target, args, kwargs, name, callback, exception_callback, wait_finish, _task_overtime]
        # 放入待处理清单
        self._put_task_to_queue(task_obj=_task_job)
        if wait_finish:
            # 需要等待线程结束
            while True:
                if _id in self._task_status.keys():
                    # 未完成
                    if self._stop_flag:
                        # 未完成但遇到线程池关闭的情况，抛出异常
                        raise TaskPoolStopedError('task pool has stoped!')
                    else:
                        time.sleep(0.1)
                        continue
                else:
                    # 已完成
                    break

    def stop_task_pool(self, wait_finish=True):
        """
        @fun 停止线程池
        @funName stop_task_pool
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {bool} wait_finish 是否等待所有待处理任务执行完成才返回

        """
        if wait_finish:
            self._wait_stop_flag = True  # 标记任务池待停止，不再接收新的任务
            # 等待所有待处理任务完成
            while True:
                if not self._stop_flag and len(self._wait_task_queue) == 0:
                    # 已经无待处理任务，可以将停止标记设置为True，正式停止线程
                    self._stop_flag = True
                    continue
                if len(self._generate_workers) == 0:
                    # 线程已经全部退出
                    return
                time.sleep(0.5)
        else:
            # 不等待所有处理结束，等级标记即可(可能会有实际执行完但状态不对的情况)
            self._wait_stop_flag = True
            self._stop_flag = True

    def pause_task_pool(self, wait_finish=True):
        """
        @fun 暂停线程池处理
        @funName pause_task_pool
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {bool} wait_finish 是否等待当前正在处理的任务执行完成才返回

        """
        self._pause_flag = True
        if wait_finish:
            while len(self._generate_workers) != len(self._free_workers):
                # 只要空闲线程的数量和创建线程的数量不一样，就说明有任务正在执行





class Parallel(object):
    """
    @class 并行处理封装类
    @className Parallel
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 类功能描述

    @classExample {Python} 示例名:
        类使用参考示例

    """

    #############################
    # 静态类
    #############################

    @staticmethod
    def simple_task_decorator(parallel_type=EnumParallelType.Threading, is_asyn=False, name='', callback=None):
        """
        @fun 简单任务函数修饰符定义
        @funName simple_task_decorator
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            ReferenceError 当EnumParallelType不支持时抛出异常

        @funParam {EnumParallelType} parallel_type 并发任务类型
        @funParam {bool} is_asyn 是否异步模式，True-异步模式，函数立即返回；False-同步模式，函数阻塞等待执行完成再返回
        @funParam {string} name 线程名
        @funParam {func} callback 结果回调函数，函数定义为fun(res)，无需返回值，res为并发任务的返回值，无返回值则为None

        @funExample {python} 示例参考:
            @Parallel.simple_task_decorator(parallel_type=EnumParallelType.Threading, is_asyn=False)
            def parallel_task_fun(para1=xx, para2=xx, ...):
                # 需要并行处理的函数定义，如果是协程模式，还要注意在主进程中通过gevent.sleep给到协程函数CPU空闲
                # 此外，对于协程函数中涉及IO的操作，需通过gevent.monkey引入socket等高IO的协程处理类，实现真正的协程处理
                pass

            # 然后在需要执行协程的地方，执行协程函数
            parallel_task_fun(para1=xx, para2=xx, ...)

        """
        def task(func):  # 修饰符函数封装
            def task_args(*args, **kwargs):  # 参数处理
                if parallel_type == EnumParallelType.Coroutine:
                    # 协程模式，马上执行
                    _task_obj = gevent.spawn(Parallel._callback_fun_caller, *(func, args, kwargs, callback))
                    if is_asyn:
                        # 异步模式，通过阻塞空任务的形式快速返回
                        _null_task = gevent.spawn(Parallel._null_execute_fun)
                        _null_task.join()
                    else:
                        # 同步模式，等待函数执行完才返回
                        _task_obj.join()
                elif parallel_type == EnumParallelType.Threading:
                    # 线程模式
                    _task_obj = threading.Thread(
                        target=func,
                        args=(func, args, kwargs, callback),
                        name=name
                    )
                    _task_obj.setDaemon(True)  # 程序关闭时自动结束，不考虑状态问题，具体状态处理由应用逻辑考虑
                    _task_obj.start()
                    if not is_asyn:
                        # 同步模式，等待线程执行完成
                        _task_obj.join()
                else:
                    # 异常情况
                    raise ReferenceError
            return task_args
        return task

    @staticmethod
    def create_simple_task(target=None, name=None, args=(), kwargs=None,
                           parallel_type=EnumParallelType.Threading, is_asyn=False):
        """
        @fun 创建并发任务
        @funName create_simple_task
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            ReferenceError 当EnumParallelType不支持时抛出异常

        @funParam {func} target 目标函数
        @funParam {string} name 线程名
        @funParam {tuple} args 函数运行参数(顺序格式)
        @funParam {dict} kwargs 函数运行参数(kv格式)
        @funParam {EnumParallelType} parallel_type 并发任务类型
        @funParam {bool} is_asyn 是否异步模式，True-异步模式，函数立即返回；False-同步模式，函数阻塞等待执行完成再返回
            该参数仅在is_run_immediately为True的情况下生效

        """
        if parallel_type == EnumParallelType.Coroutine:
            # 协程,马上执行
            _task_obj = gevent.spawn(target, *args, **kwargs)
            if is_asyn:
                # 异步模式，通过阻塞空任务的形式快速返回
                _null_task = gevent.spawn(Parallel._null_execute_fun)
                _null_task.join()
            else:
                # 同步模式，等待函数执行完才返回
                _task_obj.join()
        elif parallel_type == EnumParallelType.Threading:
            # 线程模式
            _task_obj = threading.Thread(
                target=target,
                args=args,
                kwargs=kwargs,
                name=name
            )
            _task_obj.setDaemon(True)  # 程序关闭时自动结束，不考虑状态问题，具体状态处理由应用逻辑考虑
            _task_obj.start()
        else:
            # 异常情况
            raise ReferenceError

    #############################
    # 私有变量
    #############################
    _parallel_type = EnumParallelType.Threading  # 并发处理模式
    _wait_task_list = list()  # 等待执行的任务清单
    _task_pool_size = 0  # 线程池大小，<= 0代表不使用线程池
    _pool = None  # 线程池对象

    #############################
    # 私有函数
    #############################

    @staticmethod
    def _null_execute_fun():
        """
        @fun 不执行任何操作的函数，用于空跑
        @funName _null_execute_fun
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        """
        pass

    @staticmethod
    def _callback_fun_caller(target=None, args=(), kwargs=None, callback=None):
        """
        @fun 封装函数，让并发任务支持结果回调函数
        @funName _callback_fun_caller
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {func} target 目标函数
        @funParam {tuple} args 函数运行参数(顺序格式)
        @funParam {dict} kwargs 函数运行参数(kv格式)
        @funParam {func} callback 结果回调函数，函数定义为fun(res)，无需返回值，res为并发任务的返回值，无返回值则为None

        """
        if callback is not None:
            _res = target(*args, **kwargs)
            callback(_res)
        else:
            # 直接执行
            target(*args, **kwargs)

    #############################
    # 公共函数
    #############################

    def __init__(self, parallel_type=EnumParallelType.Threading, task_pool_size=0, **kwargs):
        """
        @fun 函数中文名
        @funName
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {EnumParallelType} parallel_type 并发处理模式

        """
        self._parallel_type = parallel_type
        self._task_pool_size = task_pool_size
        if parallel_type == EnumParallelType.Coroutine:
            # 是否使用线程池
            if task_pool_size > 0:
                self._pool = gevent.pool.Pool(task_pool_size)
            else:
                self._pool = gevent  # 简化后面调用的代码

    def task_decorator(
            self,
            is_run_immediately=False,
            is_asyn=False,
            callback=None
    ):
        """
        @fun 任务函数修饰符定义
        @funName task_decorator
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 定义
        @funExcepiton:
            ReferenceError 当EnumParallelType不支持时抛出异常

        @funParam {bool} is_run_immediately 是否立即执行
        @funParam {bool} is_asyn 是否异步模式，True-异步模式，函数立即返回；False-同步模式，函数阻塞等待执行完成再返回
            该参数仅在is_run_immediately为True的情况下生效
        @funParam {func} callback 结果回调函数，函数定义为fun(res)，无需返回值，res为并发任务的返回值，无返回值则为None

        @funExample {python} 示例参考:
            _Parallel_Obj = task_decorator(parallel_type=EnumParallelType.Coroutine)
            @_Parallel_Obj.task_decorator(is_run_immediately=False)
            def parallel_task_fun(para1=xx, para2=xx, ...):
                # 需要并行处理的函数定义，如果是协程模式，还要注意在主进程中通过gevent.sleep给到协程函数CPU空闲
                # 此外，对于协程函数中涉及IO的操作，需通过gevent.monkey引入socket等高IO的协程处理类，实现真正的协程处理
                # 并通过monkey.patch_all()将IO类替换为支持协程的IO类
                pass

            # 然后在需要执行协程的地方，执行协程函数
            parallel_task_fun(para1=xx, para2=xx, ...)

        """
        def task(func):  # 修饰符函数封装
            def task_args(*args, **kwargs):  # 参数处理
                if self._parallel_type == EnumParallelType.Coroutine:
                    if is_run_immediately:
                        # 马上执行
                        _task_obj = self._pool.spawn(Parallel._callback_fun_caller, *(func, args, kwargs, callback))
                        if is_asyn:
                            # 异步模式，通过阻塞空任务的形式快速返回
                            _null_task = self._pool.spawn(Parallel._null_execute_fun)
                            _null_task.join()
                        else:
                            # 同步模式，等待函数执行完才返回
                            _task_obj.join()
                    else:
                        # 只放到代办任务中
                        self._wait_task_list.append([func, args, kwargs, callback])
                else:
                    # 异常情况
                    raise ReferenceError
            return task_args
        return task

    def create_task(self, target=None, name=None, args=(), kwargs=None, is_run_immediately=False, is_asyn=False, callback=None):
        """
        @fun 创建并发任务
        @funName create_task
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            ReferenceError 当EnumParallelType不支持时抛出异常

        @funParam {func} target 目标函数
        @funParam {string} name 线程名
        @funParam {tuple} args 函数运行参数(顺序格式)
        @funParam {dict} kwargs 函数运行参数(kv格式)
        @funParam {bool} is_run_immediately 是否立即执行
        @funParam {bool} is_asyn 是否异步模式，True-异步模式，函数立即返回；False-同步模式，函数阻塞等待执行完成再返回
            该参数仅在is_run_immediately为True的情况下生效
        @funParam {func} callback 结果回调函数，函数定义为fun(res)，无需返回值，res为并发任务的返回值，无返回值则为None

        """
        if self._parallel_type == EnumParallelType.Coroutine:
            # 协程
            if is_run_immediately:
                # 马上执行
                _task_obj = self._pool.spawn(Parallel._callback_fun_caller, *(target, args, kwargs, callback))
                if is_asyn:
                    # 异步模式，通过阻塞空任务的形式快速返回
                    _null_task = self._pool.spawn(Parallel._null_execute_fun)
                    _null_task.join()
                else:
                    # 同步模式，等待函数执行完才返回
                    _task_obj.join()
            else:
                # 只放到代办任务中
                self._wait_task_list.append([target, args, kwargs, callback])
        else:
            # 异常情况
            raise ReferenceError

    def run_wait_task(self, is_asyn=False):
        """
        @fun 函数中文名
        @funName 执行任务函数修饰符定义函数的待处理任务
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            ReferenceError 当EnumParallelType不支持时抛出异常

        @funParam {bool} is_asyn 是否异步模式，True-异步模式，函数立即返回；False-同步模式，函数阻塞等待执行完成再返回

        """
        if self._parallel_type == EnumParallelType.Coroutine:
            if is_asyn:
                # 异步模式
                for _task_para in self._wait_task_list:
                    _task_obj = self._pool.spawn(Parallel._callback_fun_caller,
                                                 *(_task_para[0], _task_para[1], _task_para[2], _task_para[3]))
                _null_task = self._pool.spawn(self._null_execute_fun)
                _null_task.join()
            else:
                # 同步模式
                _task_list = list()
                for _task_para in self._wait_task_list:
                    _task_list.append(self._pool.spawn(Parallel._callback_fun_caller,
                                                       *(_task_para[0], _task_para[1], _task_para[2], _task_para[3])))
                gevent.joinall(_task_list)
        else:
            # 异常情况
            raise ReferenceError


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))
