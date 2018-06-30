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


"""The setup.py file for Python snakerlib."""

from setuptools import setup, find_packages


LONG_DESCRIPTION = """
snakerlib 是一个方便开发人员调用的，集合一些常用开发功能的开发Python库，
包括网络编程（tcpip、http）、日志、命令行交互、公式计算等。

snakerlib 的目的是让开发人员用最简单的方法实现最常用的功能，提高开发效率，关注
具体功能逻辑而非具体技术实现。
""".strip()

SHORT_DESCRIPTION = """
一个方便开发人员调用的，集合一些常用开发功能的开发Python库.""".strip()

DEPENDENCIES = [
    'prompt-toolkit>=2.0.0',
    'gevent>=1.2.2'
]

TEST_DEPENDENCIES = []

VERSION = '0.1.0'
URL = 'https://github.com/snakeclub/SnakerLib4Py'

setup(
    # pypi中的名称，pip或者easy_install安装时使用的名称
    name="snakerlib",
    version=VERSION,
    author="黎慧剑",
    author_email="snakeclub@163.com",
    description=SHORT_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license="Apache License, Version 2.0",
    keywords="snaker development lib",
    url=URL,
    # 需要打包的目录列表, 可以指定路径packages=['path1', 'path2', ...]
    packages=find_packages(),
    install_requires=DEPENDENCIES,
    tests_require=TEST_DEPENDENCIES,
    # 此项需要，否则卸载时报windows error
    zip_safe=False
)
