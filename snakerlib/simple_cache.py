#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : simple_cache.py


import threading
import functools
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod  # 利用abc模块实现抽象类


__MoudleName__ = 'simple_cache'
__MoudleDesc__ = '缓存处理框架'
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/2/23'


class EnumCacheSortedOrder(Enum):
    """
    @enum 缓存排序优先规则
    @enumName EnumCacheSortedOrder
    @enumDescription 描述

    """
    HitTimeFirst = 'HitTimeFirst'  # 按命中时间优先排序
    HitCountFirst = 'HitCountFirst'  # 按命中次数优先排序


class BaseCache(ABC):
    """
    @class 基础缓存理定义基类
    @className BaseCache
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 定义缓存处理的基本框架函数

    """

    #############################
    # 内部变量
    #############################

    _cache_size = 10  # 缓存大小，<=0 代表没有限制
    # 缓存使用情况登记字典
    # key为缓存唯一识别标识，value为使用情况登记字典，固定登记信息key包括:
    #   last_hit_time - datetime最后一次命中时间，hit_count - int 命中次数
    _cache_hit_info = dict()
    _cache_data = dict()  # 缓存数据登记字典，key为缓存唯一识别标识，value为缓存数据
    _sortedorder = EnumCacheSortedOrder.HitTimeFirst  # 缓存排序优先规则
    _cache_change_lock = threading.RLock()  # 为保证缓存信息的一致性，需要控制的锁

    #############################
    # 构造函数
    #############################

    def __init__(self, size=10, sorted_order=EnumCacheSortedOrder.HitTimeFirst):
        """
        @fun 构造函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {int} size 缓存大小，<=0 代表没有限制
        @funParam {EnumCacheSortedOrder} sorted_order 缓存排序优先规则

        """
        self._cache_size = size
        self._sortedorder = sorted_order

    #############################
    # 内部函数
    #############################

    @staticmethod
    def _hit_info_sorted_compare(hit_info_x, hit_info_y, sorted_order=EnumCacheSortedOrder.HitTimeFirst):
        """
        @fun 用于进行命中信息的排序处理
        @funName _hit_info_sorted_compare
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 用于字典的sorted排序函数
        @funExcepiton:
            异常类名 异常说明

        @funParam {dict} hit_info_x 命中信息字典x，格式为[{'last_hit_time':?, 'hit_count':?}, key]
        @funParam {dict} hit_info_y 命中信息字典y，格式为[{'last_hit_time':?, 'hit_count':?}, key]

        @funReturn {int} 比较结果：
            0 : 相等
            -1 : x 排在前面
            1 : y排在前面

        """
        if sorted_order == EnumCacheSortedOrder.HitTimeFirst:
            # 命中时间优先
            if hit_info_x[0]['last_hit_time'] > hit_info_y[0]['last_hit_time']:
                return -1
            elif hit_info_x[0]['last_hit_time'] < hit_info_y[0]['last_hit_time']:
                return 1
            else:
                if hit_info_x[0]['hit_count'] > hit_info_y[0]['hit_count']:
                    return -1
                elif hit_info_x[0]['hit_count'] < hit_info_y[0]['hit_count']:
                    return 1
                else:
                    return 0
        else:
            # 命中次数优先
            if hit_info_x[0]['hit_count'] > hit_info_y[0]['hit_count']:
                return -1
            elif hit_info_x[0]['hit_count'] < hit_info_y[0]['hit_count']:
                return 1
            else:
                if hit_info_x[0]['last_hit_time'] > hit_info_y[0]['last_hit_time']:
                    return -1
                elif hit_info_x[0]['last_hit_time'] < hit_info_y[0]['last_hit_time']:
                    return 1
                else:
                    return 0

    @staticmethod
    def _hit_info_sorted_compare_by_hit_time(hit_info_x, hit_info_y):
        return BaseCache._hit_info_sorted_compare(hit_info_x, hit_info_y, EnumCacheSortedOrder.HitTimeFirst)

    @staticmethod
    def _hit_info_sorted_compare_by_hit_count(hit_info_x, hit_info_y):
        return BaseCache._hit_info_sorted_compare(hit_info_x, hit_info_y, EnumCacheSortedOrder.HitCountFirst)

    def _get_keys_sorted(self):
        """
        @fun 获取排好序的key列表
        @funName _get_keys_sorted
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funReturn {list} 排好序的缓存唯一标识列表

        """
        _sort_list = [(v, k) for k, v in self._cache_hit_info.items()]
        # 排序
        if self._sortedorder == EnumCacheSortedOrder.HitTimeFirst:
            _sort_list.sort(key=functools.cmp_to_key(BaseCache._hit_info_sorted_compare_by_hit_time))
        else:
            _sort_list.sort(key=functools.cmp_to_key(BaseCache._hit_info_sorted_compare_by_hit_count))
        # 返回key列表
        return [k[1] for k in _sort_list]

    def _check_size_and_cut(self):
        """
        @fun 检查缓存列表是否超过指定大小，如果超过则按优先级从后删除缓存
        @funName _check_size_and_cut
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        """
        if self._cache_size <= 0:
            return

        _key_list = self._get_keys_sorted()
        _len = len(_key_list)
        while _len - self._cache_size > 0:
            self.del_cache(_key_list[_len - 1])
            _len -= 1

    #############################
    # 公共处理函数
    #############################

    def clear(self):
        """
        @fun 清除所有缓存
        @funName clear
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        """
        # 先清除数据，再清除其他
        self._clear_cache_data()
        self._cache_change_lock.acquire()
        try:
            self._cache_hit_info.clear()
            self._cache_data.clear()
        finally:
            self._cache_change_lock.release()

    def get_cache(self, key):
        """
        @fun 获取指定key的缓存数据
        @funName get_cache
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识

        @funReturn {object} 具体缓存data，返回None代表没有缓存

        """
        _value = None
        self._cache_change_lock.acquire()
        try:
            if key not in self._cache_data.keys():
                return None
            _value = self._cache_data[key]
        finally:
            self._cache_change_lock.release()

        _data = self._get_cache_data(key=key, value=_value)

        self._cache_change_lock.acquire()
        try:
            if _data is None:
                # 说明该数据已经被清理掉了，清理掉内存信息
                if key in self._cache_data.keys():
                    del self._cache_data[key]
                if key in self._cache_hit_info.keys():
                    del self._cache_hit_info[key]
            else:
                # 更新命中信息
                if key in self._cache_hit_info.keys():
                    self._cache_hit_info[key]['last_hit_time'] = datetime.now()
                    self._cache_hit_info[key]['hit_count'] = self._cache_hit_info[key]['hit_count'] + 1
        finally:
            self._cache_change_lock.release()
        return _data

    def update_cache(self, key, data):
        """
        @fun 更新缓存数据
        @funName update_cache
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识
        @funParam {object} data 要更新的缓存数据

        """
        _value = None
        self._cache_change_lock.acquire()
        try:
            if key in self._cache_data.keys():
                _value = self._cache_data[key]
        finally:
            self._cache_change_lock.release()

        # 先存入缓存数据
        _ret_value = self._update_cache_data(key=key, value=_value, data=data)

        # 更新数据
        self._cache_change_lock.acquire()
        try:
            self._cache_data[key] = _ret_value
            if key in self._cache_hit_info.keys():
                self._cache_hit_info[key]['last_hit_time'] = datetime.now()
                self._cache_hit_info[key]['hit_count'] = self._cache_hit_info[key]['hit_count'] + 1
            else:
                self._cache_hit_info[key] = {
                    'last_hit_time': datetime.now(),
                    'hit_count': 1
                }
        finally:
            self._cache_change_lock.release()

        # 检查是否超过大小限制
        self._check_size_and_cut()

    def del_cache(self, key):
        """
        @fun 删除指定缓存
        @funName del_cache
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识

        """
        _value = None
        self._cache_change_lock.acquire()
        try:
            if key in self._cache_data.keys():
                _value = self._cache_data[key]
            else:
                # 不存在缓存
                return
        finally:
            self._cache_change_lock.release()

        # 执行数据删除
        self._del_cache_data(key=key, value=_value)

        # 删除索引
        self._cache_change_lock.acquire()
        try:
            if key in self._cache_data.keys():
                del self._cache_data[key]
            if key in self._cache_hit_info.keys():
                del self._cache_hit_info[key]
        finally:
            self._cache_change_lock.release()

    def get_cache_keys(self):
        """
        @fun 返回缓存唯一标识列表
        @funName get_cache_keys
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funReturn {list} 已按优先级排好序的key列表

        """
        return self._get_keys_sorted()

    #############################
    # 需继承类实现的内部处理函数
    #############################

    @abstractmethod
    def _clear_cache_data(self):
        """
        @fun 清除缓存所有实际数据
        @funName _clear_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 该函数应实现清除所有缓存数据的操作（注意非_cache_data字典中的value，但可以根据该value遍历）

        """
        pass

    @abstractmethod
    def _get_cache_data(self, key, value):
        """
        @fun 获取指定缓存数据
        @funName _get_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识
        @funParam {object} value _cache_data字典中的value(可能是真实数据的索引)

        @funReturn {返回值类型} 具体缓存data，返回None代表没有缓存

        """
        pass

    @abstractmethod
    def _update_cache_data(self, key, value, data):
        """
        @fun 更新缓存数据
        @funName _update_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识
        @funParam {object} value _cache_data字典中的value(如果原来已有数据)
        @funParam {object} data 要更新的缓存数据

        @funReturn {object} 更新完成后需同步到_cache_data字典中value

        """
        pass

    @abstractmethod
    def _del_cache_data(self, key, value):
        """
        @fun 删除指定缓存数据
        @funName _del_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识
        @funParam {object} value _cache_data字典中的value

        """
        pass


