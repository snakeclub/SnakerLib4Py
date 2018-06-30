#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : formula.py


import copy
import datetime
from operator import itemgetter
from enum import Enum
from simple_stream import StringStream
from generic import NullObj, DebugTools, StringTools


__MoudleName__ = 'formula'
__MoudleDesc__ = '公式解析处理工具'
__Version__ = '0.0.1'
__Author__ = 'snaker'
__Time__ = '2018/1/26'


class EnumFormulaSearchSortOrder(Enum):
    """
    @enum 检索结果排序模式
    @enumName EnumSearchSortOrder
    @enumDescription 检索结果排序模式

    """
    ListAsc = 'ListAsc'  # 按匹配清单顺序
    ListDesc = 'ListDesc'  # 按匹配清单降序
    MatchBig = 'MatchBig'  # 按最大匹配顺序
    MatchSmall = 'MatchSmall'  # 按最小匹配顺序
    MatchAsc = 'MatchAsc'  # 按匹配先后顺序（先遇到优先，同时遇到则先结束优先），顺序
    MatchDesc = 'MatchDesc'  # 按匹配先后顺序（先遇到优先，同时遇到则先结束优先），倒序


class EnumFormulaSearchResultType(Enum):
    """
    @enum 检索结果类型
    @enumName EnumFormulaSearchResultType
    @enumDescription 检索结果类型

    """
    Dict = 'Dict'  # 按匹配字符串索引的字典形式
    List = 'List'  # 按匹配顺序排序的数组形式


class StructFormulaKeywordPara(object):
    """
    @class 公式匹配关键字配置参数结构
    @className StructFormulaKeywordPara
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 类功能描述

    """

    is_single_tag = False  # 该标签是否单独一个标识，不含公式内容
    has_sub_formula = True  # 是否包含子公式，如果为True则代表继续分解公式里面的子公式
    is_string = False  # 是否字符串，如果为True代表是字符串（字符串不包含子公式）
    string_ignore_chars = list()  # 字符串的结束标签忽略字符，例如["\\'", "''"]
    # 当结束标签为None时，且不是单独标签，通过该参数获取结束标识（可以为多个字符）
    # \$ : 以结尾为结束标签'\\$'
    # \t : 以下一个标签开始为当前结束标签'\\t'，注意不是代表tab的'\t'
    end_tags = list()


class StructFormula(object):
    """
    @class 公式结构
    @className StructFormula
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 定义公式的结构

    """

    formula_string = ''  # 公式完整字符串
    keyword = ''  # 公式的关键字标识
    content_string = ''  # 公式内容字符串
    sub_formula_list = list()  # 子公式对象列表（StructFormula数组）
    formula_value = ''  # 公式计算值字符串
    start_pos = 0  # 公式在原字符串中的开始位置
    end_pos = 0  # 公式在原字符串中的结束位置
    content_start_pos = 0  # 公式内容开始位置
    content_end_pos = 0  # 公式内容结束位置


