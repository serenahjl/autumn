# -*- coding:utf-8 -*-
# !/usr/bin/env.conf python
#
# Author: daisheng
# Email: shawntai.ds@gmail.com
#
# This is the init file for the user package
# holding api & urls of the user module
#

from .todo import DoneAPI, TodoAPI
from .. import api, app

api.add_resource(
    TodoAPI, '/api/' + app.config['API_VERSION'] + '/user/todo',
    endpoint='todo_ep')
api.add_resource(
    DoneAPI, '/api/' + app.config['API_VERSION'] + '/user/done',
    endpoint='done_ep')
