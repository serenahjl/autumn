from compusher import db,app
from nose.tools import *
from werkzeug.datastructures import FileMultiDict
import  json
import config

# establish db
def setUp(self):
        app.testing = True
        app.config.from_object(config)
        self.tester = app.test_client()
        db.drop_all()
        db.create_all()

def tearDown(self):
        # self.token = None
        db.session.close()
        # db.drop_all()

def post_api(self, api_name, d={}):
    response = self.tester.post(
        '/api/%s/spider/%s' % (self.api_v, api_name),
        content_type='application/json',
        data=json.dumps(d))
    return response


def get_api(self, api_name, id=None):
    url_str = '/api/%s/spider/%s' % (self.api_v, api_name)
    if id is not None:
        url_str += '/%s' % id
    response = self.tester.get(url_str)
    return response


def delete_api(self, api_name, id):
    url_str = '/api/%s/spider/%s/%s' % (self.api_v, api_name, id)
    response = self.tester.delete(url_str)
    return response


def put_api(self, api_name, id, d={}):
    url_str = '/api/%s/spider/%s/%s' % (self.api_v, api_name, id)
    response = self.tester.put(url_str, content_type='application/json', data=json.dumps(d))
    return response