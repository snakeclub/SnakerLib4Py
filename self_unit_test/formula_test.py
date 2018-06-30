#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : formula_test.py


from formula import *
from simple_log import *
from generic import *
import traceback

__MoudleName__ = 'formula_test'
__MoudleDesc__ = ''
__Version__ = ''
__Author__ = 'snaker'
__Time__ = '2018/2/8'


# 通用的logger
_logger = Logger(conf_file_name=None, logger_name=EnumLoggerName.Console.value, config_type=EnumLoggerConfigType.JSON_STR)


def test_formula_1():
    _source_str = 'select * From test where t.name \tlike \'%fromxxx\' order by name order'
    _split_common = ('\\^', '\r', '\n', ' ', '\t', '\\$')
    _match_list_1 = {
        'select' : (_split_common, _split_common),
        'from': (_split_common, _split_common),
        'where': (_split_common, _split_common),
        'like': (_split_common, _split_common),
        'order': (_split_common, _split_common),
        'by': (_split_common, _split_common),
        'name' : (tuple(), tuple()),
        'na' : (tuple(), tuple())
    }

    _match_result_1 = FormulaTool.search(source_str=_source_str, match_list=_match_list_1, ignore_case=False,
                                         multiple_match=True, sort_oder=EnumFormulaSearchSortOrder.MatchBig)
    """
    for _key in _match_result_1.keys():
        for _key1 in _match_result_1[_key].keys():
            _item = _match_result_1[_key][_key1]
            _logger.info(_key + '：'+StringTools.format_obj_property_str(deal_obj=_item, is_deal_subobj=True))
            _logger.info('check : %s' % _source_str[_item.start_pos : _item.end_pos])
    """

    _match_result_2 = FormulaTool.search(source_str=_source_str, match_list=_match_list_1, ignore_case=True,
                                         multiple_match=False, sort_oder=EnumFormulaSearchSortOrder.ListDesc)

    _logger.info(str(FormulaTool.match_result_to_sorted_list(_match_result_1)))
    _logger.info(str(FormulaTool.match_result_to_sorted_list(_match_result_2)))

def test_formula_2():
    _source_str = 'select {$PY=xxxx{$begin=xx{$PY=eeeee$}x$} from {$end=abc {$abc="kkkaf{$PY=not formula$}dfdf,\\",""haha"$} PY=eeffff bad'
    _string_para = StructFormulaKeywordPara()
    _string_para.is_string = True
    _string_para.has_sub_formula = False
    _string_para.string_ignore_chars = ['\\"', '""']

    _single_para = StructFormulaKeywordPara()
    _single_para.is_single_tag = True

    _end_para = StructFormulaKeywordPara()
    _end_para.end_tags = ['\\$']

    _keywords = {
        'PY' : [
            ['{$PY=', list(), list()],
            ['$}', list(), list()],
            StructFormulaKeywordPara()
        ],
        'abc' : [
            ['{$abc=', list(), list()],
            ['$}', list(), list()],
            StructFormulaKeywordPara()
        ],
        'String' : [
            ['"', list(), list()],
            ['"', list(), list()],
            _string_para
        ],
        'Begin' : [
            ['{$begin=', list(), list()],
            None,
            _single_para
        ],
        'End': [
            ['{$end=', list(), list()],
            None,
            _end_para
        ],
        'End': [
            ['{$end=', list(), list()],
            None,
            _end_para
        ],
        'PYTest': [
            ['PY=ee', list(), list()],
            None,
            _end_para
        ]
    }

    _formula = FormulaTool.analyse_formula(formula_str=_source_str, keywords=_keywords, ignore_case=False)
    _logger.info(StringTools.format_obj_property_str(deal_obj=_formula,is_deal_subobj=True))


