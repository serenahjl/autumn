# -*- coding: utf-8 -*-
from flask import Blueprint, make_response, json
from flask_restful import Api

from .application import app
from .explorer import CompnExplorerAPI
from .explorer import ExplorerAPI
from .filesync import FileSyncAPI

bp = Blueprint('explorer', 'explorer.explorer')
api = Api(bp)

prefix = '/api/' + app.config['API_VERSION']

api.add_resource(ExplorerAPI,
                 prefix + '/explorer/user_folder',
                 endpoint='explorer_user_ep')
api.add_resource(CompnExplorerAPI,
                 prefix + '/explorer/compn_folder',
                 endpoint='explorer_compn_ep')
api.add_resource(FileSyncAPI,
                 prefix + '/explorer/file_sync',
                 endpoint='file_sync_ep')


@api.representation('application/json')
def responseJson(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


def create_app():
    app.register_blueprint(bp)
    return app
