# -*- coding:utf-8 -*-
# !/usr/bin/env.conf python
#
# Author: Shawn.T
# Email: dai.sheng@139.com
#
# This is the filesync module of promise
#

from flask import request
from flask_restful import reqparse, Resource
from gryphon.msclient import token_decode

import utils
from explorer import app
from .tasks import fetch_task, get_task_status

playbook_bkname = app.config['COMPN_PBS_BKNAME']
pkgs_bkname = app.config['COMPN_PKGS_BKNAME']
roles_bkname = app.config['COMPN_ROLES_BKNAME']

COMPN_PACK_EXTENSIONS = {'zip', 'tar.gz'}
COMPN_TEXT_EXTENSIONS = {'yml', 'py', 'sh', 'txt'}


class FileSyncAPI(Resource):
    """
    API class of FileSyncAPI
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(FileSyncAPI, self).__init__()

    def post(self):
        current_user_name = self._get_current_username()
        [remote_paths, local_path, sync_type] = self._post_arg_check()
        rest = fetch_task.delay(remote_paths_ips=remote_paths,
                                bkname=current_user_name,
                                local_path=local_path)
        msg = 'file sync task is running.'

        return {'message': msg, 'task_id': rest.task_id}, 200

    def _post_arg_check(self):
        self.reqparse.add_argument(
            'remote_paths', type=list, location='json',
            help='remote_paths must be a json.')
        self.reqparse.add_argument(
            'local_path', type=unicode, location='json',
            help='must be a folder in user_folder.')
        self.reqparse.add_argument(
            'sync_type', type=str, location='json',
            help='type must be get or put.')

        args = self.reqparse.parse_args()

        sync_type = args['sync_type']
        if sync_type == 'put':
            raise utils.ClientUnprocEntError('file put is not ready.')
        if not sync_type == 'get':
            raise utils.ClientUnprocEntError('sync_type must be "get".')
        local_path = args['local_path']
        remote_paths = args['remote_paths']

        return [remote_paths, local_path, sync_type]

    def get(self):
        task_id = self._get_arg_check()

        return {'status': get_task_status(task_id)}, 200

    def _get_arg_check(self):
        self.reqparse.add_argument(
            'task_id', type=str, location='args',
            help='task_id must be a string.')

        args = self.reqparse.parse_args()
        task_id = args['task_id']
        return task_id

    def _get_token_payload(self):
        token = request.headers.get('Authorization')
        return token_decode(token)

    def _get_current_username(self):
        return self._get_token_payload()['username']

    def _get_current_user_id(self):
        return self._get_token_payload()['user_id']
