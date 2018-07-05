#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
增强的交互命令行扩展处理，基于prompt_toolkit进行封装和扩展
@module prompt_plus
@file prompt_plus.py
"""

from __future__ import unicode_literals
import threading
import traceback
import copy
import time
import sys
from queue import Queue
import asyncio
# from prompt_toolkit import prompt, Prompt
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession
# from prompt_toolkit.key_binding import KeyBindings
# from prompt_toolkit.enums import EditingMode
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.completion import Completer, Completion
from .generic import CResult, ExceptionTools
from .simple_stream import StringStream


"""
命令参数内部存储结构定义
@typedef {cmdpara} 命令参数 - 定义统一的命令参数内部存储结构，基本类型是dict，具体定义如下：
    key为命令标识
    value同样为dict()，value的key为参数名，参数名与参数值的定义如下:
        deal_fun (匹配到命令要执行的函数) : fun 函数定义（function类型）
            函数固定入参为fun(message='', cmd='', cmd_para='')
                @param {string} message - prompt提示信息
                @param {string} cmd - 执行的命令key值
                @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
                @returns {string} - 执行命令完成后要输到屏幕的内容
        name_para (para_name=para_value形式的参数) : dict(para_name: para_value_list)
            para_name {string} - 参数名
            para_value_list {string[]} - 对应参数名下的可选参数值清单，如果para_value_list为None代表可以输入任意值
        short_para (-para_char para_value 形式的参数) : dict(para_char, para_value_list)
            para_char {char} - 短参数标识字符（单字符，不带-）
            para_value_list {string[]} - 对应参数名下的可选参数值清单，如果para_value_list为None代表可以输入任意值
            注：该形式可以支持多个字符写在一个'-'后面，例如: -xvrt
        long_para (-para_name para_value形式的参数) : dict(para_name, para_value_list)
            para_name {string} - 参数名（可以多字符，不带-）
            para_value_list {string[]} - 对应参数名下的可选参数值清单，如果para_value_list为None代表可以输入任意值

