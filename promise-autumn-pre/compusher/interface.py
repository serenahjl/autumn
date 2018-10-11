# -*- coding:utf-8 -*-
# !/usr/bin/env python
#
# Author: Shawn.T
# Email: shawntai.ds@gmail.com
#
# This is the mgmt module of compusher package,
# holding component package management, etc.
#

from flask import request
from flask_restful import reqparse, Resource
#from ..user import auth
#from ..user.models import User, Role
from bulter.user.models import User,Role
from gryphon import msclient
#from ..explorer.explorer import ExplorerInf
from . import app
#from flask import g
from . import utils
from . import exception
from .models import Compn, CompnInst
import os
import tarfile
import werkzeug
#from promise.eater.interfaces import toWalkerGetHost, toWalkerGetOwner
import datetime

COMPN_PACK_EXTENSIONS = set(['zip', 'tar.gz'])
COMPN_TEXT_EXTENSIONS = set(['yml', 'py', 'sh', 'txt'])


class CompnAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(CompnAPI, self).__init__()


    def post(self):
        """
        create a new component
        """
        [owner, compn_name, description, default_params, yml_fname,
        # eater_version,eater_reload_cmd, eater_port, eater_runtime_id, eater_mid_type, eater_owner_id
         ] = self._post_arg_check()
        compn = Compn(
            compn_name=compn_name, description=description, owner=owner, yml_fname=yml_fname,
           # eater_reload_cmd=eater_reload_cmd, eater_version=eater_version, eater_port=eater_port,
           # eater_runtime_id=eater_runtime_id, eater_mid_type=eater_mid_type,eater_owner_id=eater_owner_id
            default_params=default_params )
        [state, msg] = compn.save()
        if not state:
            app.logger.error(utils.logmsg('create new compn faild.'))
            raise exception.ServerError('create new compn faild.')
        return {'message': 'compn created.', 'compn_id': compn.compn_id}, 200

    def _post_arg_check(self):
        self.reqparse.add_argument(
            'compn_name', type=str, location='json',
            required=True, help='compn_name must be a string.')
        self.reqparse.add_argument(
            'description', type=unicode, location='json',
            required=True, help='description must be unicode.')
        self.reqparse.add_argument(
            'default_params', type=unicode, location='json',
            help='default_params must be unicode.')
        self.reqparse.add_argument(
            'yml_fname', type=str, location='json',
            required=True, help='yml_fname must have been a uploaded yml filename.')

        # self.reqparse.add_argument(
        #     'eater_version', type=str, location='json',
        #     help='eater_version must be a string. Default value is "v1.0"')
        # self.reqparse.add_argument(
        #     'eater_owner_id', type=str, location='json',
        #     help='eater_owner_id must be a string. it means compn run by which OS user.')
        # self.reqparse.add_argument(
        #     'eater_reload_cmd', type=str, location='json',
        #     required=True, help='eater_reload_cmd must be string.')
        # self.reqparse.add_argument(
        #     'eater_port', type=str, location='json',
        #     help='eater_port must be string.')
        # self.reqparse.add_argument(
        #     'eater_runtime_id', type=str, location='json',
        #     help='eater_runtime_id must be string.')
        # self.reqparse.add_argument(
        #     'eater_mid_type', type=str, location='json',
        #     help='eater_mid_type must be string.')

        args = self.reqparse.parse_args()

        try:
            #owner = User.get_users(user_id=g.current_user_id)[0]
            #现在通过msclient来获取current_user_id
            token = request.headers.get('Authorization')
            current_user_id = msclient.token_decode(token)['user_id']
            owner = User.get_users(user_id=current_user_id)[0]

        except:
            app.logger.debug(utils.logmsg('wrong user_id in token.'))
            raise exception.ClientUnauthError('wrong user_id in token.')

        compn_name = args['compn_name']
        yml_fname = args['yml_fname']

        description = args['description']
        default_params = args['default_params']
        # eater_version = args['eater_version']
        # eater_reload_cmd = args['eater_reload_cmd']
        # eater_port = args['eater_port']
        # eater_runtime_id = args['eater_runtime_id']
        # eater_mid_type = args['eater_mid_type']
        # eater_owner_id = args['eater_owner_id']
        # if eater_owner_id is not None and eater_owner_id is not '':
        #     eater_owner = toWalkerGetOwner(id=eater_owner_id)
        #     if eater_owner is None:
        #         raise utils.ClientUnprocEntError('wrong eater_owner_id.')
        # else:
        #     eater_owner_id = None
        return [owner, compn_name, description, default_params, yml_fname,
                 #eater_version,eater_reload_cmd, eater_port, eater_runtime_id, eater_mid_type, eater_owner_id
                 ]


    def get(self):
        [compn, current_user] = self._get_arg_check()
        if compn is not None:
            compn_dict = compn.get_dict_info()
            msg = 'compn info.'
            return {'message': msg, 'compn_info': compn_dict}, 200
        compns = Compn.get_compns()
        compn_dics = list()
        for compn in compns:
            compn_dics.append(compn.get_dict_info())
        msg = 'Compns info.'
        return {'message': msg, 'compns_info': utils.sort_dict(compn_dics, 'compn_name')}

    def _get_arg_check(self):
        self.reqparse.add_argument(
            'compn_id', type=str, location='args', help='compn_id must be a string.')
        args = self.reqparse.parse_args()

        try:
            #current_user = User.get_users(user_id=g.current_user_id)[0]

            #现在通过新方法获取current_user_id
            token = request.headers.get('Authorization')
            current_user_id = msclient.token_decode(token)['user_id']
            current_user = User.get_users(user_id=current_user_id)[0]


        except:
            app.logger.debug(utils.logmsg('wrong user_id in token.'))
            raise exception.ClientUnauthError('wrong user_id in token.')

        compn_id = args['compn_id']
        if compn_id is not None:
            try:
                compn = Compn.get_compns(compn_id=compn_id)[0]
            except:
                app.logger.info(utils.logmsg('wrong compn id.'))
                raise exception.ClientUnprocEntError('wrong component id.')
            return [compn, current_user]
        else:
            return [None, current_user]

    def delete(self):
        """
        delete one component
        """
        # check the arguments
        [compn, current_user] = self._delete_arg_check()
        [state, msg] = compn.delete()
        if not state:
            msg = 'delete compn faild.'
            app.logger.info(utils.logmsg(msg))
            raise exception.ServerError(msg)
        app.logger.debug(utils.logmsg(msg))
        return {'message': msg}, 200

    def _delete_arg_check(self):
        self.reqparse.add_argument(
            'compn_id', type=str, location='args',
            required=True, help='compn id must be a string')

        args = self.reqparse.parse_args()
        compn_id = args['compn_id']

        try:
            #current_user = User.get_users(user_id=g.current_user_id)[0]

            #现在通过msclient获取current_user_id
            token = request.headers.get('Authorization')
            current_user_id = msclient.token_decode(token)['user_id']
            current_user = User.get_users(user_id=current_user_id)[0]


        except:
            app.logger.info(utils.logmsg('wrong user_id in token.'))
            raise exception.ClientUnprocEntError('wrong user_id in token.')

        try:
            compn = Compn.get_compns(compn_id=compn_id)[0]
        except:
            app.logger.info(utils.logmsg('wrong compn_id.'))
            raise exception.ClientUnprocEntError('wrong compn_id.')
        return [compn, current_user]


    def put(self):
        [compn, owner, compn_name, description, default_params, yml_fname,
         #eater_version, eater_reload_cmd, eater_port, eater_runtime_id, eater_mid_type, eater_owner_id
         ] = self._put_arg_check()
        [state, msg] = compn.update(
            yml_fname=yml_fname, compn_name=compn_name, description=description,
            #eater_reload_cmd=eater_reload_cmd,
            #eater_version=eater_version, eater_port=eater_port, eater_runtime_id=eater_runtime_id,
           # eater_mid_type=eater_mid_type, eater_owner_id=eater_owner_id
            default_params=default_params)
        if not state:
            app.logger.error(utils.logmsg('compn ' + compn.compn_id + ' update faild.'))
            raise exception.ServerError('compn update faild.')
        app.logger.info(utils.logmsg('compn ' + compn.compn_id + ' updated.'))
        return {"message": 'compn updated.', 'compn_id': compn.compn_id}, 200

    def _put_arg_check(self):
        [compn, current_user] = self._delete_arg_check()
        [owner, compn_name, description, default_params, yml_fname,
         #eater_version, eater_reload_cmd,
         #eater_port, eater_runtime_id, eater_mid_type, eater_owner_id
         ] = self._post_arg_check()
        return [compn, owner, compn_name, description, default_params, yml_fname,
                #eater_version, eater_reload_cmd, eater_port, eater_runtime_id, eater_mid_type, eater_owner_id
                ]


