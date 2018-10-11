# -*- coding:utf-8 -*-
# !/usr/bin/env python
#
# Author: daisheng
# Email: shawntai.ds@gmail.com
#
# This is the init file for the user package
# holding api & urls of the user module
#

from .mgmtapi import UserAPI, RoleAPI, ApiAPI, MyselfAPI
from .. import api, app

prefix = '/api/%s/user' % app.config['API_VERSION']

api.add_resource(MyselfAPI, prefix + '/myself', endpoint='myself_ep')
api.add_resource(UserAPI, prefix + '/user', endpoint='user_ep')
api.add_resource(RoleAPI, prefix + '/role', endpoint='role_ep')
api.add_resource(ApiAPI, prefix + '/api', endpoint='api_ep')