""".strip()


__MOUDLE__ = 'prompt_plus'  # 模块名
__DESCRIPT__ = '增强的交互命令行扩展处理'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = 'Huijian Li'  # 作者
__PUBLISH__ = '2018.06.30'  # 发布日期


class PromptPlusCmdParaLexer(Lexer):
    """
    PromptPlus的命令关键字解析器，继承prompt_toolkit.Lexer类，实现自身对命令参数的解析和高亮处理
    参考SimpleLexer(Lexer)，实际上需要实现的接口函数为lex_document(self, document)
    """

    #############################
    # 内部变量
    #############################
    _cmd_para = dict()  # {type:cmdpara}
    _ignore_case = False
    # _cache = MemoryCache(size=10, sorted_order=EnumCacheSortedOrder.HitTimeFirst)

    #############################
    # 内部函数
    #############################

    def _match_cmd_para_str(self, match_str='', cmd='', match_type=''):
        """
        按类型找到指定词对应的命令行参数key值

        @param {string} match_str='' - 要匹配的词（完整的命令或参数）
        @param {string} cmd='' - 指定要搜索的命令（匹配命令参数时候用到，如果要匹配命令则无需传入）
        @param {string} match_type='' - 匹配类型（cmd|name_para|short_para|long_para）

        @returns {string} - 没有匹配上返回''，匹配上返回对应的关键字
        """
        _ret_key = ''
        if match_type == 'cmd':
            # 匹配命令
            if self._ignore_case:
                # 忽略大小写
                for _key in self._cmd_para.keys():
                    if _key.upper() == match_str.upper():
                        _ret_key = _key
                        break
            else:
                # 不忽略大小写
                if match_str in self._cmd_para.keys():
                    _ret_key = match_str
        else:
            # 匹配命令参数名
            if not(cmd not in self._cmd_para.keys() or
                   match_type not in self._cmd_para[cmd].keys() or
                   self._cmd_para[cmd][match_type] is None):
                if self._ignore_case:
                    for _key in self._cmd_para[cmd][match_type].keys():
                        if _key.upper() == match_str.upper():
                            _ret_key = _key
                            break
                else:
                    if match_str in self._cmd_para[cmd][match_type].keys():
                        _ret_key = match_str
        # 最终返回匹配结果
        return _ret_key

    def _analyse_cmd_para_stream_dealer(self, deal_char='', position=0, cmd_para_str='',
                                        match_cmd='', current_info=None,
                                        style_list=None, info_list=None):
        """
        使用StringStream逐个字符解析命令行参数的流处理函数（注意不含cmd部分）
        该函数执行流处理结束后，会生成info_list（关键字列表）和style_list（关键字样式列表），用于Lexer显示样式

        @param {string} deal_char='' - 当前处理到的字符
        @param {int} position=0 - 当前字符位置
        @param {string} cmd_para_str='' - 要处理的完整参数字符串
        @param {string} match_cmd='' - 要匹配的命令
        @param {list} current_info=None - 当前正在处理的字符所处的词的处理信息,传入的是上一个字符处理后的状态，处理中会更新:
            [
                引号是否结束(bool), 引号开始位置(int),
                长短参数是否结束(bool)， 长短参数开始位置(int),
                连续词是否结束, 连续词开始位置
            ]
            注：如果需标注参数内容是从字符串开始，可以通过传入current_info设置，应对多行处理的情况
        @param {list} style_list=None - 字符样式对应列表，传入的是上一个字符处理后的列表，处理中会更新:
            [('style_str','char_str'), ('style_str','char_str'), ...]
            注意：字符处理完后可能会在最后多一个char_str为空的列表项，完整结束后需判断和删除
        @param {list} info_list=None - 与style_list一一对应，等级每个标记的具体信息，传入的是上一个字符处理后的列表，
            处理中会更新，格式为:[开始位置(int), 结束位置(int), 标记类型(''|cmd|name_para|short_para|long_para|wrong)]
        """
        # 初始化可变入参
        if current_info is None:
            current_info = list()
        if style_list is None:
            style_list = list()
        if info_list is None:
            info_list = list()

        if position == 0:
            # 进行初始化
            # [引号是否结束(bool), 引号开始位置(int),
            # 长短参数是否结束(bool)， 长短参数开始位置(int),
            # 连续词是否结束, 连续词开始位置]
            if current_info.count == 0:
                current_info.extend([True, -1, True, -1, False, 0])
            else:
                _is_in_string = current_info[0]
                current_info.clear()
                current_info.extend([_is_in_string, -1, True, -1, False, 0])

            # [('style_str','char_str'), ('style_str','char_str'), ...]，注意如果对外部变量直接用=赋值，传不到外面
            style_list.clear()
            style_list.append(('class:', ''))
            # [开始位置(int), 结束位置(int), 标记类型(''\cmd\name_para\short_para\long_para)]
            info_list.clear()
            info_list.append([0, 0, ''])

        # 开始正式的处理
        _last_index = len(style_list) - 1
        _last_style_word = style_list[_last_index][1]
        if not current_info[0]:
            # 还在双引号里面，将自己纳入上一个处理中
            style_list[_last_index] = (style_list[_last_index][0], _last_style_word + deal_char)
            info_list[_last_index][1] = position + 1
            if deal_char == '"':
                # 是引号结束
                current_info[0] = True
                current_info[1] = -1
            return  # 继续等待下一个处理

        # 不在引号里面，判断几个特殊字符
        _last_word = cmd_para_str[current_info[5]: position]
        if deal_char == ' ':
            # 引号外遇到空格，代表上一个字的结束
            if _last_word != '' and _last_word[0:1] == '-' and \
                self._match_cmd_para_str(match_str=_last_word[1:], cmd=match_cmd,
                                         match_type='long_para') != '':
                # 开始是按短参数匹配的，判断是否能匹配到长参数，如果可以，则修改为长参数
                _deal_index = _last_index
                # 注意_deal_index有可能变成-1，因此需要进行判断
                while _deal_index >= 0 and info_list[_deal_index][0] >= current_info[5]:
                    del info_list[_deal_index]
                    del style_list[_deal_index]
                    _deal_index -= 1
                # 删除完以后，重新建立样式
                style_list.append(('class:long_para', _last_word))
                info_list.append([current_info[5], position, 'long_para'])
                current_info[2] = True  # 标注长短词结束
                _last_index = len(style_list) - 1
                _last_style_word = style_list[_last_index][1]

            # 其他情况无需对原来的样式进行调整单纯关闭和初始化下一个词的开始即可
            if style_list[_last_index][1] == '':
                # 本来就没有词，不用特殊处理，把空格放到style_list最后的位置即可
                style_list[_last_index] = ('class:', ' ')
                info_list[_last_index][1] = position + 1
            else:
                # 原来已经有词，新开一个
                style_list.append(('class:', ' '))
                info_list.append([position, position+1, ''])
            # 初始化下一个词的处理
            style_list.append(('class:', ''))
            info_list.append([position + 1, position + 1, ''])
            current_info.clear()
            current_info.extend([True, -1, True, -1, False, position + 1])
            return
        elif deal_char == '"' and _last_word[0:1] != '-':
            # 字符串开始，与平常处理没有分别，只是要标注是字符串开始
            style_list[_last_index] = (style_list[_last_index][0], _last_style_word + deal_char)
            info_list[_last_index][1] = position + 1
            current_info[0] = False
            current_info[1] = position
            return
        elif deal_char == '-' and (position == 0 or cmd_para_str[position-1:position] == ' '):
            # 短参数匹配，且是在词的开始位置
            style_list[_last_index] = ('class:short_para', '-')
            info_list[_last_index][1] = position + 1
            current_info[2] = False
            current_info[3] = position
            # 初始化下一个词的处理
            style_list.append(('class:', ''))
            info_list.append([position + 1, position + 1, ''])
            return
        elif deal_char == '=' and _last_word != '' and _last_word[0:1] != '-':
            # 遇到等号，则代表前面是name_para
            if self._match_cmd_para_str(match_str=_last_word,
                                        cmd=match_cmd, match_type='name_para') != '':
                # 匹配上
                style_list[_last_index] = ('class:name_para', _last_word)
                info_list[_last_index][2] = 'name_para'
            else:
                # 匹配不上
                style_list[_last_index] = ('class:wrong_tip', _last_word)
                info_list[_last_index][2] = 'wrong'
            # 加上自身样式同步初始化下一个的处理
            style_list.append(('class:', '='))
            info_list.append([position, position + 1, ''])
            return
        else:
            # 延续字符的处理，只需要特殊判断是否短参数的情况
            if not current_info[2]:
                # 按短参数匹配处理
                if self._match_cmd_para_str(match_str=deal_char, cmd=match_cmd,
                                            match_type='short_para') != '':
                    # 匹配上
                    style_list[_last_index] = ('class:short_para', deal_char)
                    info_list[_last_index][1] = position + 1
                    info_list[_last_index][2] = 'short_para'
                else:
                    # 匹配不上
                    style_list[_last_index] = ('class:wrong_tip', deal_char)
                    info_list[_last_index][1] = position + 1
                    info_list[_last_index][2] = 'wrong'
                # 初始化下一个词的处理
                style_list.append(('class:', ''))
                info_list.append([position + 1, position + 1, ''])
                return
            else:
                # 正常字符增加，延续上一个的情况
                style_list[_last_index] = (style_list[_last_index][0], _last_style_word + deal_char)
                info_list[_last_index][1] = position + 1
                return

    def _get_line_tokens(self, line='', match_cmd='', start_in_string=False, current_info=None):
        """
        按行进行解析，返回一行参数的样式清单（调用_analyse_cmd_para_stream_dealer）
        @todo 通过缓存提升速度

        @param {string} line='' - 要处理的行字符串
        @param {string} match_cmd='' - 要匹配的命令
        @param {bool} start_in_string=False - 当前行是否从字符串内部开始（上一行开始的字符串中间）
        @param {list} current_info=None - 当前正在处理的字符所处的词的处理信息

        @returns {list} - 样式清单列表
        """
        # 初始化可变参数
        if current_info is None:
            current_info = list()

        if line == '':
            return []

        # 从缓存获取处理参数，缓存唯一标识格式为: match_cmd + str(start_in_string) + line
        # TODO(待办人): 发现换了算法后，即使不用缓存，响应速度也能接受，因此暂时不实现缓存机制
        # _cache_key = match_cmd + str(start_in_string) + line
        _cache_data = None

        if _cache_data is None:
            # 从缓存获取不到数据，将_cache_data设置为从0位置开始，cache的数据格式如下：
            # [current_position, last_current_info, last_style_list, last_info_list]
            if start_in_string:
                _cache_data = [0, [False, 0, True, -1, False, 0], list(), list()]  # 从字符串开始行
            else:
                _cache_data = [0, [True, 0, True, -1, False, 0], list(), list()]
        else:
            _cache_data = copy.deepcopy(x=_cache_data)  # 深度复制，避免影响原缓存信息

        # 执行处理
        _position = _cache_data[0]
        _str_len = len(line)
        while _position < _str_len:
            self._analyse_cmd_para_stream_dealer(
                deal_char=line[_position: _position+1],
                position=_position,
                cmd_para_str=line,
                match_cmd=match_cmd,
                current_info=_cache_data[1],
                style_list=_cache_data[2],
                info_list=_cache_data[3]
            )
            _position += 1

        # 加入到缓存
        # self._cache.update_cache(key=_cache_key, data=_cache_data)

        # 返回当前行的最后信息
        current_info.clear()
        current_info.extend(copy.deepcopy(_cache_data[1]))

        # 处理返回值
        _para_style = copy.deepcopy(_cache_data[2])
        _style_len = len(_para_style)
        if _style_len > 0 and _para_style[_style_len-1][1] == '':
            # 最后一个没有具体数据，删除
            del _para_style[_style_len-1]
        return _para_style

    def _get_lexer_tokens(self, lines=None):
        """
        解析传入的字符数组（多行）并返回解析后的样式清单列表（支持多行换行的情况）

        @param {list} lines=None - 要解析的字符串数组

        @returns {list} - 样式清单列表，每行对应lines的一行，格式为:
            [
                [('style_str','char_str'), ('style_str','char_str'), ...],
                [('style_str','char_str'), ('style_str','char_str'), ...],
                ...
            ]
        """
        # 初始化可变参数
        if lines is None:
            lines = list()

        _style_list = [[('class:', _line)] for _line in lines]  # 每行一个默认的清单

        # 先判断第一行的信息，截取命令
        _split_index = lines[0].find(' ')
        _cmd = ''
        if _split_index > 0:
            _cmd = lines[0][0:_split_index]
        else:
            _cmd = lines[0]  # 整行都是命令

        _match_cmd = self._match_cmd_para_str(match_str=_cmd, match_type='cmd')

        if _match_cmd == '':
            # 第一行匹配不到命令
            return _style_list

        _cmd_style = ('class:cmd', _cmd)
        _current_info = list()
        _para_style = self._get_line_tokens(
            line=lines[0][len(_cmd):], match_cmd=_match_cmd, start_in_string=False,
            current_info=_current_info
        )
        _para_style.insert(0, _cmd_style)
        _style_list[0] = _para_style

        # 其他行的处理
        _lineno = 1
        while _lineno < len(lines):
            _start_in_string = False
            if _current_info.count != 0:
                _start_in_string = not _current_info[0]
            _current_info = list()
            _para_style = self._get_line_tokens(
                line=lines[_lineno], match_cmd=_match_cmd,
                start_in_string=_start_in_string, current_info=_current_info
            )
            _style_list[_lineno] = _para_style
            _lineno += 1

        # 完成处理
        return _style_list

    #############################
    # 公共函数
    #############################

    def __init__(self, cmd_para=None, ignore_case=False):
        """
        PromptPlusCmdParaLexer的构造函数

        @param {cmdpara} cmd_para=None - 命令参数字典
        @param {bool} ignore_case=False - ignore_case 匹配命令是否忽略大小写
        """
        # 初始化可变参数
        if cmd_para is None:
            cmd_para = dict()

        self._cmd_para = cmd_para
        self._ignore_case = ignore_case

    def lex_document(self, document):
        """
        实现Lexer类的解析文档函数，按行解析并返回对应的样式，字符列表

        @param {prompt_toolkit.document} document - 要解析的lex文档
        """
        lines = document.lines

        # 直接进行所有行的解析，得到各行的解析数组，但由于每次全部进行检索性能不好，输入内容多的时候会卡顿
        # 因此要优化算法，利用缓存历史数据提升处理速度
        _style_list = []
        try:
            _style_list = self._get_lexer_tokens(lines=lines)
        except Exception:
            _style_list = [[('class:', _line)] for _line in lines]  # 每行一个默认的清单
            print(traceback.format_exc())

        def get_line(lineno):
            " Return the tokens for the given line. "
            try:
                return _style_list[lineno]
            except IndexError:
                return []

        return get_line


class PromptPlusCompleter(Completer):
    """
    PromptPlus的自动完成类，根据输入的状态以及命令行提示可用的命令和参数输入
    该类继承prompt_toolkit.Completer类，参考DummyCompleter类，主要对外提供get_completions接口
    """

    #############################
    # 内部变量
    #############################
    _cmd_para = dict()  # {type:cmdpara}
    _ignore_case = False
    _slow_time = 0
    _cmd_word = list()
    _para_word = dict()

    #############################
    # 私有函数
    #############################

    def _match_cmd_para_str(self, match_str='', cmd='', match_type=''):
        """
        按类型找到指定词对应的命令行参数key值
        @todo 该函数与Lexer中的函数一样，看是否要整合为1个

        @param {string} match_str='' - 要匹配的词（完整的命令或参数）
        @param {string} cmd='' - 指定要搜索的命令（匹配命令参数时候用到，如果要匹配命令则无需传入）
        @param {string} match_type='' - 匹配类型（cmd|name_para|short_para|long_para）

        @returns {string} - 没有匹配上返回''，匹配上返回对应的关键字
        """
        _ret_key = ''
        if match_type == 'cmd':
            # 匹配命令
            if self._ignore_case:
                # 忽略大小写
                for _key in self._cmd_para.keys():
                    if _key.upper() == match_str.upper():
                        _ret_key = _key
                        break
            else:
                # 不忽略大小写
                if match_str in self._cmd_para.keys():
                    _ret_key = match_str
        else:
            # 匹配命令参数名
            if not(cmd not in self._cmd_para.keys() or
                   match_type not in self._cmd_para[cmd].keys() or
                   self._cmd_para[cmd][match_type] is None):
                if self._ignore_case:
                    for _key in self._cmd_para[cmd][match_type].keys():
                        if _key.upper() == match_str.upper():
                            _ret_key = _key
                            break
                else:
                    if match_str in self._cmd_para[cmd][match_type].keys():
                        _ret_key = match_str
        # 最终返回匹配结果
        return _ret_key

    def _check_position_in_string(self, document):
        """
        检查文档当前的位置是否在引号里面

        @param {prompt_toolkit.document} document - 要检查的文档

        @returns {bool} - 文档当前位置是否在字符串中
        """
        _lineno = document.cursor_position_row
        _lineindex = document.cursor_position_col
        _current_lineno = 0
        _is_in_string = False
        _is_in_para = False  # 是否在长短参数里面（长短参数里的双引号当普通字符处理）
        _is_word_begin = True  # 指示当前位置是否单词的开始
        while _current_lineno <= _lineno:
            _line = document.lines[_current_lineno]
            _current_index = 0
            while ((_current_lineno == _lineno and _current_index < _lineindex) or
                   (_current_lineno < _lineno and _current_index < len(_line))):
                _char = _line[_current_index: _current_index + 1]
                if _is_in_string:
                    if _char == '"':
                        _is_in_string = False
                elif _is_in_para:
                    if _char == ' ':
                        _is_in_para = False
                        _is_word_begin = True
                else:
                    if _char == ' ':
                        # 遇到空格，代表下一个是词的开始
                        _is_word_begin = True
                    elif _char == '"':
                        # 遇到双引号，是引号的开始
                        _is_in_string = True
                        _is_word_begin = False
                    elif _is_word_begin and _char == '-':
                        # 在词的开始遇到-，代表是参数的开始
                        _is_in_para = True
                        _is_word_begin = False
                    else:
                        _is_word_begin = False
                _current_index += 1
            _current_lineno += 1

        return _is_in_string

    def _get_complete_words(self, document):
        """
        获取当前词的自动填充列表

        @param {prompt_toolkit.document} document - 要获取的文档

        @returns {list} - 获取到的填充词列表
        """
        _cmd = ''
        _current_word = document.get_word_before_cursor()
        if document.cursor_position_row == 0 and document.cursor_position_col == len(_current_word):
            return self._cmd_word

        # 非开头的输入，先判断是否能找到命令参数
        _split_index = document.lines[0].find(' ')
        if _split_index > 0:
            _cmd = self._match_cmd_para_str(
                match_str=document.lines[0][0:_split_index], match_type='cmd')
        if _cmd == '':
            # 匹配不到命令行参数，返回空词
            return []

        # 判断是否在双引号中
        if self._check_position_in_string(document=document):
            # 在引号中，不进行自动提示
            return []

        # 其他情况，全量匹配即可
        return self._para_word[_cmd]

    def _get_word_before_cursor(self, document):
        """
        获取当前位置的词，解决document.get_word_before_cursor不支持-=等字符作为一个词判断的问题

        @param {prompt_toolkit.document} document - 要处理的文档

        @returns {string} - 找到当前位置前的词
        """
        _word_before_cursor = document.get_word_before_cursor()
        # 检查当前词的前一个字符是否空格或文本开头，如果不是，则需要向前查找
        _x, _y = document.cursor_position_row, document.cursor_position_col - \
            len(_word_before_cursor)
        _line = document.lines[_x]
        while _y > 0 and _line[_y-1:_y] != ' ':
            _word_before_cursor = _line[_y-1:_y] + _word_before_cursor
            _y -= 1

        return _word_before_cursor

    #############################
    # 公共函数
    #############################

    def __init__(self, cmd_para=None, ignore_case=False, slow_time=0):
        """
        PromptPlusCompleter的构造函数，传入命令行参数

        @param {cmdpara} cmd_para=None - 命令参数字典
        @param {bool} ignore_case=False - 匹配命令是否忽略大小写
        @param {int} slow_time=0 - 延迟提示的时长（秒），0代表不延迟
        """
        # 初始化可变参数
        if cmd_para is None:
            cmd_para = dict()

        self.loading = False
        self._cmd_para = cmd_para
        self._ignore_case = ignore_case
        self._slow_time = slow_time
        # 初始化词组，设置self._cmd_word和self._para_word，用于自动完成快速查找词
        for _cmd in cmd_para.keys():
            self._cmd_word.append(_cmd)
            self._para_word[_cmd] = list()
            # key - value形式的参数
            if cmd_para[_cmd]['name_para'] is not None:
                for _name_para_key in cmd_para[_cmd]['name_para'].keys():
                    self._para_word[_cmd].append(_name_para_key+'=')
                    if cmd_para[_cmd]['name_para'][_name_para_key] is not None:
                        for _name_para_value in cmd_para[_cmd]['name_para'][_name_para_key]:
                            self._para_word[_cmd].append(_name_para_key + '=' + _name_para_value)
            # 长短名
            if cmd_para[_cmd]['long_para'] is not None:
                for _long_para_key in cmd_para[_cmd]['long_para'].keys():
                    self._para_word[_cmd].append('-'+_long_para_key+' ')
                    if cmd_para[_cmd]['long_para'][_long_para_key] is not None:
                        for _long_para_value in cmd_para[_cmd]['long_para'][_long_para_key]:
                            self._para_word[_cmd].append(
                                '-' + _long_para_key + ' ' + _long_para_value)
            if cmd_para[_cmd]['short_para'] is not None:
                for _short_para_key in cmd_para[_cmd]['short_para'].keys():
                    self._para_word[_cmd].append('-'+_short_para_key + ' ')
                    if cmd_para[_cmd]['short_para'][_short_para_key] is not None:
                        for _short_para_value in cmd_para[_cmd]['short_para'][_short_para_key]:
                            self._para_word[_cmd].append(
                                '-' + _short_para_key + ' ' + _short_para_value)

    def get_completions(self, document, complete_event):
        """
        重载Completer的提示函数

        @param {prompt_toolkit.document} document - 要处理的文档
        @param {function} complete_event - 事件
        """
        self.loading = True
        word_before_cursor = self._get_word_before_cursor(document=document)

        _word_list = self._get_complete_words(document=document)

        if self._slow_time > 0:
            time.sleep(self._slow_time)  # Simulate slowness.

        if self._ignore_case:
            word_before_cursor = word_before_cursor.lower()

        for word in _word_list:
            if self._ignore_case:
                word = word.lower()

            if word.startswith(word_before_cursor):
                yield Completion(word, -len(word_before_cursor))

        self.loading = False


class PromptPlus(object):
    """
    命令行扩展处理类,利用python-prompt-toolkit实现人机交互处理，再补充封装命令处理部分登记注册的功能，固定的操作:
        Ctrl + C : abort,取消本次输入
        Ctrl + D : exit,关闭命令行

    """

    #############################
    # 静态方法，无需实例化对象即可使用的方法
    #############################

    @staticmethod
    def simple_prompt(message='', deal_fun=None, **kwargs):
        """
        简单命令行输入处理函数,获取键盘输入，并返回输入处理结果

        @static

        @param {string} message='' - 获取输入的提示信息
        @param {function} deal_fun=None - 获取到输入后执行的处理函数fun(prompt_text='')，函数要求满足:
            输入参数为prompt_text，返回值为string
        @param {kwargs} kwargs python-prompt-toolki的prompt参数:
            详细参数见python-prompt-toolki的官方文档，常用参数见类注释中的《python-prompt-toolki的prompt参数说明》

        @returns {string} - 如果deal_fun为None，直接返回所获取到的输入值:
            如果deal_fun不为None，则返回deal_fun的执行结果

        @throws {exception} - 可能会返回deal_fun执行中出现的各种异常
        """
        _prompt_text = prompt(message, **kwargs)
        ret_str = ''
        if deal_fun is not None:
            ret_str = deal_fun(_prompt_text)
            if ret_str is None:
                ret_str = ''
        else:
            ret_str = _prompt_text
        return ret_str

    @staticmethod
    @StringStream.stream_decorator(is_sync=True)
    def _analyse_para_stream_dealer(deal_obj=None, position=0, str_obj='', para_list=None):
        """
        逐个字符检索参数的流函数定义
            算法描述:
            1、para_list既作为结果对象，也作为堆栈对象进行处理，每一行的格式如下
                [参数名, 参数值, 关联符('='或' ')，开始位置(int), 结束位置(int), 引号是否结束(bool), 处理是否结束(bool)]
            2、逐个字符进行解析，如果判断到para_list最后一个信息未完成，则当前字符是延续上一个处理
            3、优先匹配'-'开头的参数名，如果该参数名后紧接空格和非'-'开头的词，则认为这个词是对应的参数值
            4、对于非'-'开头且不认为是'-'参数的参数值的对象，如果对象中间有'='，则拆分为参数名和参数值两部分，否则认为
                直接就是独立的参数值
            5、对于有双引号的情况，检索到双引号结束，且下一个字符不是空格的情况，则认为下一个字符是一起的

        @static

        @decorators StringStream - 定义为字符流处理函数

        @param {object} deal_obj=None - 当前处理的字符对象
        @param {int} position=0 - 当前处理位置
        @param {string} str_obj='' - 完整的字符对象
        @param {list} para_list=None - 处理结果缓存列表
        """
        # 初始化可变参数
        if para_list is None:
            para_list = list()

        _last_index = len(para_list) - 1
        if _last_index == -1 or para_list[_last_index][6]:
            # 上一个参数已经处理结束，开辟新的参数
            if deal_obj == ' ':
                # 遇到空格不处理，直接返回
                return
            elif deal_obj == '-':
                # 长参数模式，写入堆栈
                para_list.append([deal_obj, '', '', position, -1, True, False])
                return
            else:
                # 先认为是纯参数值
                _info = ['', deal_obj, '', position, -1, True, False]
                if deal_obj == '"':
                    # 引号的开始，标记未结束
                    _info[5] = False
                para_list.append(_info)
                return
        else:
            # 延续上一个参数的处理
            if not para_list[_last_index][5]:
                # 还属于引号的处理中
                para_list[_last_index][1] = para_list[_last_index][1] + deal_obj  # 参数值更新
                if deal_obj == '"':
                    # 引号结束
                    para_list[_last_index][5] = True
                return
            elif deal_obj == ' ':
                # 遇到空格且不在引号内，是参数名或参数值的结束
                if para_list[_last_index][1] == '':
                    # 是参数名的结束，需要判断再下一个字符是否'-'
                    if position+1 < len(str_obj) and str_obj[position+1: position+2] != '-':
                        # 后面不是新的参数，并且也没有到结尾，属于参数值，更新参数关联字符即可
                        para_list[_last_index][2] = ' '
                    else:
                        # 已经到结尾或新参数，当前结束
                        para_list[_last_index][4] = position
                        para_list[_last_index][6] = True
                else:
                    # 是参数值的结束
                    para_list[_last_index][4] = position
                    para_list[_last_index][6] = True
                    # 需要判断是否=号模式的参数
                    if para_list[_last_index][0] == '' and para_list[_last_index][1][0:1] != '"':
                        _index = para_list[_last_index][1].find('=')
                        if _index > 0:
                            para_list[_last_index][0] = para_list[_last_index][1][0:_index]
                            para_list[_last_index][1] = para_list[_last_index][1][_index + 1:]
                            para_list[_last_index][2] = '='

            else:
                # 非空格，如果关联字符不为空就是参数值，如果关联字符为空就是参数名
                if para_list[_last_index][2] == '' and para_list[_last_index][1] == '':
                    para_list[_last_index][0] = para_list[_last_index][0] + deal_obj
                else:
                    para_list[_last_index][1] = para_list[_last_index][1] + deal_obj
                # 判断是否引号
                if (deal_obj == '"' and
                        (para_list[_last_index][0][0:1] != '-' or para_list[_last_index][2] != '')):
                    para_list[_last_index][5] = False
                return

    @classmethod
    def analyse_cmd_para(cls, cmd_para_str='', is_start_in_string=False):
        """
        解析命令的参数（通过流方式调用_analyse_para_stream_dealer）

        @decorators classmethod - 定义类成员函数，无需实例化可调用类内部函数

        @param {string} cmd_para_str='' - 要解析的参数字符串
        @param {bool} is_start_in_string=False - 是否在字符串中间启动，在多行分开解析时使用

        @returns {list} - 解析结果，格式如下:
            [参数名, 参数值, 关联符('='或' ')，开始位置(int), 结束位置(int), 引号是否结束(bool), 处理是否结束(bool)]
        """
        _para_list = list()
        if is_start_in_string:
            _para_list.append(['', '', '', 0, -1, False, False])
        cls._analyse_para_stream_dealer(deal_obj=None, position=0,
                                        str_obj=cmd_para_str, para_list=_para_list)
        _len = len(_para_list)
        if _len > 0 and not _para_list[_len-1][6]:
            # 没有结束，修正数据
            _para_list[_len - 1][6] = True
            _para_list[_len - 1][4] = _len
            # 需要判断是否=号模式的参数
            if _para_list[_len - 1][0] == '' and _para_list[_len - 1][1][0:1] != '"':
                _index = _para_list[_len - 1][1].find('=')
                if _index > 0:
                    _para_list[_len - 1][0] = _para_list[_len - 1][1][0:_index]
                    _para_list[_len - 1][1] = _para_list[_len - 1][1][_index + 1:]
                    _para_list[_len - 1][2] = '='
        return _para_list

    #############################
    # 实例化的命令行处理 - 内部变量
    #############################

    _prompt_instance = None  # 命令输入处理对象（prompt_toolkit.shortcuts.Prompt类）
    _message = 'CMD>'  # 命令行提示符内容
    _default = ''  # 人机交互输入的默认值，直接显示在界面上，可以进行修改后回车输入
    # 默认输入参数值，定义了一些必须有默认取值的参数，用于创建_prompt_init_para并合并实际的调用参数
    _prompt_default_para = {
        'cmd_para': dict(),
        'ignore_case': False,
        'default_dealfun': None,
        'on_abort': None,
        'on_exit': None,
        'is_async': False,
        'logger': None,
        'enable_color_set': True,
        'color_set': None,
        'enable_cmd_auto_complete': True,
        'cmd_auto_complete_slow_time': 0
    }
    _prompt_init_para = dict()  # 用于初始化输入类的参数字典，key为参数名(string)，value为参数值
    # Prompt类初始化支持的参数名清单，内部使用
    _prompt_para_name_list = (
        'lexer', 'completer', 'complete_in_thread', 'is_password',
        'editing_mode', 'extra_key_bindings', 'is_password', 'bottom_toolbar',
        'style', 'include_default_pygments_style', 'rprompt', 'multiline',
        'prompt_continuation', 'wrap_lines', 'history',
        'enable_history_search', 'complete_while_typing',
        'validate_while_typing', 'complete_style', 'mouse_support',
        'auto_suggest', 'clipboard', 'validator', 'refresh_interval',
        'extra_input_processor', 'default', 'enable_system_prompt',
        'enable_suspend', 'enable_open_in_editor', 'reserve_space_for_menu',
        'tempfile_suffix', 'inputhook')
    # 命令参数的默认设置值，用于合并至外部参数对象，避免传入参数有误导致其他问题
    _cmd_para_default = {
        'deal_fun': None,
        'name_para': None,
        'short_para': None,
        'long_para': None
    }
    _loop = asyncio.get_event_loop()  # 异步模式需要的事件循环处理对象
    _async_cmd_queue = Queue()  # 异步模式的命令执行队列
    # 关键字配色方案，每个配色方案格式为'#000088 bg:#aaaaff underline'
    _default_color_set = {
        # 用户输入
        '': '#ffffff',  # 默认输入
        'cmd': '#66ff66',  # 命令
        'name_para': '#00FFFF',  # key-value形式参数名
        'short_para': '#00FFFF',  # -char形式的短参数字符
        'long_para': '#ff8c00',  # -name形式的长参数字符
        'wrong_tip': '#ff0000 bg:#ffffff reverse',  # 错误的命令或参数名提示

        # prompt提示信息
        'prompt': '#EEEEEE'
    }

    #############################
    # 实例化的命令行处理 - 内部函数
    #############################

    def _init_prompt_instance(self):
        """
        根据类的当前参数重新初始化prompt实例对象

        @throws {ValueError} - 当传入的参数值不对的时候抛出该异常
        """
        # 根据传入参数设置一些特殊值，简化外部处理
        # History
        if 'enable_history_search' in self._prompt_init_para.keys() \
            and self._prompt_init_para['enable_history_search'] \
            and ('history' not in self._prompt_init_para.keys() or
                 self._prompt_init_para['history'] is None):
            # 要启动历史检索功能，但未指定对象
            self._prompt_init_para['history'] = InMemoryHistory()

        # 颜色处理
        if self._prompt_init_para['enable_color_set']:
            _color_set = self._default_color_set.copy()
            if self._prompt_init_para['color_set'] is not None:
                _color_set.update(self._prompt_init_para['color_set'])
            # 生成style
            _style = Style.from_dict(_color_set)
            self._prompt_init_para['style'] = _style
            _lexer = PromptPlusCmdParaLexer(cmd_para=self._prompt_init_para['cmd_para'],
                                            ignore_case=self._prompt_init_para['ignore_case'])
            self._prompt_init_para['lexer'] = _lexer

        # 自动完成处理
        if self._prompt_init_para['enable_cmd_auto_complete']:
            _completer = PromptPlusCompleter(
                cmd_para=self._prompt_init_para['cmd_para'],
                ignore_case=self._prompt_init_para['ignore_case'],
                slow_time=self._prompt_init_para['cmd_auto_complete_slow_time']
            )
            self._prompt_init_para['completer'] = _completer
            self._prompt_init_para['complete_in_thread'] = True

        # 实例化输入类
        if self._prompt_instance is not None:
            del self._prompt_instance  # 先清除原来的对象
        _init_str = ('self._prompt_instance = PromptSession('
                     'message=self._get_color_message(self._message)'
                     ', default=self._default')
        for _para_name in self._prompt_init_para.keys():
            if _para_name in self._prompt_para_name_list:
                _init_str = '%s, %s=self._prompt_init_para[\'%s\']' % (
                    _init_str, _para_name, _para_name)
        _init_str = '%s)' % _init_str
        # 动态执行初始化处理
        exec(_init_str)

    def _get_color_message(self, message):
        """
        根据配色方案返回指定消息的对应值

        @param {string} message - 要处理的消息

        @returns {string} - 返回格式化后的消息?
        """
        _message = message
        if self._prompt_init_para['enable_color_set']:
            _message = (lambda: ('class:prompt', message))
        return _message

    def _match_cmd_para(self, cmd=''):
        """
        根据命令字符串匹配命令参数定义，返回匹配上的命令key（匹配不到返回''）

        @param {string} cmd='' - 要匹配的命令字符串

        @returns {string} - 命令字符串所在的位置
        """
        ret_key = ''
        if self._prompt_init_para['ignore_case']:
            # 忽略大小写
            for _key in self._prompt_init_para['cmd_para'].keys():
                if cmd.upper() == _key.upper():
                    ret_key = _key
                    break
        else:
            # 不忽略大小写
            if cmd in self._prompt_init_para['cmd_para'].keys():
                ret_key = cmd
        return ret_key

    def _call_on_abort(self, message=''):
        """
        用户取消输入时执行函数

        @param {string} message='' - 传入的提示信息

        @returns {string} - 返回执行函数的返回结果
        """
        if ('on_abort' in self._prompt_init_para.keys() and
                self._prompt_init_para['on_abort'] is not None):
            try:
                return self._prompt_init_para['on_abort'](message)
            except Exception:
                _print_str = 'call on_abort exception: %s' % traceback.format_exc()
                if self._prompt_init_para['logger'] is None:
                    print(_print_str)  # 没有日志类，直接输出
                else:
                    self._prompt_init_para['logger'].error(_print_str)
                return ''
        else:
            # 没有处理，返回空字符
            return ''

    def _call_on_exit(self, message=''):
        """
        用户退出处理时执行函数

        @param {string} message='' - 传入的提示信息

        @returns {string} - 返回执行函数的返回结果
        """
        if ('on_exit' in self._prompt_init_para.keys() and
                self._prompt_init_para['on_exit'] is not None):
            try:
                return self._prompt_init_para['on_exit'](message)
            except Exception:
                _print_str = 'call on_exit exception: %s' % traceback.format_exc()
                if self._prompt_init_para['logger'] is None:
                    print(_print_str)  # 没有日志类，直接输出
                else:
                    self._prompt_init_para['logger'].error(_print_str)
                return ''
        else:
            # 没有处理，返回空字符
            return ''

    def _call_on_cmd(self, message='', cmd_str=''):
        """
        执行命令处理

        @param {string} message='' - 输入提示信息
        @param {string} cmd_str='' - 要执行的命令字符串（含参数）

        @returns {string} - 返回执行函数的返回结果
        """
        _cmd = cmd_str
        _cmd_para_str = ''
        _print_str = ''
        if len(_cmd) == 0:
            return ''  # 空字符，不处理
        _first_space_index = _cmd.find(' ')
        if _first_space_index > 0:
            _cmd_para_str = _cmd[_first_space_index + 1:]
            _cmd = _cmd[0: _first_space_index]
        elif _first_space_index == 0:
            _cmd = ''
            _cmd_para_str = cmd_str

        # 查找是否有定义处理函数
        _match_cmd = self._match_cmd_para(cmd=_cmd)
        try:
            if _match_cmd == '':
                # 没有匹配上命令
                if self._prompt_init_para['default_dealfun'] is not None:
                    return self._prompt_init_para['default_dealfun'](message=message,
                                                                     cmd=_cmd,
                                                                     cmd_para=_cmd_para_str)
            else:
                # 匹配到命令
                if self._prompt_init_para['cmd_para'][_match_cmd]['deal_fun'] is not None:
                    return self._prompt_init_para['cmd_para'][_match_cmd]['deal_fun'](
                        message=message, cmd=_match_cmd, cmd_para=_cmd_para_str
                    )
        except Exception:
            _print_str = '_call_on_cmd (cmd[%s] para[%s]) exception: %s' % (
                _cmd, _cmd_para_str, traceback.format_exc()
            )
            if self._prompt_init_para['logger'] is None:
                print(_print_str)  # 没有日志类，直接输出
            else:
                self._prompt_init_para['logger'].error(_print_str)
            _print_str = ''
        return _print_str

    def _async_call_on_cmd(self, message='', cmd_str='', is_print_async_execute_info=True):
        """
        异步模式执行匹配命令，直接调用_call_on_cmd，只是标识为异步模式处理

        @param {string} message='' - 输入提示信息
        @param {string} cmd_str='' - 匹配到的命令
        @param {bool} is_print_async_execute_info=True - 异步执行时是否打印执行信息
        """
        if is_print_async_execute_info:
            _print_str = 'begin execute (message[%s]): cmd[%s]' % (message, cmd_str)
            if self._prompt_init_para['logger'] is None:
                print(_print_str)  # 没有日志类，直接输出
            else:
                self._prompt_init_para['logger'].info(_print_str)
        _print_str = self._call_on_cmd(message=message, cmd_str=cmd_str)
        # 如果有值打印输出
        if len(_print_str) > 0:
            if self._prompt_init_para['logger'] is None:
                print(_print_str)  # 没有日志类，直接输出
            else:
                self._prompt_init_para['logger'].info(_print_str)

        if is_print_async_execute_info:
            _print_str = 'done execute (message[%s]): cmd[%s]' % (message, cmd_str)
            if self._prompt_init_para['logger'] is None:
                print(_print_str)  # 没有日志类，直接输出
            else:
                self._prompt_init_para['logger'].info(_print_str)

    async def _async_cmd_service(self):
        """
        异步模式的命令行循环获取命令线程服务, 标识为异步模式
        获取到一个命令后，将命令放入队列，然后马上处理下一个命令的接收
        """
        while True:
            _print_str = ''
            _cmd_str = ''
            _exit_code = 0
            _message = self._message
            try:
                _cmd_str = await self._prompt_instance.prompt(message=_message, async_=True)
            except KeyboardInterrupt:
                # 用户取消输入
                # 执行on_abort函数
                _exit_code = 1
                _print_str = self._call_on_abort(message=_message)
            except EOFError:
                # 用户退出处理
                # 执行on_exit函数
                _exit_code = 2
                _print_str = self._call_on_exit(message=_message)

            # 如果有值打印输出
            if len(_print_str) > 0:
                if self._prompt_init_para['logger'] is None:
                    print(_print_str)  # 没有日志类，直接输出
                else:
                    self._prompt_init_para['logger'].info(_print_str)

            if _exit_code == 2:
                # 退出获取命令处理
                return

            if len(_cmd_str) > 0:
                # 处理执行函数
                self._async_cmd_queue.put((_message, _cmd_str))

            # 间隔一会，继续下一个处理
            await asyncio.sleep(0.1)

    async def _async_deal_cmd_from_queue(self, is_print_async_execute_info=True):
        """
        异步模式从队列中获取命令行并启动后台线程执行处理， 标识为异步模式

        @param {bool} is_print_async_execute_info - 异步执行时是否打印执行信息
        """
        while True:
            _cmd = tuple()
            try:
                _cmd = self._async_cmd_queue.get(block=False)
            except Exception:
                await asyncio.sleep(1)
                continue
            if len(_cmd) > 0:
                # 开始处理命令，用多线程方式
                _job_thread = threading.Thread(
                    target=self._async_call_on_cmd, args=(
                        _cmd[0], _cmd[1], is_print_async_execute_info)
                )
                # 启动线程
                _job_thread.start()
            await asyncio.sleep(1)

    #############################
    # 实例化的命令行处理 - 公共函数
    #############################

    def __init__(
            self,
            message='CMD>',
            default='',
            **kwargs):
        """
        PromptPlus的构造函数

        @param {string} message='CMD>' - 命令行提示符内容
        @param {string} default='' - 人机交互输入的默认值，直接显示在界面上，可以进行修改后回车输入
        @param {kwargs} kwargs - 扩展参数，分为两部分，第一部分为类自行封装的扩展参数，
            第二部分为python-prompt-toolki的原生prompt参数(自行到到官网查找)
            第一部分扩展参数说明如下：
                cmd_para {cmdpara} - 命令参数字典
                ignore_case {bool} - 匹配命令是否忽略大小写，默认值为False
                default_dealfun {function} - 在命令处理函数字典中没有匹配到的命令，默认执行的处理函数
                    函数定义为fun(message='', cmd='', cmd_para='')，返回值为string，是执行命令函数要输出的内容
                on_abort {function} - 当用户取消输入（Ctrl + C）时执行的函数:
                    函数定义为fun(message='')，返回值为string，是执行命令函数要输出的内容
                on_exit {fun} - 当用户退出（Ctrl + D）时执行的函数，注意如果已输入部分内容，Ctrl + D将不生效:
                    函数定义为fun(message='')，返回值为string，是执行命令函数要输出的内容
                logger {object} - logger 日志对象，服务过程中通过该函数写日志:
                    可以为标准的logging日志库对象，也可以为simple_log对象，但要求对象实现:
                    标准的info、debug、warning、error、critical五个日志方法
                enable_color_set {bool} - 默认True，使用配色集方案:
                    如果选否则自行通过python-prompt-toolkit的方式设定配色方案
                color_set {dict} - 要使用的配色集方案，如果传None则使用系统默认配色集
                enable_cmd_auto_complete {bool} - 默认True，是否启用命令行自动完成提示
                    1、如果启用，则使用命令行自带的completer，实现命令、参数的自动完成功能；
                        不启用则可以自行传入completer、complete_in_thread等原生参数
                    2、可以与complete_while_typing参数共同生效，控制是按tab提示还是输入自动提示
                cmd_auto_complete_slow_time {float} - 默认0，输入后延迟多久提示完成菜单

        """
        self._message = message
        self._default = default
        self._prompt_init_para = self._prompt_default_para.copy()
        self._prompt_init_para.update(kwargs)  # 将传入的参数合并到默认参数中
        self._init_prompt_instance()

    def prompt_once(self, message=None, default='', **kwargs):
        """
        处理一次命令输入

        @param {string} message=None - 命令行提示符内容，如果不传则代表使用实例的默认提示符
        @param {string} default='' - 人机交互输入的默认值，直接显示在界面上，可以进行修改后回车输入
        @param {kwargs} kwargs - python-prompt-toolki的原生prompt参数

        @returns {CResult} - 处理结果，code定义如下:
            0 - 处理成功
            -1 - 出现未知异常
            1 - 用户中断输入（Ctrl + C）
            2 - 用户退出应用（Ctrl + D）
        """
        _result = CResult(code=0, msg=u'成功')
        _print_str = ''
        _message = message
        if message is None:
            _message = self._message

        with ExceptionTools.ignored_cresult(result_obj=_result,
                                            self_log_msg=u'prompt deal exception:'):
            _cmd_str = ''
            # 不确定参数数量，因此用循环方式赋值
            _run_str = u'self._prompt_instance.prompt(message=_message, default=default'
            for _para_name in kwargs:
                if _para_name in self._prompt_para_name_list:
                    _run_str = u'%s, %s=kwargs[\'%s\']' % (_run_str, _para_name, _para_name)
            _run_str = u'%s)' % _run_str

            # 执行获取输入
            try:
                _cmd_str = eval(_run_str)
            except KeyboardInterrupt:
                # 用户取消输入
                _result.code = 1
                _result.msg = u'get abort single(KeyboardInterrupt)'
                _result.error = sys.exc_info()
                _result.trace_str = traceback.format_exc()
                # 执行on_abort函数
                _print_str = self._call_on_abort(message=_message)
            except EOFError:
                # 用户退出处理
                _result.code = 2
                _result.msg = u'get exit single(EOFError)'
                _result.error = sys.exc_info()
                _result.trace_str = traceback.format_exc()
                # 执行on_exit函数
                _print_str = self._call_on_exit(message=_message)

            # 处理输入
            if len(_cmd_str) > 0:
                _print_str = self._call_on_cmd(message=_message, cmd_str=_cmd_str)

        # 打印信息，返回结果
        if len(_print_str) > 0:
            if self._prompt_init_para['logger'] is None:
                print(_print_str)  # 没有日志类，直接输出
            else:
                self._prompt_init_para['logger'].info(_print_str)
        return _result

    # FIXME(黎慧剑): 异步模式，当任务进程有输出时命令行不能固定在最后一行
    def start_prompt_service(
            self,
            tips=u'命令处理服务(输入过程中可通过Ctrl+C取消输入，通过Ctrl+D退出命令行处理服务)',
            is_async=False,
            is_print_async_execute_info=True
    ):
        """
        启动命令行服务(循环获取用户输入并执行相应命令)

        @param {string} tips=u'命令处理服务(输入过程中可通过Ctrl+C取消输入，通过Ctrl+D退出命令行处理服务)'
             - 命令行启动后的提示信息
        @param {bool} is_async=False - 是否异步模式，即在命令执行完成前就可以接收下一个命令输入，
            否则等待命令结束后才接收下一个命令输入
        @param {bool} is_print_async_execute_info=True - 异步模式下是否打印执行信息（开始、结束）
        """
        # 先打印提示信息
        print(tips)
        if not is_async:
            # 非异步模式，按部就班完成处理
            while True:
                _result = self.prompt_once()
                if _result.code == 2:
                    # 退出获取命令处理
                    return
                # 间隔一会，继续下一个处理
                time.sleep(0.1)
        else:
            # 异步模式，通知prompt_toolkit使用asyncio event loop
            use_asyncio_event_loop()
            with patch_stdout():  # 支持重定向屏幕输出，保证命令行一直在最下面
                shell_task = asyncio.ensure_future(self._async_cmd_service())
                background_task = asyncio.gather(
                    self._async_deal_cmd_from_queue(
                        is_print_async_execute_info=is_print_async_execute_info
                    ),
                    return_exceptions=True
                )

                self._loop.run_until_complete(shell_task)
                background_task.cancel()
                self._loop.run_until_complete(background_task)


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
