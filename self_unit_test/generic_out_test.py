#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : generic_out_test.py


from generic import DebugTools


__MoudleName__ = 'generic_out_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/1/29'

def test_debugtools():
    DebugTools.debug_print("从generic_out_test中的打印信息")

if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))
