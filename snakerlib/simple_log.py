#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Filename : simple_log.py

import sys
import os
import os.path
import uuid
import datetime
import configparser
import shutil
import logging
import logging.config
import threading
import json
from enum import Enum
from generic_enum import EnumLogLevel
from generic import FileTools


__MoudleName__ = 'simple_log'
__MoudleDesc__ = '简单日志模块'
__Version__ = '0.9.0'
__Author__ = 'snaker'
__Time__ = '2018/1/17'


# 日志默认配置文件信息
_LOGGER_DEFAULT_CONF_STR = u'''###############################################
[loggers]
keys=root,Console,File,ConsoleAndFile

[logger_root]
level=DEBUG
handlers=

[logger_Console]
level=DEBUG
handlers=ConsoleHandler

[logger_File]
level=INFO
handlers=FileHandler
qualname=File
propagate=0

[logger_ConsoleAndFile]
level=DEBUG
handlers=ConsoleHandler,FileHandler
qualname=ConsoleAndFile
propagate=0

###############################################
[handlers]
keys=ConsoleHandler,FileHandler

[handler_ConsoleHandler]
class=StreamHandler
level=DEBUG
formatter=simpleFormatter
args=(sys.stdout,)

[handler_FileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=simpleFormatter
args=('{$log_file_path$}', 'a', 10*1024*1024, 1000)

###############################################
[formatters]
keys=simpleFormatter
[formatter_simpleFormatter]
format=[%(asctime)s][%(levelname)s][PID:%(process)d][TID:%(thread)d]%(message)s
datefmt=
'''


_LOGGER_HELP_CONF_STR = u'''###############################################
##定义logger模块，root是父类，必需存在的，其它的是自定义。
##logging.getLogger(NAME)便相当于向logging模块注册了一种日志打印
##[logger_xxxx] logger_模块名称
##level     级别，级别有DEBUG、INFO、WARNING、ERROR、CRITICAL
##handlers  处理类，可以有多个，用逗号分开
##qualname  logger名称，应用程序通过 logging.getLogger获取。对于不能获取的名称，则记录到root模块
##propagate 是否继承父类的log信息，0:否 1:是
###############################################
[loggers]
keys=root,Console,File,ConsoleAndFile

[logger_root]
level=DEBUG
handlers=ConsoleHandler

[logger_Console]
level=DEBUG
handlers=ConsoleHandler

[logger_File]
handlers=FileHandler
qualname=File
propagate=0

[logger_ConsoleAndFile]
handlers=ConsoleHandler,FileHandler
qualname=ConsoleAndFile
propagate=0

###############################################
##logging.StreamHandler
###使用这个Handler可以向类似与sys.stdout或者sys.stderr的任何文件对象(file object)输出信息。它的构造函数是：
###StreamHandler([strm])
###其中strm参数是一个文件对象。默认是sys.stderr
#
##logging.FileHandler
###和StreamHandler类似，用于向一个文件输出日志信息。不过FileHandler会帮你打开这个文件。它的构造函数是：
###FileHandler(filename[,mode])
###filename是文件名，必须指定一个文件名。
###mode是文件的打开方式。参见Python内置函数open()的用法。默认是’a'，即添加到文件末尾。
#
##logging.handlers.RotatingFileHandler
###这个Handler类似于上面的FileHandler，但是它可以管理文件大小。当文件达到一定大小之后，
###    它会自动将当前日志文件改名，然后创建 一个新的同名日志文件继续输出。
###    比如日志文件是chat.log。当chat.log达到指定的大小之后，RotatingFileHandler自动把文件改名为chat.log.1,
###    不过，如果chat.log.1已经存在，会先把chat.log.1重命名为chat.log.2。。。
###    最后重新创建 chat.log，继续输出日志信息。它的构造函数是：
###RotatingFileHandler( filename[, mode[, maxBytes[, backupCount]]])
###其中filename和mode两个参数和FileHandler一样。
###maxBytes用于指定日志文件的最大文件大小。如果maxBytes为0，意味着日志文件可以无限大，
###    这时上面描述的重命名过程就不会发生。
###backupCount用于指定保留的备份文件的个数。比如，如果指定为2，当上面描述的重命名过程发生时，
###    原有的chat.log.2并不会被更名，而是被删除。
###############################################
[handlers]
keys=ConsoleHandler,FileHandler

[handler_ConsoleHandler]
class=StreamHandler
level=DEBUG
formatter=simpleFormatter
args=(sys.stdout,)

[handler_FileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=simpleFormatter
args=('myapp.log', 'a', 10*1024*1024, 1000)

###############################################
#format: 指定输出的格式和内容，format可以输出很多有用信息，如上例所示:
# %(levelno)s: 打印日志级别的数值
# %(levelname)s: 打印日志级别名称
# %(pathname)s: 打印当前执行程序的路径，其实就是sys.argv[0]
# %(filename)s: 打印当前执行程序名
# %(funcName)s: 打印日志的当前函数
# %(lineno)d: 打印日志的当前行号
# %(asctime)s: 打印日志的时间
# %(thread)d: 打印线程ID
# %(threadName)s: 打印线程名称
# %(process)d: 打印进程ID
# %(message)s: 打印日志信息
###############################################
[formatters]
keys=simpleFormatter

[formatter_simpleFormatter]
format=[%(asctime)s][%(levelname)s][PID:%(process)d][TID:%(thread)d]%(message)s
datefmt=
'''


