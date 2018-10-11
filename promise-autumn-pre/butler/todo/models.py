# -*- coding: utf-8 -*-

from gryphon import msclient

from .. import app
from .. import utils
from ..utils import redis_factory

redis = redis_factory()


class ApprovState(object):
    """docstring for ApprovState"""

    def __init__(self, appinst_id, user_id):
        super(ApprovState, self).__init__()
        self.appinst_id = appinst_id
        self.user_id = user_id
        self._client = msclient.MSClient(app.config['KONG_URL'],
                                         app.config['KONG_USER'],
                                         app.config['KONG_PWD'])

    @property
    def state(self):
        url = '/applet/approval?user_id={}'.format(self.user_id)
        result = self._client.execute('GET', url)
        return result

    def get_todo_appinsts_json(self):
        url = '/applet/approval?state=todo&user_id={}'.format(self.user_id)
        result = self._client.execute('GET', url)
        return result

    def get_done_approval_json(self):
        url = '/applet/approval?state=done&user_id={}'.format(self.user_id)
        result = self._client.execute('GET', url)
        return result

    def get_todo_approval_ids(self):
        url = '/applet/approval?state=done&user_id={}&flat=1'.\
            format(self.user_id)
        result = self._client.execute('GET', url)
        return result

    def get_done_approval_ids(self, user_id):
        url = '/applet/approval?state=done&user_id={}&flat=1'.\
            format(self.user_id)
        result = self._client.execute('GET', url)
        return result

    def set_passed(self, msg):
        try:
            data = {
                'user_id': self.user_id,
                'is_passed': True,
                'msg': msg
            }
            url = '/applet/approval/{}'.format(self.appinst_id)
            self._client.execute('PATCH', url, json_d=data)
        except Exception as e:
            _msg = utils.logmsg('set approv state error. err {}'.format(e))
            app.logger.error(_msg)
            return False
        return True

    def set_rejected(self, msg):
        try:
            data = {
                'user_id': self.user_id,
                'is_passed': False,
                'msg': msg
            }
            url = '/applet/approval/{}'.format(self.appinst_id)
            self._client.execute('PATCH', url, json_d=data)
        except Exception as e:
            _msg = utils.logmsg('set approv state error. err {}'.format(e))
            app.logger.error(_msg)
            return False
        return True

    def remove_appinst(self):
        try:
            data = {
                'user_id': self.user_id,
                'is_passed': False,
            }
            url = '/applet/approval/{}'.format(self.appinst_id)
            self._client.execute('PATCH', url, json_d=data)
        except Exception as e:
            _msg = utils.logmsg('set approv state error. err {}'.format(e))
            app.logger.error(_msg)
            return False
        return True
