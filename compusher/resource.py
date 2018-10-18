# -*- coding:utf-8 -*-

# 添加api的resource


from .interface import CompnAPI, CompnInstAPI
from . import api, app

api.add_resource(
    CompnAPI, '/api/' + app.config['API_VERSION'] + '/compusher/compn',
    endpoint='compn_ep')
# api.add_resource(
#     FilesAPI, '/api/' + app.config['API_VERSION'] + '/compusher/files',
#     endpoint='compn_files_ep')
api.add_resource(
    CompnInstAPI, '/api/' + app.config['API_VERSION'] + '/compusher/compn_inst',
    endpoint='compn_inst_ep')