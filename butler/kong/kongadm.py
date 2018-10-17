# -*- coding:utf-8 -*-
# !/usr/bin/env.conf python
#
# Author: daisheng
# Email: shawntai.ds@gmail.com

import utils
from baseinf import GroupInf, ConsumerInf, ApiInf, AclPluginInf, JwtCredInf, \
    JwtPluginInf
from exceptions import *

logger = utils.logger
group_inf = GroupInf()
consumer_inf = ConsumerInf()
api_inf = ApiInf()
aclplugin_inf = AclPluginInf()


class Consumer(object):
    """docstring for Consumer"""

    def __new__(cls, username):
        return super(Consumer, cls).__new__(cls)

    def __init__(self, username):
        super(Consumer, self).__init__()
        self._username = username

        consumer_id, username = self._chk_kong(username)
        if consumer_id is None:
            self._consumer_id = self._add(self.username)
        else:
            self._consumer_id = consumer_id

    @classmethod
    def get(cls, username_or_id):
        consumer_id, username = cls._chk_kong(username_or_id)
        if consumer_id:
            consumer = cls.__new__(cls, username)
            consumer._username = username
            consumer._consumer_id = consumer_id
            return consumer
        else:
            return None

    @staticmethod
    def list_usernames():
        total, infos = consumer_inf.list()
        return [info['username'] for info in infos if 'username' in info]

    @staticmethod
    def _chk_kong(username_or_id):
        if username_or_id is None:
            return None, None
        kong_info = consumer_inf.retrieve(username_or_id)
        if kong_info is None:
            return None, None
        return kong_info['id'], kong_info['username']

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        if isinstance(username, str) or isinstance(username, unicode):
            consumer_inf.update(username, self._username)
            self._username = username

    @property
    def groups(self):
        return group_inf.list(self._username)

    @groups.setter
    def groups(self, groups):
        if isinstance(groups, list):
            group_inf.set_groups2consumer(username_or_id=self._username,
                                          groups=groups)

    @property
    def consumer_id(self):
        return self._consumer_id

    @staticmethod
    def _add(username):
        consumer_id = consumer_inf.add(username=username)
        if consumer_id is None:
            logger.error('create consumer error<username:%s>' % username)
            return None
        else:
            return consumer_id

    def delete(self):
        consumer_inf.delete(self._username)
        self._username = None

    @staticmethod
    def get_username(consumer_id):
        info = consumer_inf.retrieve(consumer_id)
        return info['username']


class Group(object):
    """docstring for Groups"""

    def __init__(self, group):
        super(Group, self).__init__()
        self.group = group

    @staticmethod
    def list():
        return group_inf.list()

    @classmethod
    def get(cls, group):
        return Group(group)

    @property
    def usernames(self):
        infos = group_inf.list_groups2consumers()
        consumer_ids = [info['consumer_id'] for info in infos if
                        info['group'] == self.group]
        consumer_ids = list(set(consumer_ids))
        return [Consumer.get_username(consumer_id) for consumer_id in
                consumer_ids]

    @usernames.setter
    def usernames(self, tar_usernames):
        if not isinstance(tar_usernames, list):
            logger.error('tar_usernames is not a list')
        all_usernames = Consumer.list_usernames()
        invalidated_usernames = [
            tar_username for tar_username in tar_usernames if
            tar_username not in all_usernames]
        if invalidated_usernames:
            logger.error('%s not exist' % invalidated_usernames)
        cur_usernames = self.usernames
        for cur_username in cur_usernames:
            for tar_username in tar_usernames:
                if cur_username not in tar_usernames:
                    # delete relationship: tar_username+self.group
                    group_inf.delete(cur_username, self.group)
                if tar_username not in cur_usernames:
                    # add relationship: tar_username+self.group
                    group_inf.add(tar_username, self.group)

    @property
    def api_ids(self):
        total, aclplugin_infos = aclplugin_inf.list()
        api_ids = list()
        for info in aclplugin_infos:
            if 'config' in info and 'whitelist' in info['config']:
                if self.group in info['config']['whitelist']:
                    api_ids.append(info['api_id'])
        return api_ids

    @api_ids.setter
    def api_ids(self, tar_api_ids):
        if not isinstance(tar_api_ids, list):
            logger.error('tar_api_ids should be a list<%s>' % tar_api_ids)
        try:
            # remove this group from exists api binding relationship
            cur_apiids = self.api_ids
            for cur_apiid in cur_apiids:
                if cur_apiid not in tar_api_ids:
                    cur_api = KongApi(cur_apiid)
                    whitelist = cur_api.whitelist
                    if self.group in whitelist:
                        whitelist.remove(self.group)
                        cur_api.whitelist = whitelist

            # add this group to new api binding relationship
            for tar_apiid in tar_api_ids:
                if tar_apiid not in cur_apiids:
                    tar_api = KongApi(tar_apiid)
                    whitelist = tar_api.whitelist
                    if self.group not in whitelist:
                        whitelist.append(self.group)
                        tar_api.whitelist = whitelist
        except KongError as e:
            logger.error('kongerror:%s' % e)

    def delete(self):
        self.apis = []
        self.usernames = []
        self.group = None


class KongApi(object):
    """docstring for Api"""

    def __new__(cls, api_id):
        if cls._chk_kong(api_id):
            return super(KongApi, cls).__new__(cls)
        else:
            return None

    def __init__(self, _id):
        super(KongApi, self).__init__()
        self.id = _id

    @staticmethod
    def _chk_kong(api_id):
        try:
            api_inf.retrieve(api_id)
        except ResourceNotFoundError:
            return False
        else:
            return True

    @classmethod
    def get(cls, api_id):
        return cls(api_id)

    @staticmethod
    def list():
        total, api_infos = api_inf.list()
        return api_infos

    @property
    def info(self):
        return api_inf.retrieve(self.id)

    @property
    def whitelist(self):
        """
        whitelist is a list of groups set in kong acls
        """
        info = aclplugin_inf.get_acllist(self.id)
        return info['whitelist']

    @whitelist.setter
    def whitelist(self, whitelist):
        if not len(whitelist):
            self._remove_acl_plugin()
        else:
            aclplugin_inf.set_acllist(self.id, whitelist)

    def init_jwt_plugin(self):
        jwt_plugin_inf = JwtPluginInf(self.id)
        return jwt_plugin_inf.add(self.id)

    def _remove_jwt_plugin(self):
        jwt_plugin_inf = JwtPluginInf(self.id)
        return jwt_plugin_inf.remove(self.id)

    def _remove_acl_plugin(self):
        return aclplugin_inf.delete(self.id)


class JwtCred(object):
    """docstring for JwtCred"""

    def __init__(self, user):
        super(JwtCred, self).__init__()
        self._cred_inf = JwtCredInf(user.username)
        self._user = user

    @property
    def token(self):
        info = self._cred_inf.info
        return self._cred_inf.token_gen(
            key=info['key'],
            secret=info['secret'],
            username=self._user.username,
            user_id=self._user.user_id)

    def delete(self):
        self._cred_inf.delete()

    @staticmethod
    def get_user_id(token):
        claims = JwtCredInf.token_decode(token)
        return claims['user_id']

    @staticmethod
    def get_username(token):
        claims = JwtCredInf.token_decode(token)
        return claims['user_name']