class MemoryCache(BaseCache):
    """
    @class 内存缓存
    @className
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 直接继承原生BaseCache定义的方法，通过_cache_data直接存储数据

    """

    #############################
    # 需继承类实现的内部处理函数
    #############################

    def _clear_cache_data(self):
        """
        @fun 清除缓存所有实际数据
        @funName _clear_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 不涉及另行存储数据，无需处理

        """
        return

    def _get_cache_data(self, key, value):
        """
        @fun 获取指定缓存数据
        @funName _get_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识
        @funParam {object} value _cache_data字典中的value(可能是真实数据的索引)

        @funReturn {object} 具体缓存data，直接返回传入的value

        """
        return value

    def _update_cache_data(self, key, value, data):
        """
        @fun 更新缓存数据
        @funName _update_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识
        @funParam {object} value _cache_data字典中的value(如果原来已有数据)
        @funParam {object} data 要更新的缓存数据

        @funReturn {object} 更新完成后需同步到_cache_data字典中value，直接返回传入的data

        """
        return data

    def _del_cache_data(self, key, value):
        """
        @fun 删除指定缓存数据
        @funName _del_cache_data
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 不涉及另行存储数据，无需处理
        @funExcepiton:
            异常类名 异常说明

        @funParam {string} key 缓存唯一标识
        @funParam {object} value _cache_data字典中的value

        """
        return


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))