class CompnInstAPI(Resource):
    """docstring for CompnInstAPI"""
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(CompnInstAPI, self).__init__()


    def post(self):
        [current_user, compn, description, hosts_params] = self._post_arg_check()
        compn_inst = CompnInst(compn=compn, description=description, owner=current_user,
                               hosts_params=hosts_params)
        [state, msg] = compn_inst.save()
        if not state:
            app.logger.error(utils.logmsg('compn_inst create faild.'))
            raise exception.ClientUnprocEntError('compn_inst create faild.')
        compn_inst.asyn_push.delay()
        return {'message': 'compn_inst created.', 'compninst_id': compn_inst.compninst_id}, 200

    def _post_arg_check(self):
        self.reqparse.add_argument(
            'compn_id', type=str, location='json',
            required=True, help='compn_id must be a string.')
        self.reqparse.add_argument(
            'description', type=unicode, location='json',
            help='description must be unicode.')
        self.reqparse.add_argument(
            'hosts_params', type=list, location='json',
            required=True,
            help='host_params must be a list like[{"host_id":xx,"params":xx},...].')

        args = self.reqparse.parse_args()

        try:
           # current_user = User.get_users(user_id=g.current_user_id)[0]

          #现在用msclient来获取current_user_id
            token = request.headers.get('Authorization')
            current_user_id = msclient.token_decode(token)['user_id']
            current_user = User.get_users(user_id=current_user_id)[0]


        except:
            app.logger.debug(utils.logmsg('wrong user_id in token.'))
            raise exception.ClientUnauthError('wrong user_id in token.')

        compn_id = args['compn_id']
        try:
            compn = Compn.get_compns(compn_id=compn_id)[0]
        except:
            app.logger.info(utils.logmsg('wrong compn id.'))
            raise exception.ClientUnprocEntError('wrong component id.')

        description = args['description']

        hosts_params = args['hosts_params']
        if not len(hosts_params):
            raise exception.ClientUnprocEntError('empty hosts_params.')

        for host_params in hosts_params:
            if 'params' not in host_params.keys():
                raise exception.ClientUnprocEntError('missing params in hosts_params.')
            if 'host_id' not in host_params.keys():
                raise exception.ClientUnprocEntError('missing host_id in hosts_params.')
            if not host_params['host_id']:
                raise exception.ClientUnprocEntError('host_id is empty in hosts_params.')

            #现在检查不了host_id的值了
            # host = toWalkerGetHost(id=host_params['host_id'])
            # if host is None:
            #     raise utils.ClientUnprocEntError('wrong host_id in hosts_params.')
        return [current_user, compn, description, hosts_params]


    def get(self):
        [compn_inst, current_user] = self._get_arg_check()
        if compn_inst is not None:
            compninst_dict = compn_inst.get_dict_info()
            msg = 'componet instance info.'
            return {'message': msg, 'compninst_info': compninst_dict}, 200
        compn_insts = CompnInst.get_compninsts(owner_id=current_user.user_id)
        compninst_dics = list()
        for compn_inst in compn_insts:
            compninst_dics.append(compn_inst.get_dict_info())
        msg = 'Component instance info.'
        return {'message': msg, 'compninsts_info': utils.sort_dict(compninst_dics, 'compn_id')}

    def _get_arg_check(self):
        self.reqparse.add_argument(
            'compninst_id', type=str, location='args', help='compninst_id must be a string.')
        args = self.reqparse.parse_args()

        try:
            #current_user = User.get_users(user_id=g.current_user_id)[0]

           #现在用msclent来获取current_user_id
            token = request.headers.get('Authorization')
            current_user_id = msclient.token_decode(token)['user_id']
            current_user = User.get_users(user_id=current_user_id)[0]


        except:
            app.logger.debug(utils.logmsg('wrong user_id in token.'))
            raise exception.ClientUnauthError('wrong user_id in token.')

        compninst_id = args['compninst_id']
        if compninst_id is not None:
            try:
                compn_inst = CompnInst.get_compninsts(
                    compninst_id=compninst_id, owner_id=current_user.user_id)[0]
            except:
                app.logger.info(utils.logmsg('wrong compninst id.'))
                raise exception.ClientUnprocEntError('wrong compninst id.')
            return [compn_inst, current_user]
        else:
            return [None, current_user]
