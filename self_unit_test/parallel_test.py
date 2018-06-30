#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : parallel_test.py

import asyncio
import time
from parallel import *
import gevent
from gevent import pool

__MoudleName__ = 'parallel_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/3/1'

_Parallel_Coroutine_Obj = Parallel(parallel_type=EnumParallelType.Coroutine, task_pool_size=0)


def callback_fun(res):
    print("callback_fun: " + str(res))

@_Parallel_Coroutine_Obj.task_decorator(is_run_immediately=False, callback=callback_fun)
def coroutine_task_1(para1='a', para2=2):
    # 非马上执行
    _i = 0
    while _i < 5:
        print('coroutine_task_1: para1=%s para2=%s _i:%s' % (para1, str(para2), str(_i)))
        gevent.sleep(0.5)
        _i += 1
    return 'coroutine_task_1 callback res'

@_Parallel_Coroutine_Obj.task_decorator(is_run_immediately=True, is_asyn=False, callback=callback_fun)
def coroutine_task_2(para1='a', para2=2):
    # 马上执行，同步等待完成状态
    _i = 0
    while _i < 5:
        print('coroutine_task_1: para1=%s para2=%s _i:%s' % (para1, str(para2), str(_i)))
        gevent.sleep(0.5)
        _i += 1
    return 'coroutine_task_2 callback res'


@_Parallel_Coroutine_Obj.task_decorator(is_run_immediately=True, is_asyn=True, callback=callback_fun)
def coroutine_task_asyn_2(para1='a', para2=2):
    # 马上执行，异步执行状态
    _i = 0
    while _i < 5:
        print('coroutine_task_asyn_2: para1=%s para2=%s _i:%s' % (para1, str(para2), str(_i)))
        gevent.sleep(0.5)
        _i += 1
    return 'coroutine_task_asyn_2 callback res'


def test_coroutine_1():
    print('非马上执行，同步等待完成状态，开始：')
    print("装载 p1")
    coroutine_task_1(para1='p1', para2=1)
    print("装载 p2")
    coroutine_task_1(para1='p2', para2=2)
    print("装载 p3")
    coroutine_task_1(para1='p3', para2=3)
    print("装载 p4")
    coroutine_task_1(para1='p4', para2=4)
    print("装载 p5")
    coroutine_task_1(para1='p5', para2=5)
    print("统一发起执行，同步等待完成状态...")
    _Parallel_Coroutine_Obj.run_wait_task(is_asyn=False)
    print('执行完成，应无再输出')


def test_coroutine_2():
    print('非马上执行，异步执行状态，开始：')
    print("装载 p1_asyn")
    coroutine_task_1(para1='p1_asyn', para2=1)
    print("装载 p2_asyn")
    coroutine_task_1(para1='p2_asyn', para2=2)
    print("装载 p3_asyn")
    coroutine_task_1(para1='p3_asyn', para2=3)
    print("装载 p4_asyn")
    coroutine_task_1(para1='p4_asyn', para2=4)
    print("装载 p5_asyn")
    coroutine_task_1(para1='p5_asyn', para2=5)
    print("统一发起执行，应马上完成...")
    _Parallel_Coroutine_Obj.run_wait_task(is_asyn=True)
    print('未完成执行，先返回结果')
    _i = 0
    while _i < 14:
        print('等待：'+str(_i))
        gevent.sleep(0.5)  # 注意主进程一定要通过gevent.sleep(1)为协程提供执行的CPU空闲资源
        _i += 1


def test_coroutine_3():
    print('马上执行，同步执行状态，开始：')
    print("start p1")
    coroutine_task_2(para1='p1', para2=1)
    print("start p2")
    coroutine_task_2(para1='p2', para2=2)
    print("start p3")
    coroutine_task_2(para1='p3', para2=3)
    print("start p4")
    coroutine_task_2(para1='p4', para2=4)
    print("start p5")
    coroutine_task_2(para1='p5', para2=5)
    print('同步执行状态，应按顺序完成各协程函数，然后再退出')


def test_coroutine_4():
    print('马上执行，异步执行状态，开始：')
    print("start p1")
    coroutine_task_asyn_2(para1='p1', para2=1)
    print("start p2")
    coroutine_task_asyn_2(para1='p2', para2=2)
    print("start p3")
    coroutine_task_asyn_2(para1='p3', para2=3)
    print("start p4")
    coroutine_task_asyn_2(para1='p4', para2=4)
    print("start p5")
    coroutine_task_asyn_2(para1='p5', para2=5)
    print('异步执行状态，应可以直接执行到该步骤')
    _i = 0
    while _i < 3:
        print('等待：' + str(_i))
        gevent.sleep(3)  # 注意主进程一定要通过gevent.sleep(1)为协程提供执行的CPU空闲资源
        _i += 1



if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    # test_coroutine_1()

    # test_coroutine_2()

    # test_coroutine_3()

    test_coroutine_4()