class FormulaTool(object):
    """
    @class 公式解析处理工具
    @className FormulaTool
    @classGroup 所属分组
    @classVersion 1.0.0
    @classDescription 公式解析处理工具

    @classExample {Python} 示例名:
        类使用参考示例

    """

    #############################
    # 内部函数
    #############################

    # TODO(lhj): 可将字符串拆分为多个字符串段进行比较，然后合并比较结果，以支持多线程方式处理，利用CPU性能提高匹配速度
    @staticmethod
    def __search_all(source_str, match_list, ignore_case=False):
        """
        @fun 内部函数，从字符串中检索匹配字符清单，并返回所有结果
        @funName __search_all
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 从字符串中检索匹配字符清单，并返回所有结果，算法：
            1、总体算法思路是建立待匹配堆栈，只是登记匹配字符和已匹配到的位置；堆栈保持不动，将检索字符串逐个字符流转入
                堆栈中比对，匹配上则更新堆栈位置信息和增加部分匹配清单；完全匹配情况插入结果信息；
            2、待匹配堆栈内容如下：
                （1）固定匹配清单，在堆栈中固定保留，每次匹配都只匹配第一个字符
                （2）部分匹配清单，当固定匹配清单匹配上的时候新增待匹配清单，后续匹配中发现不匹配的时候移出清单；
                    每次匹配字符如果通过登记匹配字符位置，不通过移出清单，完全通过登记结果并移出清单。

        @funParam {string} source_str 需要检索的字符串
        @funParam {dict} match_list 要检索的匹配字符清单字典，格式为：
            key - string, 要匹配的字符串
            value - (string[], string[]) 前置字符列表，后置字符列表（可以一次设置多个前置字符匹配）:
                注意：前置字符和后置字符都只支持1个字符，当有两个字符时必须满足一下转义的定义：
                    \^ : 匹配字符串开头
                    \$ : 匹配字符串结尾
                    \* : 匹配任意字符（也可以是前面无字符）
        @funParam {bool} ignore_case 是否忽略大小写

        @funReturn {dict} 匹配结果字典，格式为:
            key - string, 匹配上的字符串（match_list的key）
            value - dict, 匹配到的结果字典，key为start_pos,value为一个object:
                object.source_str : string 匹配到的原文字符串
                object.start_pos : int 匹配结果开始位置（不含前置字符）
                object.end_pos : int 匹配结果结束位置（不含后置字符）
                object.front_char : string 匹配到的前置字符
                object.end_char : string 匹配到的后置字符

        """
        _match_result = dict()  # 最终的匹配结果
        # 初始化匹配堆栈，匹配\^的情况
        _compare_stack = dict()
        for _key in match_list.keys():
            if '\\^' in match_list[_key][0]:
                # 有匹配开头，添加进去
                FormulaTool.__add_compare_stack(compare_stack=_compare_stack, match_str=_key,
                                                start_pos=0, front_char='\\^', match_pos=0)

        # 执行流处理
        # DebugTools.debug_print(_compare_stack=_compare_stack)
        FormulaTool.__match_stream_dealer(deal_obj=None, position=0, str_obj=source_str, match_list=match_list,
                                          compare_stack=_compare_stack, match_result=_match_result,
                                          ignore_case=ignore_case)

        # 完成流处理，根据待匹配堆栈，匹配转义的结束字符\$
        _end_pos = len(source_str)
        for _match_str in _compare_stack.keys():
            for _key in _compare_stack[_match_str].keys():
                _match_info = _compare_stack[_match_str][_key]
                if _match_info.match_pos == len(_match_str):
                    # 前面都匹配上，只需要判断后置字符
                    _end_char = ''
                    _match_flag = False
                    if len(match_list[_match_str][1]) == 0:
                        _match_flag = True
                    elif '\\$' in match_list[_match_str][1]:
                        _match_flag = True
                        _end_char = '\\$'
                    elif '\\*' in match_list[_match_str][1]:
                        _match_flag = True
                        _end_char = '\\*'
                    # 处理匹配上的
                    if _match_flag:
                        _match_info.end_char = _end_char
                        _match_info.end_pos = _end_pos
                        FormulaTool.__add_match_result(match_result=_match_result, source_str=source_str,
                                                       match_str=_match_str, match_info=_match_info)

        return _match_result

    @staticmethod
    def __add_compare_stack(compare_stack, match_str, start_pos, front_char, match_pos):
        """
        @fun 将新匹配到第1个字符的对象放入待匹配堆栈
        @funName __add_compare_stack
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        """
        if match_str not in compare_stack.keys():
            # 构建新的堆栈key
            compare_stack[match_str] = dict()
        # 添加匹配上的信息，以front_char+pos为key
        _match_info = NullObj()
        _match_info.front_char = front_char
        _match_info.start_pos = start_pos
        _match_info.match_pos = match_pos
        _match_info.end_char = ''
        _match_info.end_pos = -1
        compare_stack[match_str][front_char+str(start_pos)] = _match_info

    @staticmethod
    def __del_compare_stack(compare_stack, match_str, start_pos, front_char):
        """
        @fun 删除待匹配堆栈的匹配记录
        @funName __del_compare_stack
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        """
        if match_str in compare_stack.keys():
            _key = front_char+str(start_pos)
            if _key in compare_stack[match_str].keys():
                del compare_stack[match_str][_key]

    @staticmethod
    def __add_match_result(match_result, source_str, match_str, match_info):
        """
        @fun 将匹配信息放入匹配结果
        @funName __add_match_result
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        """
        if match_str not in match_result.keys():
            match_result[match_str] = dict()
        _result_info = NullObj()
        _result_info.start_pos = match_info.start_pos  # 匹配结果开始位置（不含前置字符）
        _result_info.end_pos = match_info.end_pos  # 匹配结果结束位置（不含后置字符）
        _result_info.source_str = source_str[_result_info.start_pos: _result_info.end_pos]  # 匹配到的原文字符串
        _result_info.front_char = match_info.front_char  # 匹配到的前置字符
        _result_info.end_char = match_info.end_char  # 匹配到的后置字符
        match_result[match_str][_result_info.start_pos] = _result_info

    @staticmethod
    def __compare_char(deal_char='', match_char_list=list(), ignore_case=False):
        """
        @fun 字符比较内部函数
        @funName __compare_char
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 封装公共的字符比较函数

        @funParam {char} deal_char 传入的待比较字符
        @funParam {list} match_char_list 需要比较的字符数组
        @funParam {bool} ignore_case 是否忽略大小写

        @funReturn {string} 匹配到的字符

        """
        for _char in match_char_list:
            if not ignore_case and deal_char == _char:
                return _char
            elif ignore_case and deal_char.upper() == _char.upper():
                return _char

        # 没有一个匹配上
        return ''

    @staticmethod
    @StringStream.stream_decorator(is_sync=True)
    def __match_stream_dealer(deal_obj=None, position=0, str_obj='', match_list=dict(), compare_stack=dict(),
                              match_result=dict(), ignore_case=False):
        """
        @fun 逐个字符匹配处理的流函数定义
        @funName __match_stream_dealer
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        """
        # 先遍历堆栈中的待匹配字符，如果匹配不上则删除对应的记录
        for _match_str in compare_stack.keys():
            _compare_stack_keys = list(compare_stack[_match_str].keys())  # 复制key列表便于直接删除对象
            for _key in _compare_stack_keys:
                # 进入堆栈的都是前置字符已经通过的，可以直接进行按照match_pos的位置匹配处理
                _match_info = compare_stack[_match_str][_key]
                # DebugTools.debug_print(_match_info=_match_info)
                if _match_info.match_pos >= len(_match_str):
                    # 已经匹配到字符结尾（看是否有后置字符的比较）
                    _end_char = ''
                    _match_flag = False
                    if len(match_list[_match_str][1]) == 0:
                        _match_flag = True
                    elif '\\*' in match_list[_match_str][1]:
                        _end_char = '\\*'
                        _match_flag = True
                    else:
                        _end_char = FormulaTool.__compare_char(
                            deal_char=deal_obj, match_char_list=match_list[_match_str][1],
                            ignore_case=ignore_case)
                        if len(_end_char) > 0:
                            _match_flag = True

                    # 处理匹配结果
                    if _match_flag:
                        _match_info.end_char = _end_char
                        _match_info.end_pos = position
                        # 添加到匹配结果
                        FormulaTool.__add_match_result(match_result=match_result, source_str=str_obj,
                                                       match_str=_match_str, match_info=_match_info)

                    # 无论是否匹配上，都从待匹配清单删除
                    compare_stack[_match_str].pop(_key)
                else:
                    # 正常的匹配
                    _match_char = _match_str[_match_info.match_pos: _match_info.match_pos + 1]
                    _match_info.match_pos = _match_info.match_pos + 1  # 向下一个位置移动
                    if len(FormulaTool.__compare_char(
                            deal_char=deal_obj, match_char_list=[_match_char],
                            ignore_case=ignore_case)) == 0:
                        # 匹配不上，从堆栈中删除
                        compare_stack[_match_str].pop(_key)

        # 检索匹配清单，看是否要加入新的待匹配堆栈
        for _match_str in match_list.keys():
            _front_char = ''
            _start_pos = position
            _match_pos = 0
            _match_flag = False
            if '\\*' in match_list[_match_str][0]:
                # 前置字符匹配任意字符都可以
                _front_char = '\\*'
            if ((len(match_list[_match_str][0]) == 0 or '\\*' in match_list[_match_str][0])
                and len(FormulaTool.__compare_char(
                    deal_char=deal_obj, match_char_list=[_match_str[0: 1]],
                    ignore_case=ignore_case)) > 0):
                # 没有前置字符,或前置字符为通用匹配符，进行第1个字符的匹配且匹配上
                _match_pos = 1  # 因为已经匹配了第1个字符，因此位置要加1
                _match_flag = True
            elif len(match_list[_match_str][0]) > 0:
                _front_char = FormulaTool.__compare_char(deal_char=deal_obj,
                                                         match_char_list=match_list[_match_str][0],
                                                         ignore_case=ignore_case)
                if len(_front_char) > 0:
                    # 匹配上前置字符
                    _start_pos = position + 1  # 因为只是匹配前置，因此开始位置要加1
                    _match_flag = True

            # 添加待匹配堆栈
            if _match_flag:
                FormulaTool.__add_compare_stack(compare_stack=compare_stack, match_str=_match_str,
                                                start_pos=_start_pos, front_char=_front_char, match_pos=_match_pos)

    @staticmethod
    def __sorted_by_match_info(match_info_x, match_info_y, match_list, sort_oder=EnumFormulaSearchSortOrder.ListAsc):
        """
        @fun 对匹配信息进行比较排序
        @funName __sorted_by_match_info
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {list} _match_info_x 比较信息x，格式为:
            [match_str, source_str, start_pos, end_pos, front_char, end_char]
        @funParam {list} _match_info_y 比较信息y，格式为:
            [match_str, source_str, start_pos, end_pos, front_char, end_char]
        @funParam {dict} match_list 匹配参数
        @funParam {EnumFormulaSearchSortOrder} sort_oder 匹配结果排序顺序

        @funReturn {int} 比较结果：
            0 : 相等
            -1 : x 排在前面
            1 : y排在前面

        """
        _order_result = 0
        if sort_oder in (EnumFormulaSearchSortOrder.ListAsc, EnumFormulaSearchSortOrder.ListDesc):
            # 按照匹配清单的顺序
            _list = list(match_list.keys())
            _x_index = _list.index(match_info_x[0])
            _y_index = _list.index(match_info_y[0])
            if _x_index < _y_index:
                _order_result = -1
            elif _x_index > _y_index:
                _order_result = 1
            # 如果是反方向
            if sort_oder == EnumFormulaSearchSortOrder.ListDesc:
                _order_result = 0 - _order_result
        elif sort_oder in (EnumFormulaSearchSortOrder.MatchBig, EnumFormulaSearchSortOrder.MatchSmall):
            # 按照匹配度大小
            if len(match_info_x[0]) > len(match_info_y[0]):
                _order_result = -1
            elif len(match_info_x[0]) < len(match_info_y[0]):
                _order_result = 1
            # 如果是反方向
            if sort_oder == EnumFormulaSearchSortOrder.MatchSmall:
                _order_result = 0 - _order_result
        else:
            # 按照匹配顺序
            if match_info_x[2] < match_info_y[2]:
                _order_result = -1
            elif match_info_x[2] > match_info_y[2]:
                _order_result = 1
            else:
                # 开始位置一样
                if match_info_x[3] < match_info_y[3]:
                    _order_result = -1
                elif match_info_x[3] > match_info_y[3]:
                    _order_result = 1
            # 如果是反方向
            if sort_oder == EnumFormulaSearchSortOrder.MatchDesc:
                _order_result = 0 - _order_result
        return _order_result

    @staticmethod
    def __add_match_list(match_list, match_str, front_chars=list(), end_chars=list()):
        """
        @fun 将匹配参数添加到匹配列表
        @funName __add_match_list
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 函数需判断重复，若重复则不添加

        @funParam {dict} match_list 要处理的匹配参数字典
        @funParam {string} match_str 匹配字符串
        @funParam {list} front_chars 前置字符列表
        @funParam {list} end_chars 后置字符列表

        """
        if match_str not in match_list.keys():
            # 直接加入
            match_list[match_str] = (front_chars, end_chars)
        else:
            # 原来已存在，合并前置和后置列表，注意需要判断空的情况
            _front_chars = match_list[match_str][0]
            _end_chars = match_list[match_str][1]
            if front_chars is None or len(front_chars) == 0:
                _front_chars.append('\\*')  # 任意匹配
            else:
                _front_chars.extend(front_chars)  # 扩展

            if end_chars is None or len(end_chars) == 0:
                _end_chars.append('\\*')  # 任意匹配
            else:
                _end_chars.extend(end_chars)  # 扩展

            # 去除重复项
            match_list[match_str] = (list(set(_front_chars)), list(set(_end_chars)))

    @staticmethod
    def __keywords_to_match_list(keywords):
        """
        @fun 将公式的keywords对象转为字符匹配参数列表
        @funName __keywords_to_match_list
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {dict} keywords 公式关键字定义

        @funReturn {dict} match_list 要检索的匹配字符清单字典，格式为：
            key - string, 要匹配的字符串
            value - (string[], string[]) 前置字符列表，后置字符列表（可以一次设置多个前置字符匹配）:

        """
        _match_list = dict()
        for _key in keywords:
            _item = keywords[_key]
            # 开始标签
            FormulaTool.__add_match_list(match_list=_match_list, match_str=_item[0][0],
                                         front_chars=_item[0][1], end_chars=_item[0][2])
            # 结束标签
            if _item[1] is not None:
                FormulaTool.__add_match_list(match_list=_match_list, match_str=_item[1][0],
                                             front_chars=_item[1][1], end_chars=_item[1][2])
            elif not _item[2].is_single_tag:
                # 非单独标签且没有设置结束标签
                for _char in _item[2].end_tags:
                    if _char not in ('\\$', '\\t'):
                        FormulaTool.__add_match_list(match_list=_match_list, match_str=_char)

            # 字符串格式的忽略字符
            if _item[2].is_string:
                for _char in _item[2].string_ignore_chars:
                    FormulaTool.__add_match_list(match_list=_match_list, match_str=_char)

        # 返回处理结果
        return _match_list

    @staticmethod
    def __formula_analyse_loop(formula_str, keywords, match_result, current_index, parent_key):
        """
        @fun 循环解析公式
        @funName __formula_analyse_loop
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 算法描述：
            1、从current_index开始逐个从match_result找在keywords中定义的开始标签
            2、如果找到开始标签，则冒泡调用__formula_analyse_loop，在标签后找自身的子公式，直到遇到父公式的结束标签
        @funExcepiton:
            LookupError 如果公式存在错误（例如找不到结束标签等），抛出该异常

        @funParam {string} formula_str 公式完整字符串
        @funParam {dict} keywords 公式匹配参数
        @funParam {list} match_result 关键字匹配结果清单
        @funParam {int} current_index 关键字匹配搜索开始的索引位置
        @funParam {string} parent_key 父公式需匹配的关键字标识，如果是最外层会传None进来（一直匹配到结尾）

        @funReturn {list} [formula[], parent_key_end_index] :
            找到的公式列表, 父公式找到的结束标签位置，如果为None则代表找到结尾仍没有找到结束标签

        """
        _loop_result = [list(), None]  # 默认找不到，且到结尾返回
        _current_index = current_index
        _maxlen = len(match_result)
        while _current_index < _maxlen:
            # 格式：[match_str, source_str, start_pos, end_pos, front_char, end_char]
            _match_info = match_result[_current_index]
            # 判断是否父节点的结束
            if parent_key is not None:
                _key = FormulaTool.__is_match_keyword(match_info=_match_info, keywords=keywords, key=parent_key)
                if _key is not None:
                    # 找到父节点的结束标签，直接返回
                    _loop_result[1] = _current_index
                    return _loop_result

            # 找下一个开始标签
            _key = FormulaTool.__is_match_keyword(match_info=_match_info, keywords=keywords, key=None)
            if _key is None:
                # 不是关键字，移动到下一个
                _current_index = _current_index + 1
                continue
            else:
                # 匹配到开始标签
                _formula = StructFormula()
                _formula.keyword = _key
                _formula.start_pos = _match_info[2]
                _formula.content_start_pos = _match_info[3]

                if keywords[_key][2].is_single_tag:
                    # 是独立的标签
                    _formula.end_pos = _match_info[3]
                    _formula.formula_string = formula_str[_formula.start_pos: _formula.end_pos]
                    _formula.content_end_pos = _match_info[3]
                    _formula.content_string = ''
                    _loop_result[0].append(_formula)
                    # 继续找下一个，由于匹配上，要解决重叠问题
                    _current_index = FormulaTool.__move_next_result_index(
                        match_result=match_result,
                        current_index=_current_index
                    )
                    continue
                elif keywords[_key][2].is_string:
                    # 是字符串，先寻找到结束字符位置
                    _is_match_endkey = False
                    _current_index = FormulaTool.__move_next_result_index(
                        match_result=match_result,
                        current_index=_current_index
                    )
                    while _current_index < _maxlen:
                        _match_info = match_result[_current_index]
                        _endkey = FormulaTool.__is_match_keyword(match_info=_match_info, keywords=keywords, key=_key)
                        # DebugTools.debug_print(endkey=_endkey)
                        if _endkey is None:
                            # 没有匹配到结束字符，继续找下一个
                            _current_index = _current_index + 1
                            continue
                        # 找到结束标签，判断是否包含在忽略字符里面
                        if FormulaTool.__check_string_tag_ignore(
                                match_result=match_result, tag_index=_current_index,
                                string_ignore_chars=keywords[_key][2].string_ignore_chars):
                            # 在忽略列表中，继续找下一个
                            _current_index = _current_index + 1
                            continue
                        # 匹配上，退出子循环
                        _is_match_endkey = True
                        _formula.end_pos = _match_info[3]
                        _formula.formula_string = formula_str[_formula.start_pos: _formula.end_pos]
                        _formula.content_end_pos = _match_info[2]
                        _formula.content_string = formula_str[_formula.content_start_pos: _formula.content_end_pos]

                        _loop_result[0].append(_formula)
                        # 继续找下一个，由于匹配上，要解决重叠问题
                        _current_index = FormulaTool.__move_next_result_index(
                            match_result=match_result,
                            current_index=_current_index
                        )
                        break
                    # 退出到这里，要不已找到字符串结束，要不已到公式结尾，直接继续主循环即可
                    if _is_match_endkey:
                        continue
                    else:
                        # 没有匹配到结束，抛出异常
                        raise LookupError(u'未找到字符串公式%s[ %s ]的结束标记[ %s ]，开始位置: %s' % (
                            _key, keywords[_key][0][0], keywords[_key][1][0], str(_formula.start_pos)
                        ))
                elif not keywords[_key][2].has_sub_formula:
                    # 没有子公式的情况，直接找结束字符位置
                    _is_match_endkey = False
                    _current_index = FormulaTool.__move_next_result_index(
                        match_result=match_result,
                        current_index=_current_index
                    )
                    while _current_index < _maxlen:
                        _match_info = match_result[_current_index]
                        _endkey = FormulaTool.__is_match_keyword(match_info=_match_info, keywords=keywords, key=_key)
                        if _endkey is None:
                            # 没有匹配到结束字符，继续找下一个
                            _current_index = _current_index + 1
                            continue
                        # 找到结束标签，退出子循环
                        _is_match_endkey = True
                        _formula.end_pos = _match_info[3]
                        _formula.formula_string = formula_str[_formula.start_pos: _formula.end_pos]
                        _formula.content_end_pos = _match_info[2]
                        _formula.content_string = formula_str[_formula.content_start_pos: _formula.content_end_pos]
                        _loop_result[0].append(_formula)
                        # 继续找下一个，由于匹配上，要解决重叠问题
                        _current_index = FormulaTool.__move_next_result_index(
                            match_result=match_result,
                            current_index=_current_index
                        )
                        break
                    # 退出到这里，要不已找到结束标签，要不已到公式结尾，直接继续主循环即可
                    if _is_match_endkey:
                        continue
                    else:
                        # 没有匹配到结束，抛出异常
                        raise LookupError(u'未找到公式%s[ %s ]的结束标记[ %s ]，开始位置: %s' % (
                            _key, keywords[_key][0][0], keywords[_key][1][0], str(_formula.start_pos)
                        ))
                else:
                    # 匹配到一般标签，先跳到下一个位置
                    _current_index = FormulaTool.__move_next_result_index(
                        match_result=match_result,
                        current_index=_current_index
                    )
                    if keywords[_key][1] is None:
                        if '\\t' in keywords[_key][2].end_tags:
                            # 下一个标签开始就是本标签的结束
                            while _current_index < _maxlen:
                                _key = FormulaTool.__is_match_keyword(match_info=_match_info, keywords=keywords,
                                                                      key=None)
                                if _key is None:
                                    # 不是关键字，移动到下一个
                                    _current_index = _current_index + 1
                                    continue
                                else:
                                    # 匹配到下一个了，登记本标签结束，跳出循环，让主循环重新处理本节点
                                    _formula.end_pos = match_result[_current_index][2]
                                    _formula.formula_string = formula_str[_formula.start_pos: _formula.end_pos]
                                    _formula.content_end_pos = _formula.end_pos
                                    _formula.content_string = formula_str[
                                                              _formula.content_start_pos: _formula.content_end_pos]
                                    _loop_result[0].append(_formula)
                                    break
                            # 完成这个标签的处理，重新进行主循环，且从下一个标签开始位置开始处理
                            continue
                        elif '\\$' in keywords[_key][2].end_tags:
                            # 标签直接到字符结束
                            _key = None

                    # 正常情况，找子公式，含标签直接到字符结束的情况
                    _sub_formule_result = FormulaTool.__formula_analyse_loop(
                        formula_str=formula_str, keywords=keywords, match_result=match_result,
                        current_index=_current_index, parent_key=_key
                    )
                    _formula.sub_formula_list = _sub_formule_result[0]
                    if _sub_formule_result[1] is None:
                        _formula.end_pos = len(formula_str)
                        _formula.content_end_pos = _formula.end_pos
                    else:
                        _formula.end_pos = match_result[_sub_formule_result[1]][3]
                        _formula.content_end_pos = match_result[_sub_formule_result[1]][2]
                    _formula.formula_string = formula_str[_formula.start_pos: _formula.end_pos]
                    _formula.content_string = formula_str[_formula.content_start_pos: _formula.content_end_pos]
                    _loop_result[0].append(_formula)
                    if _sub_formule_result[1] is None:
                        # 判断是否匹配到父公式的结束标签，如果没有匹配到，抛出异常
                        if _key is not None:
                            if (
                                    keywords[_key][1] is not None
                                    or (
                                        '\\t' not in keywords[_key][1].end_tags
                                        and '\\$' not in keywords[_key][1].end_tags
                                    )
                            ):
                                # 必须有结束标签
                                raise LookupError(u'未找到公式%s[ %s ]的结束标记[ %s ]，开始位置: %s' % (
                                    _key, keywords[_key][0][0], keywords[_key][1][0], str(_formula.start_pos)
                                ))
                        return _loop_result
                    else:
                        # 调到下一个位置执行
                        _current_index = FormulaTool.__move_next_result_index(
                            match_result=match_result,
                            current_index=_sub_formule_result[1]
                        )
                        continue
        # 返回最终结果
        return _loop_result

    @staticmethod
    def __is_match_keyword(match_info, keywords, key=None):
        """
        @fun 检查匹配节点是否与keywords中的配置匹配
        @funName __is_match_keyword
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {list} match_info 匹配节点信息，[match_str, source_str, start_pos, end_pos, front_char, end_char]
        @funParam {dict} keywords 公式匹配参数
        @funParam {string} key 指定匹配的关键字标识，如果为None代表匹配开始标签，如果不为None代表匹配对应的结束标签

        @funReturn {string} 返回None代表没有匹配上，否直返回匹配上的关键字标签

        """
        if key is None:
            # 匹配开始标签
            for _key in keywords.keys():
                _begin_tag = keywords[_key]
                if match_info[0] == _begin_tag[0][0]:
                    # 匹配到关键字
                    return _key
        else:
            # 匹配结束标签
            _end_tag = keywords[key]
            if _end_tag[1] is None:
                # 没有特定的结束标签，通过参数判断
                if match_info[0] in _end_tag[2].end_tags:
                    return key
            else:
                # 匹配结束标签
                if match_info[0] == _end_tag[1][0]:
                    # 匹配到关键字
                    return key
        # 找不到对应的关键字
        return None

    @staticmethod
    def __move_next_result_index(match_result, current_index):
        """
        @fun 取得下一个有效的匹配节点位置（对于当前节点已匹配上的情况下，不能造成关键字重叠的情况）
        @funName __move_next_result_index
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funReturn {int} 下一个有效的可匹配位置，如果超过匹配清单大小，返回清单大小

        """
        _maxlen = len(match_result)
        _next_index = current_index + 1
        while _next_index < _maxlen:
            if match_result[_next_index][2] >= match_result[current_index][3]:
                return _next_index
            else:
                _next_index = _next_index + 1
        # 超过范围
        return _maxlen

    @staticmethod
    def __check_string_tag_ignore(match_result, tag_index, string_ignore_chars):
        """
        @fun 检查匹配到的字符串结束标签在忽略字符中
        @funName __check_string_tag_ignore
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 向前、向后找与标签有重叠冲突的匹配结果，看是否在忽略字符中

        @funReturn {bool} True-在忽略字符中，False-不在忽略字符中

        """
        # 判断忽略列表最大长度
        # DebugTools.debug_print(tag_index=tag_index, string_ignore_chars=string_ignore_chars)
        _max_char_len = 0
        for _item in string_ignore_chars:
            if len(_item) > _max_char_len:
                _max_char_len = len(_item)
        if _max_char_len < 2:
            # 忽略列表不存在或不合理
            return False

        _match_info = match_result[tag_index]
        _maxlen = len(match_result)

        # 先向前检索
        _current_index = tag_index - 1
        while _current_index >= 0:
            _cmp_info = match_result[_current_index]
            if _cmp_info[2] <= _match_info[2] - _max_char_len:
                # 超出相交范围，不再继续
                break
            if _cmp_info[2] <= _match_info[2] < _cmp_info[3]:
                # 有冲突，判断是否忽略列表中
                if _cmp_info[0] in string_ignore_chars:
                    # 在忽略列表中
                    return True
            # 继续向前
            _current_index = _current_index - 1
            continue

        # 再向后检索
        _current_index = tag_index + 1
        while _current_index < _maxlen:
            _cmp_info = match_result[_current_index]
            if _cmp_info[2] > _match_info[2]:
                # 匹配在后面，不再继续
                break
            if _cmp_info[2] <= _match_info[2]:
                # 有冲突，判断是否忽略列表中
                if _cmp_info[0] in string_ignore_chars:
                    # 在忽略列表中
                    return True
            # 继续向后
            _current_index = _current_index + 1
            continue

        # 没有匹配到忽略列表
        return False

    @staticmethod
    def __analyse_formula(formula_str, keywords=dict(), ignore_case=False, match_list=None):
        # 匹配清单，内部如果已传入则无需再转换，提高性能
        _match_list = match_list
        if _match_list is None:
            _match_list = FormulaTool.__keywords_to_match_list(keywords=keywords)

        # 获取关键字匹配结果，List格式
        _match_result = FormulaTool.search(source_str=formula_str, match_list=_match_list,
                                           ignore_case=ignore_case, multiple_match=True,
                                           result_type=EnumFormulaSearchResultType.List)

        # 循环遍历匹配结果，形成公式结果，先将整个字符串当主公式，处理结束的时候再更新其他信息
        _formula = StructFormula()
        _formula.formula_string = formula_str
        _formula.start_pos = 0
        _formula.end_pos = len(formula_str)
        _formula.content_string = formula_str
        _formula.content_start_pos = _formula.start_pos
        _formula.content_end_pos = _formula.end_pos
        _sub_formule_result = FormulaTool.__formula_analyse_loop(
            formula_str=formula_str, keywords=keywords, match_result=_match_result,
            current_index=0, parent_key=None
        )
        if (
                len(_sub_formule_result[0]) == 1
                and _sub_formule_result[0][0].start_pos == 0
                and _sub_formule_result[0][0].end_pos == len(formula_str)
        ):
            return _sub_formule_result[0][0]
        else:
            _formula.sub_formula_list = _sub_formule_result[0]
            return _formula

    #############################
    # 静态工具
    #############################

    @staticmethod
    def search(source_str, match_list, ignore_case=False,
               multiple_match=True, sort_oder=EnumFormulaSearchSortOrder.MatchAsc,
               result_type=EnumFormulaSearchResultType.Dict):
        """
        @fun 从字符串中检索匹配字符清单
        @funName search
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 从字符串中检索匹配字符清单，获取匹配结果

        @funParam {string} source_str 需要检索的字符串
        @funParam {dict} match_list 要检索的匹配字符清单字典，格式为：
            key - string, 要匹配的字符串
            value - (string[], string[]) 前置字符列表，后置字符列表（可以一次设置多个前置字符匹配）:
                前置字符/后置字符可以支持以下3个转义：'\\^'匹配开始；'\\$'匹配开始；'\\*'匹配任意字符（也可以匹配0字符）
                如果前置字符/后置字符列表长度为0，则代表不判断前置及后置字符，等同于'\\*'
        @funParam {bool} ignore_case 是否忽略大小写
        @funParam {bool} multiple_match 是否支持多重匹配（即同一段字符可以被多个匹配字符所匹配上）
        @funParam {EnumFormulaSearchSortOrder} sort_oder 匹配结果获取顺序，在不支持多重匹配的情况下按该顺序保留结果
        @funParam {EnumFormulaSearchResultType} result_type 匹配结果类型

        @funReturn {dict/list} 匹配结果，返回格式与result_type参数有关:
            字典格式为:
            key - string, 匹配上的字符串（match_list的key）
            value - dict, 匹配到的结果字典，key为start_pos,value为一个object:
                object.source_str : string 匹配到的原文字符串
                object.start_pos : int 匹配结果开始位置（不含前置字符）
                object.end_pos : int 匹配结果结束位置（不含后置字符）
                object.front_char : string 匹配到的前置字符
                object.end_char : string 匹配到的后置字符

            列表格式为：
            [
                [match_str, source_str, start_pos, end_pos, front_char, end_char],
                ……
            ]

        """
        _match_result = FormulaTool.__search_all(source_str=source_str, match_list=match_list, ignore_case=ignore_case)
        if not multiple_match:
            # 不允许多重匹配，检查冲突并按排序规则删除列表
            _result_list = FormulaTool.match_result_to_sorted_list(match_result=_match_result)
            _last_item = None
            for _item in _result_list:
                # 循环处理
                if _last_item is None:
                    # 第一个
                    _last_item = _item
                    continue
                # 检查有没有冲突
                if ((_last_item[2] <= _item[2] < _last_item[3]) or (_last_item[2] < _item[3] <= _last_item[3])):
                    _compare_result = FormulaTool.__sorted_by_match_info(_last_item, _item,
                                                                         match_list=match_list, sort_oder=sort_oder)
                    if _compare_result <= 0:
                        # 删除后面一个
                        del _match_result[_item[0]][_item[2]]
                    else:
                        # 删除前面一个
                        del _match_result[_last_item[0]][_last_item[2]]
                        _last_item = _item  # 将当前对象变成上一个
                else:
                    # 没有冲突，更新上一个匹配对象
                    _last_item = _item

        if result_type == EnumFormulaSearchResultType.Dict:
            return _match_result
        else:
            return FormulaTool.match_result_to_sorted_list(match_result=_match_result)

    @staticmethod
    def match_result_to_sorted_list(match_result):
        """
        @fun 将匹配结果转换未按匹配位置排序的数组
        @funName match_result_to_sorted_list
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {dict} match_result 字符匹配结果字典

        @funReturn {list} 按匹配位置排序好的数组，格式为：
            [
                [match_str, source_str, start_pos, end_pos, front_char, end_char],
                ……
            ]

        """
        _sorted_list = list()
        for _match_str in match_result.keys():
            for _key in match_result[_match_str].keys():
                _match_info = match_result[_match_str][_key]
                _sorted_list.append([
                    _match_str,
                    _match_info.source_str,
                    _match_info.start_pos,
                    _match_info.end_pos,
                    _match_info.front_char,
                    _match_info.end_char
                ])

        # 进行排序
        _sorted_list.sort(key=itemgetter(2, 3))  # 按照第3、4个对象排序
        return _sorted_list

    @staticmethod
    def analyse_formula(formula_str, keywords=dict(), ignore_case=False):
        """
        @fun 解析公式并形成结构化展示字典
        @funName analyse_formula
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            LookupError 如果公式存在错误（例如找不到结束标签等），抛出该异常

        @funParam {string} formula_str 要解析的公式字符串
        @funParam {dict} keywords 公式关键字定义，格式如下：
            key - string 关键字标识名
            value - list 匹配定义数组，按顺序定义为:
                开始标签 - [string-匹配字符串, list-前置字符, list-后置字符]
                结束标签 - [string-匹配字符串, list-前置字符, list-后置字符]，结束标签可以置None（表示使用匹配参数）
                匹配参数 - StructFormulaKeywordPara, 对象属性为：
                    object.is_single_tag : bool 该标签是否单独一个标识，不含公式内容
                    object.has_sub_formula : bool 是否包含子公式，如果为True则代表继续分解公式里面的子公式
                    object.is_string : bool 是否字符串，如果为True代表是字符串（字符串不包含子公式）
                    object.string_ignore_chars : list 字符串的结束标签忽略字符，例如["\\'", "''"]
                    object.end_tags : list 当结束标签为None时，且不是单独标签，通过该参数获取结束标识（可以为多个字符）:
                        \$ : 以结尾为结束标签'\\$'
                        \t : 以下一个标签开始为当前结束标签'\\t'，注意不是代表tab的'\t'
        @funParam {bool} ignore_case 是否忽略大小写

        @funReturn {StructFormula} 公式分解结构对象

        """
        return FormulaTool.__analyse_formula(
            formula_str=formula_str, keywords=keywords, ignore_case=ignore_case, match_list=None
        )

    #############################
    # 实例处理 - 私有对象
    #############################

    _keywords = dict()  # 公式关键字定义
    _match_list = dict()  # 要检索的匹配字符清单字典(预先生成提高性能)
    _ignore_case = False  # 是否忽略大小写
    _deal_fun_list = dict() # 公式计算函数对照字典
    _default_deal_fun = None  # 默认的公式处理函数

    #############################
    # 实例处理 - 内部函数
    #############################

    def __run_formula(self,formular_obj, **kwargs):
        """
        @fun 进行公式对象的计算
        @funName __run_formula
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 循环调用自己进行公式对象的计算

        """
        # 先调用自己处理子公式
        for _sub_formular_obj in formular_obj.sub_formula_list:
            self.__run_formula(formular_obj=_sub_formular_obj, **kwargs)

        # 计算自身
        if formular_obj.keyword in self._deal_fun_list.keys():
            self._deal_fun_list[formular_obj.keyword](formular_obj, **kwargs)
        else:
            self._default_deal_fun(formular_obj, **kwargs)

    def __run_formula_as_string(self,formular_obj, **kwargs):
        """
        @fun 以字符串替换方式解析并执行公式计算
        @funName __run_formula
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 循环调用自己进行公式对象的计算,所有公式最终计算为字符串并替换父公司的对应内容

        """
        _content_string_bak = formular_obj.content_string

        # 先调用自己处理子公式
        for _sub_formular_obj in formular_obj.sub_formula_list:
            self.__run_formula_as_string(formular_obj=_sub_formular_obj, **kwargs)
            # 执行字符串替换
            formular_obj.content_string = formular_obj.content_string.replace(_sub_formular_obj.formula_string, str(_sub_formular_obj.formula_value))


        # 计算自身
        if formular_obj.keyword in self._deal_fun_list.keys():
            self._deal_fun_list[formular_obj.keyword](formular_obj, **kwargs)
        else:
            self._default_deal_fun(formular_obj, **kwargs)
        formular_obj.content_string = _content_string_bak
        formular_obj.formula_value = str(formular_obj.formula_value)

    #############################
    # 实例处理 - 内置的公式处理函数
    #############################

    @staticmethod
    def default_deal_fun_string_full(formular_obj, **kwargs):
        """
        @fun 默认公式计算函数-全标签转为字符串
        @funName default_deal_fun_full_string
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 将标签自身的字符串作为设置值

        @funParam {StructFormula} formular_obj 要计算的公式

        """
        formular_obj.formula_value = formular_obj.formula_string

    @staticmethod
    def default_deal_fun_string_content(formular_obj, **kwargs):
        """
        @fun 默认公式计算函数-标签内容转为字符串
        @funName default_deal_fun_string_content
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 将标签内容的字符串作为设置值

        @funParam {StructFormula} formular_obj 要计算的公式

        """
        formular_obj.formula_value = formular_obj.content_string

    @staticmethod
    def default_deal_fun_python(formular_obj, **kwargs):
        """
        @fun 默认公式计算函数-标签内容作为python代码执行
        @funName default_deal_fun_python
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 将执行结果的对象作为设置值

        @funParam {StructFormula} formular_obj 要计算的公式

        """
        formular_obj.formula_value = eval(formular_obj.content_string)

    @staticmethod
    def default_deal_fun_datetime_str(formular_obj, datetime_format_str='%Y-%m-%d %H:%M:%S', **kwargs):
        """
        @fun 默认公式计算函数-获取当前时间日期字符格式
        @funName default_deal_fun_datetime_str
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {StructFormula} formular_obj 要计算的公式
        @funParam {string} datetime_format_str 日期时间的格式化字符串
            参考：
            %y 两位数的年份表示（00-99）
            %Y 四位数的年份表示（000-9999）
            %m 月份（01-12）
            %d 月内中的一天（0-31）
            %H 24小时制小时数（0-23）
            %I 12小时制小时数（01-12）
            %M 分钟数（00=59）
            %S 秒（00-59）
            %a 本地简化星期名称
            %A 本地完整星期名称
            %b 本地简化的月份名称
            %B 本地完整的月份名称
            %c 本地相应的日期表示和时间表示
            %j 年内的一天（001-366）
            %p 本地A.M.或P.M.的等价符
            %U 一年中的星期数（00-53）星期天为星期的开始
            %w 星期（0-6），星期天为星期的开始
            %W 一年中的星期数（00-53）星期一为星期的开始
            %x 本地相应的日期表示
            %X 本地相应的时间表示
            %Z 当前时区的名称
            %% %号本身

        """
        formular_obj.formula_value = datetime.datetime.now().strftime(datetime_format_str)

    #############################
    # 实例处理 - 公共函数
    #############################

    def __init__(self, keywords=dict(), ignore_case=False, deal_fun_list=dict(), default_deal_fun=None):
        """
        @fun 构造函数
        @funName __init__
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述

        @funParam {dict} keywords 公式关键字定义，格式如下：
            key - string 关键字标识名
            value - list 匹配定义数组，按顺序定义为:
                开始标签 - [string-匹配字符串, list-前置字符, list-后置字符]
                结束标签 - [string-匹配字符串, list-前置字符, list-后置字符]，结束标签可以置None（表示使用匹配参数）
                匹配参数 - StructFormulaKeywordPara, 对象属性为：
                    object.is_single_tag : bool 该标签是否单独一个标识，不含公式内容
                    object.has_sub_formula : bool 是否包含子公式，如果为True则代表继续分解公式里面的子公式
                    object.is_string : bool 是否字符串，如果为True代表是字符串（字符串不包含子公式）
                    object.string_ignore_chars : list 字符串的结束标签忽略字符，例如["\\'", "''"]
                    object.end_tags : list 当结束标签为None时，且不是单独标签，通过该参数获取结束标识（可以为多个字符）:
                        \$ : 以结尾为结束标签'\\$'
                        \t : 以下一个标签开始为当前结束标签'\\t'，注意不是代表tab的'\t'
        @funParam {bool} ignore_case 是否忽略大小写
        @funParam {dict} deal_fun_list 公式计算函数对照字典:
            key - string keywords的关键字标识名
            value - fun 对应的公式处理函数，函数的定义必须满足以下要求:
                fun(formular_obj, **kwargs):
                    formular_obj : StructFormula 要处理公式对象（函数直接修改对象），该函数需更新对象的formula_value
                    kwargs ：计算公式所传入的key=value格式的参数，参数key由处理函数定义（建议统一定义便于简化处理）
                注意：
                    1、可以在函数定义中直接指定要传入的指定参数名，但注意函数参数的最后必须指定**kwargs，:
                        避免外部统一传入的参数与指定参数不一样的情况下出错，例如：
                        def deal_fun_string(formular_obj, my_para1='', my_para2=[], **kwargs)
                    2、如果希望传入的指定参数能在公式处理过程中被修改并传递到其他公式处理，应该指定的参数类型不要:
                        为string、int等非引用类型，而应该使用list、dict、object等引用类型
        @funParam {fun} default_deal_fun 默认的公式处理函数，如果None代表默认使用default_deal_fun_string_content

        """
        self.reset_formula_para(keywords=keywords, ignore_case=ignore_case,
                                deal_fun_list=deal_fun_list,default_deal_fun=default_deal_fun)

    def reset_formula_para(self, keywords=dict(), ignore_case=False, deal_fun_list=dict(), default_deal_fun=None):
        """
        @fun 重置公式处理参数
        @funName reset_formula_para
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 重置公式处理参数

        @funParam {dict} keywords 公式关键字定义，格式如下：
            key - string 关键字标识名
            value - list 匹配定义数组，按顺序定义为:
                开始标签 - [string-匹配字符串, list-前置字符, list-后置字符]
                结束标签 - [string-匹配字符串, list-前置字符, list-后置字符]，结束标签可以置None（表示使用匹配参数）
                匹配参数 - StructFormulaKeywordPara, 对象属性为：
                    object.is_single_tag : bool 该标签是否单独一个标识，不含公式内容
                    object.has_sub_formula : bool 是否包含子公式，如果为True则代表继续分解公式里面的子公式
                    object.is_string : bool 是否字符串，如果为True代表是字符串（字符串不包含子公式）
                    object.string_ignore_chars : list 字符串的结束标签忽略字符，例如["\\'", "''"]
                    object.end_tags : list 当结束标签为None时，且不是单独标签，通过该参数获取结束标识（可以为多个字符）:
                        \$ : 以结尾为结束标签'\\$'
                        \t : 以下一个标签开始为当前结束标签'\\t'，注意不是代表tab的'\t'
        @funParam {bool} ignore_case 是否忽略大小写
        @funParam {dict} deal_fun_list 公式计算函数对照字典:
            key - string keywords的关键字标识名
            value - fun 对应的公式处理函数，函数的定义必须满足以下要求:
                fun(formular_obj, **kwargs):
                    formular_obj : StructFormula 要处理公式对象（函数直接修改对象），该函数需更新对象的formula_value
                    kwargs ：计算公式所传入的key=value格式的参数，参数key由处理函数定义（建议统一定义便于简化处理）
        @funParam {fun} default_deal_fun 默认的公式处理函数，如果None代表默认使用default_deal_fun_string_content

        """
        self._keywords = keywords
        self._ignore_case = ignore_case
        self._deal_fun_list = deal_fun_list
        if default_deal_fun is None:
            self._default_deal_fun = self.default_deal_fun_string_content
        else:
            self._default_deal_fun = default_deal_fun
        # 计算match_list
        self._match_list = self.__keywords_to_match_list(self._keywords)

    def clear_keywords(self, with_deal_fun=False):
        """
        @fun 清除公式关键字定义
        @funName clear_keywords
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 清除公式关键字定义

        @funParam {bool} with_deal_fun 是否同步清除处理函数列表

        """
        self._keywords.clear()
        self._match_list.clear()
        if with_deal_fun:
            self._deal_fun_list.clear()

    def delete_keyword(self, key, with_deal_fun=False):
        """
        @fun 删除指定公式关键字定义
        @funName delete_keyword
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 功能描述
        @funExcepiton:
            KeyError 当找不到key时抛出该异常

        @funParam {string} key 要删除的关键字标识
        @funParam {bool} with_deal_fun 是否同步清除处理函数列表

        """
        del self._keywords[key]
        # 计算match_list
        self._match_list = self.__keywords_to_match_list(self._keywords)
        if with_deal_fun:
            if key in self._deal_fun_list.keys():
                del self._deal_fun_list[key]

    def add_keyword(self, key, begin_tag, end_tag=None, keyword_para=StructFormulaKeywordPara(),
                    deal_fun=None, is_replace=False):
        """
        @fun 添加公式关键字
        @funName add_keyword
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 添加公式关键字，如果key已存在且is_replace为True则抛出异常
        @funExcepiton:
            KeyError 当is_replace为Falseqiekey已存在时抛出该异常

        @funParam {string} key 公式关键字标识
        @funParam {list} begin_tag 开始标签定义[string-匹配字符串, list-前置字符, list-后置字符]
        @funParam {list} end_tag 结束标签定义[string-匹配字符串, list-前置字符, list-后置字符]，如果没有结束标签为None
        @funParam {StructFormulaKeywordPara} keyword_para 匹配参数
        @funParam {fun} deal_fun 对应key的处理函数，函数的定义必须满足以下要求:
            fun(formular_obj, **kwargs):
                formular_obj : StructFormula 要处理公式对象（函数直接修改对象），该函数需更新对象的formula_value
                kwargs ：计算公式所传入的key=value格式的参数，参数key由处理函数定义（建议统一定义便于简化处理）
        @funParam {bool} is_replace 是否覆盖已有参数

        """
        if not is_replace:
            if key in self._keywords.keys():
                raise KeyError(u'公式关键字标识已存在')
            if deal_fun is not None and key in self._deal_fun_list.keys():
                raise KeyError(u'处理函数关键字标识已存在')
        self._keywords[key] = [
            begin_tag,
            end_tag,
            keyword_para
        ]
        if deal_fun is not None:
            self._deal_fun_list[key] = deal_fun

        # 计算match_list
        self._match_list = self.__keywords_to_match_list(self._keywords)

    def run_formula(self, formula_str, **kwargs):
        """
        @fun 解析并执行公式计算
        @funName run_formula
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 解析并执行公式计算
        @funExcepiton:
            LookupError 如果公式存在错误（例如找不到结束标签等），抛出该异常

        @funParam {string} formula_str 要处理的公式
        @funParam {dict} kwargs 传入的公式处理参数集，动态key-value方式参数

        @funReturn {StructFormula} 解析出来的公式对象，并完成所有公式对象（含子对象）的formula_value计算

        """
        # 先解析公式
        _formular_obj = FormulaTool.__analyse_formula(
            formula_str=formula_str, keywords=self._keywords,
            ignore_case=self._ignore_case, match_list=self._match_list
        )

        # 计算公式并返回
        self.__run_formula(formular_obj=_formular_obj, **kwargs)

        return _formular_obj

    def run_formula_as_string(self, formula_str, **kwargs):
        """
        @fun 以字符串替换方式解析并执行公式计算
        @funName run_formula
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 解析并执行公式计算，所有公式最终计算为字符串并替换父公司的对应内容
        @funExcepiton:
            LookupError 如果公式存在错误（例如找不到结束标签等），抛出该异常

        @funParam {string} formula_str 要处理的公式
        @funParam {dict} kwargs 传入的公式处理参数集，动态key-value方式参数

        @funReturn {StructFormula} 解析出来的公式对象，并完成所有公式对象（含子对象）的formula_value计算

        """
        # 先解析公式
        _formular_obj = FormulaTool.__analyse_formula(
            formula_str=formula_str, keywords=self._keywords,
            ignore_case=self._ignore_case, match_list=self._match_list
        )

        # 计算公式并返回
        self.__run_formula_as_string(formular_obj=_formular_obj, **kwargs)

        return _formular_obj


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))