# JSON格式的日志配置文件默认字符串，需注意disable_existing_loggers的设置，如果为true会导致多个logger实例有被屏蔽的问题
_LOGGER_DEFAULT_JSON_STR = u'''{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simpleFormatter": {
            "format": "[%(asctime)s][%(levelname)s][PID:%(process)d][TID:%(thread)d]%(message)s"
        }
    },

    "handlers": {
        "ConsoleHandler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simpleFormatter",
            "stream": "ext://sys.stdout"
        },

        "FileHandler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simpleFormatter",
            "filename": "{$log_file_path$}",
            "maxBytes": 10485760,
            "backupCount": 1000,
            "encoding": "utf8"
        }
    },
    
    "loggers": {
        "Console": {
            "level": "DEBUG",
            "handlers": ["ConsoleHandler"]
        },
        
        "File": {
            "level": "INFO",
            "handlers": ["FileHandler"],
            "propagate": "no"
        },
        
        "ConsoleAndFile": {
            "level": "DEBUG",
            "handlers": ["ConsoleHandler", "FileHandler"],
            "propagate": "no"
        }
    },

    "root": {
        "level": "DEBUG",
        "handlers": []
    }
}
'''

# JSON格式的日志终端输出默认字符串，需注意disable_existing_loggers的设置，如果为true会导致多个logger实例有被屏蔽的问题
_LOGGER_DEFAULT_JSON_CONSOLE_STR = u'''{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simpleFormatter": {
            "format": "[%(asctime)s][%(levelname)s][PID:%(process)d][TID:%(thread)d]%(message)s"
        }
    },

    "handlers": {
        "ConsoleHandler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simpleFormatter",
            "stream": "ext://sys.stdout"
        }
    },

    "loggers": {
        "Console": {
            "level": "DEBUG",
            "handlers": ["ConsoleHandler"]
        }
    },

    "root": {
        "level": "DEBUG",
        "handlers": []
    }
}
'''


class EnumLoggerName(Enum):
    """
    @enum 输出日志类型
    @enumName EnumLoggerName
    @enumDescription 用于编码时快捷获取输出日志类型字符内容

    """
    root = 'root'  # 默认的logger，输出到控制台
    Console = 'Console'  # 输出到控制台
    File = 'File'  # 输出到文件
    ConsoleAndFile = 'ConsoleAndFile'  # 同时输出到屏幕和文件


class EnumLoggerConfigType(Enum):
    """
    @enum 日志配置方式
    @enumName EnumLoggerConfigType
    @enumDescription 日志配置方式

    """
    JSON_FILE = 'JSON_FILE'  # JSON格式配置文件
    INI_FILE = 'INI_FILE'  # INI格式配置文件
    JSON_STR = 'JSON_STR'  # JSON字符串


