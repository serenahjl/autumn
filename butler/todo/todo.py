# -*- coding:utf-8 -*-
# !/usr/bin/env.conf python
#
# Author: Shawn.T
# Email: shawntai.ds@gmail.com
#
# This is the mgmt module of user package,
# holding user management, privilege management, and role management, etc.
#

from flask_restful import reqparse, Resource
from gryphon import msclient

from .models import ApprovState
from .. import dont_cache
from .. import utils


class AuthMixin(object):
    def get_userid(self):
        self.reqparse.add_argument(
            'Authorization', type=str, location='headers',
            required=True, help='authorization must be a string')
        args = self.reqparse.parse_args()
        auth = args['Authorization']
        token_info = msclient.token_decode(auth_in_header=auth)
        return token_info['user_id']


class TodoAPI(Resource, AuthMixin):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(TodoAPI, self).__init__()

    @dont_cache()
    def get(self):
        """
        get user todo list
        """

        user_id = self.get_userid()
        approval = ApprovState(None, user_id)
        todoappinsts_json = approval.get_todo_appinsts_json()
        return utils.make_response(todoappinsts_json, 200)


class DoneAPI(Resource, AuthMixin):
    """
    do something as the todolist, eq. scene approv, etc.
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(DoneAPI, self).__init__()

    def post(self):
        # for applet unpassed approv
        user_id = self.get_userid()
        [pass_appinst_ids,
         rej_appinst_ids] = self._post_arg_check_for_approv_state()
        if pass_appinst_ids:
            for pass_appinst_id in pass_appinst_ids:
                approv_state = ApprovState(pass_appinst_id['appinst_id'],
                                           user_id)
                approv_state.set_passed(pass_appinst_id['message'])
        if rej_appinst_ids:
            for rej_appinst_id in rej_appinst_ids:
                approv_state = ApprovState(rej_appinst_id['appinst_id'],
                                           user_id)
                approv_state.set_rejected(rej_appinst_id['message'])
        return {'passed_appinst_ids': pass_appinst_ids,
                'rej_appinst_ids': rej_appinst_ids}, 200

    def _post_arg_check_for_approv_state(self):
        self.reqparse.add_argument(
            'pass_appinst_ids', type=list, location='json',
            help='pass_appinst must be a list: '
                 '[{appinst_id:xx,message:xx},{}..]')
        self.reqparse.add_argument(
            'rej_appinst_ids', type=list, location='json',
            help='rej_appinst must be a list: '
                 '[{appinst_id:xx,message:xx},{}..]')

        args = self.reqparse.parse_args()
        pass_appinst_ids = args['pass_appinst_ids']
        rej_appinst_ids = args['rej_appinst_ids']

        return [pass_appinst_ids, rej_appinst_ids]

    def get(self):
        user_id = self.get_userid()
        approv_state = ApprovState(None, user_id)
        doneappinsts_json = approv_state.get_done_approval_json()
        return utils.make_response(doneappinsts_json, 200)
