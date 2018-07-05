#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys

from pygments.lexers import HtmlLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import PygmentsLexer

sys.path.append("../../snakerlib/")
from snakerlib.prompt_plus import PromptPlus

our_style = Style.from_dict({
    'pygments.comment':   '#888888 bold',
    'pygments.keyword':   '#ff88ff bold',
})


def fun1(prompt_text=''):
    """自定义获取输入后的执行函数"""
    # 在这里填入您的处理
    print('fun1 - your input is: ' + prompt_text)
    return 'deal "' + prompt_text + '" and return'


def fun2(prompt_text=''):
    """自定义获取输入后的执行函数"""
    # 在这里填入您的处理
    print('fun2 - your input is: ' + prompt_text)
    return None


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    result1 = PromptPlus.simple_prompt(message='fun1输入>', deal_fun=fun1)
    print('fun1 return :' + result1 + '\n')

    result2 = PromptPlus.simple_prompt(message='fun2输入>', deal_fun=fun2)
    print('fun2 return :' + result2 + '\n')

    # 使用prompt_toolkit参数
    result3 = PromptPlus.simple_prompt(message='输入HTML代码>', deal_fun=None,
                                       lexer=PygmentsLexer(HtmlLexer), style=our_style)
    print('html return :' + result3 + '\n')