class Logger(object):
    """
    @class 日志输出类
    @className Logger
    @classGroup
    @classVersion 0.9.0
    @classDescription 封装Python自带logging库的日志类，简化日志类的配置和输出
    
    @classExample {Python} 使用说明:
        使用说明：
        1、import snakerlib.simple_log

        2、程序本地创建“logger.conf”文件，修改配置文件为自己希望的内容
        注意：conf文件中请不要含中文内容，原因是目前的程序对中文处理存在转码问题（问题待解决）
        主要修改的参数如下：
        （1）[handler_FileHandler]下的args参数：
            第1个参数是日志文件名（可以带路径），日志程序会自动在扩展名前补充日期；
            第2个参数固定为追加模式；
            第3个参数为自动转存的文件大小，单位为byte；
            第4个参数为自动转存时，超过多少个文件后以覆盖方式记录（不会再新增）
        （2）[formatters]下的format参数，该参数定义了日志的格式：
            需注意由于对日志类的调用进行了封装，format参数中的%(message)s和%(funcName)s并不准确（获取到的是日志模块的）
            应使用构造函数的is_print_file_name=True, is_print_fun_name=True来输出程序名和函数名

        3、各个标签下的level级别，修改为：DEBUG、INFO、WARNING、ERROR、CRITICAL中的一个

        4、使用方式
            ## 实例化类，需指定要读取的logger.conf文件地址，以及输出方式：
            ##  root - 输出屏幕 ,File - 输出到文件 , ConsoleAndFile - 同时输出到屏幕和文件
            s = simple_log.Logger(r"D:\工作目录\自主研发\Python\SimpleLog\logger.conf","ConsoleAndFile")
            ## 记录日志，第1个参数是日志级别，第2个参数是日志内容
            s.write_log(EnumLogLevel.INFO,"日志内容")

        5、特别注意，Python默认的FileHandler是线程安全的（支持多线程），但不是进程安全（不支持启动多进程记录同一日志），
        如果需要支持多进程，需要使用第三方的FileHandler，使用方式如下：
        （1）pip install ConcurrentLogHandler
        （2）修改日志配置文件的class=handlers.RotatingFileHandler为class=handlers.ConcurrentRotatingFileHandler

        6、注意：该logger类是全局共享的，即如果loggername、handler的配置名一样，
            建立多个logger且进行调整的情况下会互相干扰，因此如果需要实例化多个logger，则建议配置名和handler名有所区分

    """

    # 私有变量
    __file_date = "20170101"  # 日志文件的日期
    __conf_file_name = "logger.conf"  # 日志配置文件的路径/或配置字符串
    __config_type = EnumLoggerConfigType.JSON_FILE
    __conf_tmp_file_name = "logger.conf.tmp20170101"  # 复制的日志文件临时路径
    __logger_name = "root"  # 输出日志类型，root - 输出屏幕 ,File - 输出到文件 , ConsoleAndFile - 同时输出到屏幕和文件
    __work_path = ""  # 工作路径
    __logfile_path = ""  # 日志文件的路径（含文件名）
    __logger = None  # 日志对象
    __thread_lock = threading.Lock()  # 保证多线程访问的锁
    __is_print_file_name = True  # 是否输出文件名
    __is_print_fun_name = True  # 是否输出函数名
    __json_config = None  # json格式的配置信息
    __is_create_logfile_by_day = True  # 是否按天生成新的日志文件
    __call_level = 0  # 调用write_log函数输出文件名和函数名的层级,0代表获取直接调用函数；1代表获取直接调用函数的上一级

    @property
    def base_logger(self):
        """
        @property {get} 获取底层的logger对象
        @propertyName base_logger
        @propertyDescription 获取底层的logger对象(logging.getLogger()对象)

        """
        return self.__logger

    def __init__(self, conf_file_name='logger.json', logger_name='root', logfile_path='',
                 config_type=EnumLoggerConfigType.JSON_FILE, auto_create_conf=True,
                 is_print_file_name=True, is_print_fun_name=True, is_create_logfile_by_day=True,
                 call_level=0):
        """
        @fun 日志类构造函数
        @funName __init__
        @funGroup
        @funVersion
        @funDescription 初始化日志类，生成日志对象实例
        
        @funParam {string} conf_file_name 日志配置文件路径和文件名:
            默认为'logger.conf'，如果找不到配置文件本函数会自动创带默认设置的配置文件
            如果日志类型为EnumLoggerConfigType.JSON_STR，则该参数为JSON配置信息，如果为None则自动取默认配置值
        @funParam {string} logger_name 输出日志类型，根据conf配置可以新增自定义类型，默认为'root':
            root-输出到屏幕,File-输出到文件,ConsoleAndFile-同时输出到屏幕和文件
            如果没有自定义日志类型，可以使用EnumLoggerName枚举值,用法为：EnumLoggerName.root.value
        @funParam {string} logfile_path 如果已有配置文件的情况该参数无效
            日志输出文件的路径（含文件名），''代表使用'log/程序名.log'
        @funParam {EnumLoggerConfigType} config_type 日志配置方式
        @funParam {bool} auto_create_conf 是否自动创建配置文件（找不到指定的配置文件时），默认为True
        @funParam {bool} is_print_file_name 是否输出文件名，默认为True
        @funParam {bool} is_print_fun_name 是否输出函数名，默认为True
        @funParam {bool} is_create_logfile_by_day 是否按天生成新的日志文件，默认为True
        @funParam {int} call_level 调用write_log函数输出文件名和函数名的层级:
            0代表获取直接调用函数；1代表获取直接调用函数的上一级
        
        @funExample {Python} 参考示例:
            log = Logger(conf_file_name='/root/logger.conf', logger_name='ConsoleAndFile',
                        logfile_path="appname.log', auto_create_conf=True)
            log.write_log(log_level=EnumLogLevel.INFO, log_str='输出日志内容'):
        
        """
        # 设置默认值
        self.__file_date = ''
        self.__conf_file_name = conf_file_name
        if config_type == EnumLoggerConfigType.JSON_STR and conf_file_name is None:
            self.__conf_file_name = _LOGGER_DEFAULT_JSON_CONSOLE_STR
        self.__logger_name = logger_name
        self.__logfile_path = logfile_path
        self.__config_type = config_type
        self.__work_path = os.path.realpath(sys.path[0])
        if config_type in (EnumLoggerConfigType.INI_FILE, EnumLoggerConfigType.JSON_FILE):
            _path_dir, _path_file_name = os.path.split(os.path.realpath(self.__conf_file_name))
            self.__conf_tmp_file_name = (self.__work_path + os.sep + _path_file_name + '.tmp'
                                     + self.__file_date + str(uuid.uuid4()))
        self.__is_print_file_name = is_print_file_name
        self.__is_print_fun_name = is_print_fun_name
        self.__is_create_logfile_by_day = is_create_logfile_by_day
        self.__call_level = call_level

        if auto_create_conf and config_type in (EnumLoggerConfigType.JSON_FILE, EnumLoggerConfigType.INI_FILE):
            # 判断文件是否存在，如果不存在则按默认值创建文件
            self.__create_conf_file()

        # 如果是JSON格式，先加载到对象
        if self.__config_type == EnumLoggerConfigType.JSON_STR:
            self.__json_config = json.loads(self.__conf_file_name)
        elif self.__config_type == EnumLoggerConfigType.JSON_FILE:
            with open(self.__conf_file_name, 'rt') as f:
                self.__json_config = json.load(f)

        # 如果要求按日记录日志，则修改配置中的文件名，加上日期
        if self.__is_create_logfile_by_day:
            self.__check_log_date()
        else:
            # 直接使用默认的配置
            if self.__config_type == EnumLoggerConfigType.INI_FILE:
                shutil.copyfile(self.__conf_file_name, self.__conf_tmp_file_name)
            # 生效配置
            self.__set_logger_config()

    def __del__(self):
        """
        @fun 析构函数
        @funName __del__
        @funGroup
        @funVersion
        @funDescription 当删除日志对象时，删除对应的日志类实例
        
        """
        # 删除对象
        if self.__logger is not None:
            del self.__logger
            self.__logger = None

    @staticmethod
    def __get_date_str(dt):
        """
        @fun 获取yyyyMMdd格式的日期函数（内部函数）
        @funName __get_date_str
        @funGroup
        @funVersion
        @funDescription 将datetime转换为yyyyMMdd的字符串格式
        
        @funParam {datetime} dt 要处理的日期变量
        
        @funReturn {string} 转换后的日期字符串；如果传入的不是datetime格式，返回""

        """
        if isinstance(dt, datetime.datetime):
            return dt.strftime('%Y%m%d')
        else:
            return ""

    @staticmethod
    def __get_call_fun_frame(call_level):
        """
        @fun 获取指定层级的调用函数框架（fake_frame）
        @funName __get_call_fun_frame
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 获取指定层级的调用函数框架啊，从当前调用函数开始往逐级向上获取

        @funParam {int} call_level 要获取的函数名所属层级:
            -1 - 返回函数自身框架
            0 - 返回调用本函数的函数框架
            1 - 返回调用本函数的函数的上1级函数框架
            n - 返回调用本函数的函数的上n级函数框架

        @funReturn {fake_frame} 返回指定层级函数的框架（fake_frame），可以通过fake_frame.f_code获取代码相关信息

        """
        _ret_frame = sys._getframe()  # 要返回的函数框架
        if call_level < 0:
            return _ret_frame
        _index = 0
        # 循环获取上一级函数的框架
        while _index <= call_level:
            _ret_frame = _ret_frame.f_back
            _index = _index + 1
        return _ret_frame

    def __create_conf_file(self):
        """
        @fun 自动创建日志配置文件（内部函数）
        @funName __create_conf_file
        @funGroup
        @funVersion
        @funDescription 检查类中指定的配置文件是否存在，如果不存在则进行创建
        
        """
        _path_dir, _path_file_name = os.path.split(os.path.realpath(self.__conf_file_name))
        if not os.path.exists(_path_dir):
            # 路径不存在
            os.makedirs(_path_dir)

        if not os.path.exists(self.__conf_file_name):
            # 文件不存在，如果日志文件路径为空，则重新设置日志文件路径为工作目录下的log\发起模块名.log
            _temp_logfile_path = self.__logfile_path
            if self.__logfile_path == '':
                _temp_logfile_path = 'log/' + FileTools.get_exefile_name_no_ext() + '.log'

            # 文件不存在，创建文件并写入特殊值
            with open(self.__conf_file_name, 'w+', encoding='utf-8') as f:
                if self.__config_type == EnumLoggerConfigType.INI_FILE:
                    f.write(_LOGGER_DEFAULT_CONF_STR.replace('{$log_file_path$}', _temp_logfile_path))
                else:
                    f.write(_LOGGER_DEFAULT_JSON_STR.replace('{$log_file_path$}', _temp_logfile_path))

    def __create_log_dir(self):
        """
        @fun 遍历对应logger的配置并创建日志路径
        @funName __create_log_dir
        @funGroup
        @funVersion
        @funDescription 遍历对应logger的配置并创建日志路径

        """
        if self.__config_type == EnumLoggerConfigType.INI_FILE:
            # conf配置文件
            _config = configparser.ConfigParser()
            try:
                _config.read(self.__conf_tmp_file_name)
                _loggers = _config.get('loggers', 'keys').split(',')
                for _logger_name in _loggers:
                    _handlers = _config.get('logger_%s' % _logger_name, 'handlers').split(',')
                    for _handler_name in _handlers:
                        if _config.get('handler_%s' % _handler_name, 'class').find('FileHandler') >= 0:
                            _file_args = _config.get('handler_%s' % _handler_name, 'args')
                            _dot_index = _file_args.find(',')
                            _temp_file_path = _file_args[2:_dot_index - 1].strip(' (,\'"')
                            _temp_path = os.path.split(os.path.realpath(_temp_file_path))[0]
                            if not os.path.exists(_temp_path):
                                FileTools.create_dir(_temp_path)
            finally:
                del _config
        else:
            # JSON，要检索所有的handler进行处理
            for _handler_name in self.__json_config['handlers'].keys():
                if 'filename' in self.__json_config['handlers'][_handler_name].keys():
                    _temp_path = os.path.split(
                        os.path.realpath(self.__json_config['handlers'][_handler_name]['filename'])
                    )[0]
                    if not os.path.exists(_temp_path):
                        FileTools.create_dir(_temp_path)

    def __change_filepath_to_config(self, file_path='', handler_name=None, add_date_str=None):
        """
        @fun 修改日志配置中的文件路径（含文件名）
        @funName __change_filepath_to_config
        @funGroup
        @funVersion
        @funDescription 遍历并修改日志配置中的文件路径，如果是JSON，只修改内存的对象即可:
            如果是INI文件，则创建临时配置文件并进行修改

        @funParam {string} file_path 要修改的文件路径（含文件名）
        @funParam {string} handler_name 指定要修改的handler名称，如果不传代表遍历所有并处理
        @funParam {string} add_date_str 基于原配置增加日期字符串，如果传入该值，file_path将不再生效

        """
        if self.__config_type == EnumLoggerConfigType.INI_FILE:
            # conf配置文件，创建临时文件并修改临时文件的配置
            shutil.copyfile(self.__conf_file_name, self.__conf_tmp_file_name)
            _config = configparser.ConfigParser()
            try:
                _config.read(self.__conf_tmp_file_name)
                _handlers = _config.get('logger_%s' % self.__logger_name, 'handlers').split(',')
                for _handler_name in _handlers:
                    if _config.get('handler_%s' % _handler_name, 'class').find('FileHandler') >= 0:
                        if handler_name is None or handler_name == _handler_name:
                            _file_args = _config.get('handler_%s' % _handler_name, 'args')
                            _dot_index = _file_args.find(',')
                            if add_date_str is not None:
                                _temp_file_path = _file_args[2:_dot_index - 1].strip(' (,\'"')
                                _dot_index = _temp_file_path.rfind('.')
                                if _dot_index == -1:
                                    _temp_file_path = _temp_file_path + add_date_str
                                else:
                                    _temp_file_path = (_temp_file_path[0:_dot_index] + add_date_str
                                                       + _temp_file_path[_dot_index:])
                                # 修改配置
                                _file_args = "('%s'%s" % (_temp_file_path, _file_args[_dot_index:])
                            else:
                                _file_args = "('%s'%s" % (file_path, _file_args[_dot_index:])
                            _config.set('handler_%s' % _handler_name, 'args', _file_args)
                # 写回临时文件
                _file = open(self.__conf_tmp_file_name, 'w', encoding='utf-8')
                _config.write(_file)
                _file.close()
            finally:
                del _config
        else:
            # JSON，根据遍历配置找到对应的handler进行修改
            _ori_json_config = None
            if add_date_str is not None:
                if self.__config_type == EnumLoggerConfigType.JSON_STR:
                    _ori_json_config = json.loads(self.__conf_file_name)
                elif self.__config_type == EnumLoggerConfigType.JSON_FILE:
                    with open(self.__conf_file_name, 'rt') as f:
                        _ori_json_config = json.load(f)
            _handlers = []
            if self.__logger_name == 'root':
                _handlers = self.__json_config['root']['handlers']
            else:
                _handlers = self.__json_config['loggers'][self.__logger_name]['handlers']
            # 修改文件路径
            for _handler_name in _handlers:
                if 'filename' in self.__json_config['handlers'][_handler_name].keys():
                    if handler_name is None or handler_name == _handler_name:
                        if add_date_str is not None:
                            _temp_file_path = _ori_json_config['handlers'][_handler_name]['filename']
                            _dot_index = _temp_file_path.rfind('.')
                            if _dot_index == -1:
                                _temp_file_path = _temp_file_path + add_date_str
                            else:
                                _temp_file_path = (_temp_file_path[0:_dot_index] + add_date_str
                                                   + _temp_file_path[_dot_index:])
                            # 修改配置
                            self.__json_config['handlers'][_handler_name]['filename'] = _temp_file_path
                        else:
                            self.__json_config['handlers'][_handler_name]['filename'] = file_path

    def __set_logger_config(self):
        """
        @fun 通过临时配置文件生成logging日志实例（内部函数）
        @funName __set_logger_config
        @funGroup
        @funVersion
        @funDescription 通过临时配置文件生成logging日志实例

        """
        # 根据新参数创建目录
        self.__create_log_dir()
        # 重新设置logger的参数
        if self.__logger is not None:
            del self.__logger
        if self.__config_type == EnumLoggerConfigType.INI_FILE:
            # INI配置文件方式
            try:
                logging.config.fileConfig(self.__conf_tmp_file_name)
            finally:
                os.remove(self.__conf_tmp_file_name)
        else:
            # JSON配置方式
            logging.config.dictConfig(self.__json_config)
        # 重新获取logger
        self.__logger = logging.getLogger(self.__logger_name)

    def __check_log_date(self):
        """
        @fun 检查并变更日志文件日期（内部函数）
        @funName __check_log_date
        @funGroup
        @funVersion
        @funDescription 检查当前日期是否已发生变更，如果已发生变更，则修改临时配置文件并重新设置日志实例

        """
        # 检查当前日期是否与日志日期一致，如果不是，则重新装载文件配置
        if self.__is_create_logfile_by_day:
            try:
                self.__thread_lock.acquire()
                _now_date = self.__get_date_str(datetime.datetime.now())
                if _now_date != self.__file_date:
                    self.__file_date = _now_date
                    # 修改日志配置
                    self.__change_filepath_to_config(add_date_str=self.__file_date)
                    # 生效日志类
                    self.__set_logger_config()
            finally:
                self.__thread_lock.release()

    def write_log(self, log_level=EnumLogLevel.INFO, log_str='', call_level=None):
        """
        @fun 输出日志
        @funName write_log
        @funGroup
        @funVersion
        @funDescription 通过日志实例输出日志内容

        @funParam {EnumLogLevel} log_level 输出日志的级别
        @funParam {string} log_str 要输出的日志内容
        @funParam {int} call_level 日志中输出的函数名（文件名）所属层级，如果传入None代表使用构造函数默认的参数:
            0 - 输出调用本函数的函数名（文件名）
            1 - 输出调用本函数的函数的上1级函数的函数名（文件名）
            n - 输出调用本函数的函数的上n级函数的函数名（文件名）

        @funExample {Python}  参考示例:
            log = Logger(conf_file_name="/root/logger.conf",logger_name="ConsoleAndFile",
                logfile_path="appname.log",auto_create_conf=True)
            log.write_log(log_level=EnumLogLevel.ERROR,log_str="输出日志内容"):
        
        """
        self.__check_log_date()  # 检查日志文件是否要翻日
        # 处理文件名和函数名
        _call_level = self.__call_level
        if call_level is not None:
            _call_level = call_level
        _frame = Logger.__get_call_fun_frame(call_level=_call_level+1)
        _path_filename = ''
        _fun_name = ''
        if self.__is_print_file_name:
            _path_dir, _path_filename = os.path.split(os.path.realpath(_frame.f_code.co_filename))
            _path_filename = '[%s]' % _path_filename
        if self.__is_print_fun_name:
            _fun_name = '[%s]' % _frame.f_code.co_name
        # 组成日志信息
        _logstr = '%s%s%s' % (_path_filename, _fun_name, log_str)
        if log_level == EnumLogLevel.DEBUG:
            self.__logger.debug(_logstr)
        elif log_level == EnumLogLevel.WARNING:
            self.__logger.warning(_logstr)
        elif log_level == EnumLogLevel.ERROR:
            self.__logger.error(_logstr)
        elif log_level == EnumLogLevel.CRITICAL:
            self.__logger.critical(_logstr)
        else:
            self.__logger.info(_logstr)

    def debug(self, log_str='', call_level=None):
        """
        @fun 记录DEBUG级别的日志
        @funName debug
        @funGroup
        @funVersion
        @funDescription 用于兼容logging的写日志模式提供的方法

        @funParam {string} log_str 要输出的日志内容
        @funParam {int} call_level 日志中输出的函数名（文件名）所属层级，如果传入None代表使用构造函数默认的参数:
            0 - 输出调用本函数的函数名（文件名）
            1 - 输出调用本函数的函数的上1级函数的函数名（文件名）
            n - 输出调用本函数的函数的上n级函数的函数名（文件名）

        """
        # 处理调用函数的层级
        _call_level = self.__call_level
        if call_level is not None:
            _call_level = call_level
        self.write_log(log_level=EnumLogLevel.DEBUG, log_str=log_str, call_level=_call_level+1)

    def warning(self, log_str='', call_level=None):
        """
        @fun 记录WARNING级别的日志
        @funName warning
        @funGroup
        @funVersion
        @funDescription 用于兼容logging的写日志模式提供的方法

        @funParam {string} log_str 要输出的日志内容
        @funParam {int} call_level 日志中输出的函数名（文件名）所属层级，如果传入None代表使用构造函数默认的参数:
            0 - 输出调用本函数的函数名（文件名）
            1 - 输出调用本函数的函数的上1级函数的函数名（文件名）
            n - 输出调用本函数的函数的上n级函数的函数名（文件名）

        """
        # 处理调用函数的层级
        _call_level = self.__call_level
        if call_level is not None:
            _call_level = call_level
        self.write_log(log_level=EnumLogLevel.WARNING, log_str=log_str, call_level=_call_level+1)

    def error(self, log_str='', call_level=None):
        """
        @fun 记录ERROR级别的日志
        @funName error
        @funGroup
        @funVersion
        @funDescription 用于兼容logging的写日志模式提供的方法

        @funParam {string} log_str 要输出的日志内容
        @funParam {int} call_level 日志中输出的函数名（文件名）所属层级，如果传入None代表使用构造函数默认的参数:
            0 - 输出调用本函数的函数名（文件名）
            1 - 输出调用本函数的函数的上1级函数的函数名（文件名）
            n - 输出调用本函数的函数的上n级函数的函数名（文件名）

        """
        # 处理调用函数的层级
        _call_level = self.__call_level
        if call_level is not None:
            _call_level = call_level
        self.write_log(log_level=EnumLogLevel.ERROR, log_str=log_str, call_level=_call_level+1)

    def critical(self, log_str='', call_level=None):
        """
        @fun 记录CRITICAL级别的日志
        @funName critical
        @funGroup
        @funVersion
        @funDescription 用于兼容logging的写日志模式提供的方法

        @funParam {string} log_str 要输出的日志内容
        @funParam {int} call_level 日志中输出的函数名（文件名）所属层级，如果传入None代表使用构造函数默认的参数:
            0 - 输出调用本函数的函数名（文件名）
            1 - 输出调用本函数的函数的上1级函数的函数名（文件名）
            n - 输出调用本函数的函数的上n级函数的函数名（文件名）

        """
        # 处理调用函数的层级
        _call_level = self.__call_level
        if call_level is not None:
            _call_level = call_level
        self.write_log(log_level=EnumLogLevel.CRITICAL, log_str=log_str, call_level=_call_level+1)

    def info(self, log_str='', call_level=None):
        """
        @fun 记录INFO级别的日志
        @funName info
        @funGroup
        @funVersion
        @funDescription 用于兼容logging的写日志模式提供的方法

        @funParam {string} log_str 要输出的日志内容
        @funParam {int} call_level 日志中输出的函数名（文件名）所属层级，如果传入None代表使用构造函数默认的参数:
            0 - 输出调用本函数的函数名（文件名）
            1 - 输出调用本函数的函数的上1级函数的函数名（文件名）
            n - 输出调用本函数的函数的上n级函数的函数名（文件名）

        """
        # 处理调用函数的层级
        _call_level = self.__call_level
        if call_level is not None:
            _call_level = call_level
        self.write_log(log_level=EnumLogLevel.INFO, log_str=log_str, call_level=_call_level+1)

    def change_logger_name(self, logger_name):
        """
        @fun 修改输出日志类型配置
        @funName change_logger_name
        @funGroup
        @funVersion
        @funDescription 修改输出日志类型配置
        
        @funParam {string} logger_name 输出日志类型，默认为'root':
            root-输出到屏幕,File-输出到文件,ConsoleAndFile-同时输出到屏幕和文件
            如果没有自定义日志类型，可以使用EnumLoggerName枚举值,用法为：EnumLoggerName.root.value
        
        """
        self.__logger_name = logger_name
        if self.__is_create_logfile_by_day:
            self.__file_date = ''
            self.__check_log_date()
        else:
            try:
                self.__thread_lock.acquire()
                # 重新装载文件配置
                if self.__config_type == EnumLoggerConfigType.INI_FILE:
                    shutil.copyfile(self.__conf_file_name, self.__conf_tmp_file_name)
                # 生效配置
                self.__set_logger_config()
            finally:
                self.__thread_lock.release()

    def set_level(self, log_level):
        """
        @fun 设置日志对象的日志级别（同时修改loggername及handler的级别）
        @funName set_level
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 设置日志对象的日志级别（同时修改loggername及handler的级别）

        @funParam {EnumLogLevel} log_level 日志级别

        """
        self.__logger.setLevel(log_level.value)
        for _handler in self.__logger.handlers:
            _handler.setLevel(log_level.value)

    def set_logger_level(self, log_level):
        """
        @fun 动态设置日志logger的输出级别（只影响loggername的级别，不影响handler的级别）
        @funName set_logger_level
        @funGroup
        @funVersion
        @funDescription 运行期间设置所有handler的日志输出级别

        @funParam {EnumLogLevel} log_level 日志级别

        """
        self.__logger.setLevel(log_level.value)

    @staticmethod
    def set_handler_log_level(handler, log_level):
        """
        @fun 设置指定handler的日志输出级别
        @funName set_handler_log_level
        @funGroup
        @funVersion
        @funDescription 设置指定handler的日志输出级别

        @funParam {obj} handler 要设置的handler对象，可通过_logger.base_logger.handlers[i]获取
        @funParam {EnumLogLevel} log_level 日志级别

        """
        handler.setLevel(log_level.value)

    def set_logger_formater(self, format_str=None, is_print_file_name=None, is_print_fun_name=None):
        """
        @fun 动态设置输出日志格式
        @funName set_logger_formater
        @funGroup 所属分组
        @funVersion 版本
        @funDescription 动态设置输出日志格式

        @funParam {string} format_str 输出格式字符串，参考conf文件中的format格式，如果为None代表不修改
        @funParam {bool} is_print_file_name 是否输出文件名，如果为None代表不修改
        @funParam {bool} is_print_fun_name 是否输出函数名，如果为None代表不修改

        """
        if is_print_file_name is not None:
            self.__is_print_file_name = is_print_file_name
        if is_print_fun_name is not None:
            self.__is_print_fun_name = is_print_fun_name
        if format_str is not None:
            _formater = logging.Formatter(format_str)
            for _handler in self.__logger.handlers:
                _handler.setFormatter(_formater)