def test_formula_3():
    _string_para = StructFormulaKeywordPara()
    _string_para.is_string = True
    _string_para.has_sub_formula = False
    _string_para.string_ignore_chars = ['\\"', '""']

    _single_para = StructFormulaKeywordPara()
    _single_para.is_single_tag = True

    _end_para = StructFormulaKeywordPara()
    _end_para.end_tags = ['\\$']

    _keywords = {
        'PY' : [
            ['{$PY=', list(), list()],
            ['$}', list(), list()],
            StructFormulaKeywordPara()
        ],
        'abc' : [
            ['{$abc=', list(), list()],
            ['$}', list(), list()],
            StructFormulaKeywordPara()
        ],
        'String' : [
            ['"', list(), list()],
            ['"', list(), list()],
            _string_para
        ],
        'Begin' : [
            ['{$begin=', list(), list()],
            None,
            _single_para
        ],
        'End': [
            ['{$end=', list(), list()],
            None,
            _end_para
        ],
        'End': [
            ['{$end=', list(), list()],
            None,
            _end_para
        ],
        'PYTest': [
            ['PY=ee', list(), list()],
            None,
            _end_para
        ]
    }

    # 异常1
    try:
        _source_str = 'select {$PY=xxxx{$begin=xx{$PY=eeeee$}x$} from {$end=abc {$abc="kkkaf{$PY=not formula$}dfdf,\\",""haha$} PY=eeffff bad'
        _formula = FormulaTool.analyse_formula(formula_str=_source_str, keywords=_keywords, ignore_case=False)
    except:
        _logger.debug(str(traceback.format_exc()))

    # 异常2
    try:
        _source_str = 'select {$PY=xxxx{$begin=xx{$PY=eeeee$}x$} from {$end=abc {$abc="kkkaf{$PY=not formula$}dfdf,\\",""haha" PY=eeffff bad'
        _formula = FormulaTool.analyse_formula(formula_str=_source_str, keywords=_keywords, ignore_case=False)
    except:
        _logger.debug(str(traceback.format_exc()))

    # 异常2
    try:
        _source_str = 'select {$PY=xxxx{$begin=xx{$PY=eeeee x$} from {$end=abc {$abc="kkkaf{$PY=not formula$}dfdf,\\",""haha"$} PY=eeffff bad'
        _formula = FormulaTool.analyse_formula(formula_str=_source_str, keywords=_keywords, ignore_case=False)
    except:
        _logger.debug(str(traceback.format_exc()))


def test_formula_4():
    _source_str = 'select {$PY=xxxx{$begin=xx{$PY=eeeee$}x$} from {$end=abc {$abc="kkkaf{$PY=not formula$}dfdf,\\",""haha"$} PY=eeffff bad'
    _string_para = StructFormulaKeywordPara()
    _string_para.is_string = True
    _string_para.has_sub_formula = False
    _string_para.string_ignore_chars = ['\\"', '""']

    _single_para = StructFormulaKeywordPara()
    _single_para.is_single_tag = True

    _end_para = StructFormulaKeywordPara()
    _end_para.end_tags = ['\\$']

    _keywords = {
        'PY' : [
            ['{$PY=', list(), list()],
            ['$}', list(), list()],
            StructFormulaKeywordPara()
        ],
        'abc' : [
            ['{$abc=', list(), list()],
            ['$}', list(), list()],
            StructFormulaKeywordPara()
        ],
        'String' : [
            ['"', list(), list()],
            ['"', list(), list()],
            _string_para
        ],
        'Begin' : [
            ['{$begin=', list(), list()],
            None,
            _single_para
        ],
        'End': [
            ['{$end=', list(), list()],
            None,
            _end_para
        ],
        'End': [
            ['{$end=', list(), list()],
            None,
            _end_para
        ],
        'PYTest': [
            ['PY=ee', list(), list()],
            None,
            _end_para
        ]
    }

    _formula_obj = FormulaTool(
        keywords=_keywords,
        ignore_case=False,
        deal_fun_list={
            'PY': formula_deal_fun_py,
            'String': formula_deal_fun_string,
            'PYTest': formula_deal_fun_test
        },
        default_deal_fun=None
    )

    _formula = _formula_obj.run_formula_as_string(formula_str=_source_str, my_string='self_string', my_list=['self_list'])
    _logger.info(StringTools.format_obj_property_str(deal_obj=_formula,is_deal_subobj=True))

def formula_deal_fun_py(f_obj, my_string='my_string', my_list=['my_list'], **kwargs):
    f_obj.formula_value = '{$$%s===%s===%s$$}' % (my_string, f_obj.content_string, my_list[0])
    # 修改传入参数
    my_string = my_string + str(f_obj.start_pos)
    my_list[0] = my_list[0] + str(f_obj.start_pos)

def formula_deal_fun_string(f_obj, my_string='my_string', **kwargs):
    f_obj.formula_value = '{$$%s===%s$$}' % (my_string, f_obj.content_string)
    # 修改传入参数
    my_string = my_string + str(f_obj.start_pos)

def formula_deal_fun_test(f_obj, my_string='my_string', my_list=['my_list'], **kwargs):
    f_obj.formula_value = '{$$%s===%s===%s$$}' % (my_string, f_obj.content_string, my_list[0])
    


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    DebugTools.set_debug(True)

    #test_formula_1()

    #test_formula_2()

    #test_formula_3()

    test_formula_4()