if __name__ == "__main__":
    """
    # 当程序自己独立运行时执行的操作
    """
    # 打印版本信息
    print('''模块名：%s  -  %s
    作者：%s
    更新日期：%s
    版本：%s''' % (__MoudleName__, __MoudleDesc__, __Author__, __Time__, __Version__))

    if len(sys.argv) > 1:
        _cmd = sys.argv[1].upper()
    else:
        _cmd = ''
        print('''帮助命令：python %s.py CONF/DEMO
    CONF - 配置文件说明
    DEMO - 演示代码执行''' % (__MoudleName__))

    if _cmd == 'DEMO':
        # 执行实例代码
        _logroot = Logger(conf_file_name='logger.json', logger_name=EnumLoggerName.root.value, auto_create_conf=True,
                          is_create_logfile_by_day=False, config_type=EnumLoggerConfigType.JSON_FILE)
        _logroot.write_log(EnumLogLevel.INFO, '仅输出界面信息 - INFO')
        _logroot.write_log(EnumLogLevel.DEBUG, '仅输出界面信息 - DEBUG')
        _logroot.debug("haha")

        _logroot.change_logger_name(EnumLoggerName.ConsoleAndFile.value)
        _logroot.set_logger_level(EnumLogLevel.DEBUG)
        _logroot.set_logger_formater(format_str='[%(asctime)s]%(message)s',
                                     is_print_file_name=False, is_print_fun_name=False)
        _logroot.write_log(EnumLogLevel.INFO, "输出界面和文件信息 - INFO")
        _logroot.write_log(EnumLogLevel.DEBUG, "输出界面和文件信息 - DEBUG")

        # 停止日志服务
        del _logroot
    elif _cmd == 'CONF':
        # 展示配置文件说明
        print('\r\n 配置文件logger.conf的说明如下：')
        print(_LOGGER_HELP_CONF_STR)
