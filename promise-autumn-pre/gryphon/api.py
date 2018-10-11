#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Author: Leann Mak
# Email: leannmak@139.com
# (c) 2018
#
# This is the adapter module of external api.
#
__all__ = ['DisconfAPI', 'DisconfAPIException', 'Ansible2API', 'ZabbixAPI',
           'ZabbixAPIException', 'EtcdAPI', 'EtcdAPIException', 'MySQLAPI',
           'MySQLAPIException', 'MinioAPI', 'MinioAPIException']

"""
    DISCONF Adapter
"""
try:
    import simplejson as json
except ImportError:
    import json

import re
import urllib2
import cookielib
from urllib import urlencode
from poster.encode import multipart_encode
from poster.streaminghttp import StreamingHTTPHandler, \
    StreamingHTTPRedirectHandler, StreamingHTTPSHandler


class DisconfAPIException(Exception):
    pass


class DisconfAPI(object):
    """ Disconf API for Python

    Usage:

        dapi = DisconfAPI(
            url='http://127.0.0.1:8080', user='your-name',
            password='your-password')
        dapi.login()
        result = dapi.env_list.get()

    Supported Methods:

    :api app_list
        method get
    :api app
        method post
    :api account_session
        method get
    :api account_signin
        method post
    :api account_signout
        method get
    :api env_list
        method get
    :api web_config_item
        method post
    :api web_config_file
        method post
    :api web_config_filetext
        method post
    :api web_config_versionlist
        method get
    :api web_config_list
        method get
    :api web_config_simple_list
        method get
    :api web_config_<id>
        method get
    :api env_list
        method get
        method delete
    :api web_config_zk_<id>
        method get
    :api web_config_download_<id>
        method get
    :api web_config_downloadfilebatch_<id>
        method get
    :api web_config_item_<id>
        method put
    :api web_config_file_<id>
        method post
    :api web_config_filetext_<id>
        method put
    :api zoo_zkdeploy
        method get

    More object details see:

        http://disconf.readthedocs.io/zh_CN/latest/tutorial-web/src/12-open-api-for-web.html

    Note: Methods haven't been list upon may not be supported by DisconfAPI.
    """
    __auth = None
    _state = {}
    _method = {}

    # create a new DisconfAPI Object if not exists
    def __new__(cls, *args, **kw):
        if cls not in cls._state:
            cls._state[cls] = super(DisconfAPI, cls).__new__(cls, *args, **kw)
        return cls._state[cls]

    # constructor : disconf api's [url, user_name, user_password, api_list]
    def __init__(
            self, url, user, password, timeout=10, loglevel=1,
            cookiefile='cookie.txt'):
        self.__url = url
        self.__user = user
        self.__password = password
        self.__timeout = timeout
        self.__loglevel = 1
        self.__cookiefile = cookiefile
        self.__disconf_api_prefix = '/api/'
        self._disconf_api_list = {
            '^app/list$': ['GET'],
            '^app$': ['POST'],
            '^account/session$': ['GET'],
            '^account/signin$': ['POST'],
            '^account/signout$': ['GET'],
            '^env/list$': ['GET'],
            '^web/config/item$': ['POST'],
            '^web/config/file$': ['POST'],
            '^web/config/filetext$': ['POST'],
            '^web/config/versionlist$': ['GET'],
            '^web/config/list$': ['GET'],
            '^web/config/simple/list$': ['GET'],
            '^web/config/[0-9]+$': ['GET', 'DELETE'],
            '^web/config/zk/[0-9]+$': ['GET'],
            '^web/config/download/[0-9]+$': ['GET'],
            '^web/config/downloadfilebatch$': ['GET'],
            '^web/config/item/[0-9]+$': ['PUT'],
            '^web/config/file/[0-9]+$': ['POST'],
            '^web/config/filetext/[0-9]+$': ['PUT'],
            '^zoo/zkdeploy$': ['GET']}

    # get a DisconfAPIFactory Object
    def __getattr__(self, api):
        if api not in self.__dict__:
            api_org = re.sub('_', '/', api)
            self._method[api_org] = None
            for k, v in self._disconf_api_list.items():
                if re.match(k, api_org):
                    self._method[api_org] = v
                    break
            if not self._method[api_org]:
                self._method.pop(api_org)
                raise DisconfAPIException(
                    'No such Disconf API: %s' % api_org)
            self.__dict__[api] = DisconfAPIFactory(self, api_org)
        return self.__dict__[api]

    # user login for disconf api which returns a cookie as self.__auth
    def login(self):
        cookie = self.set_handlers()
        user_info = {'name': self.__user,
                     'password': self.__password,
                     'remember': 1}
        try:
            self.url_request(
                api='account/signin', method='POST', **user_info)
        except urllib2.HTTPError:
            raise DisconfAPIException('Disconf URL Error')
        cookie.save(ignore_discard=True, ignore_expires=True)
        self.__auth = cookie

    # check user login status for disconf
    def is_login(self):
        return self.__auth is not None

    # check user authorization for disconf
    def __checkAuth__(self):
        if not self.is_login():
            raise DisconfAPIException('Disconf-Web NOT Logged In')

    # set handlers for url request
    def set_handlers(self):
        handlers = [
            StreamingHTTPHandler(debuglevel=self.__loglevel),
            StreamingHTTPRedirectHandler,
            StreamingHTTPSHandler(debuglevel=self.__loglevel)]
        cookie = cookielib.MozillaCookieJar(self.__cookiefile)
        handlers.append(urllib2.HTTPCookieProcessor(cookie))
        opener = urllib2.build_opener(*handlers)
        urllib2.install_opener(opener)
        self.__urllib = urllib2
        return cookie

    # request a disconf api: post/get/put/delete
    def url_request(self, api, method, **params):
        api = '%s%s' % (self.__disconf_api_prefix, api)
        method = method.upper()
        if params and (method == 'GET' or method == 'PUT'):
            api += '?%s' % urlencode(params)
        data, headers = multipart_encode(params)
        headers['User-Agent'] = 'DisconfAPI'
        request = self.__urllib.Request(
            url='%s%s' % (self.__url, api), data=data, headers=headers)
        request.get_method = lambda: method
        opener = self.__urllib.urlopen(url=request, timeout=self.__timeout)
        content = json.loads(opener.read())
        return content


# add to verify authorization
def disconf_check_auth(func):
    def ret(self, *args, **params):
        self.__checkAuth__()
        return func(self, *args, **params)
    return ret


# add to get pure disconf api response
def disconf_api(func):
    def wrapper(self, method, **params):
        return self.url_request(method=method, **params)
    return wrapper


class DisconfAPIFactory(object):
    """ Disconf API Factory
    """
    # the construtor
    def __init__(self, dapi, api):
        # a DisconfAPI Object
        self.__dapi = dapi
        # a disconf api like 'app/list', ...
        self.__api = api

    # verify user authorization for disconf using the DisconfAPI Object
    def __checkAuth__(self):
        self.__dapi.__checkAuth__()

    # call a api method like post/get/put/delete of DisconfAPIFactory
    def __getattr__(self, method):
        def func(**params):
            if method.upper() not in self.__dapi._method[self.__api]:
                raise DisconfAPIException(
                    'No such API Method: %s %s' % (method.upper(), self.__api))
            return self.proxy_api(method=method, **params)
        return func

    # request a disconf api using the DisconfAPI Object
    def url_request(self, method, **params):
        return self.__dapi.url_request(
            api=self.__api, method=method, **params)

    # the request proxy method
    @disconf_check_auth
    @disconf_api
    def proxy_api(self, method, **params):
        pass


"""
    ANSIBLE Adapter
"""
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor import playbook_executor


class Ansible2API(object):
    """ Ansible v2.0+ API

    Usage:

        client = Ansible2API(
            hosts=['127.0.0.1'],
            passwords=dict(
                conn_pass='connection-password', become_pass='become-password'),
            connection='ssh',
            remote_user='root',
            verbosity=0,
            become=True,
            become_method='sudo',
            become_user='root',
            private_key_file='')
        result = client.run(module='shell', args='echo "hello world"')

    """
    _default_options = frozenset([
        'connection', 'module_path', 'forks', 'remote_user',
        'private_key_file', 'ssh_common_args', 'ssh_extra_args',
        'sftp_extra_args', 'scp_extra_args', 'become', 'become_method',
        'become_user', 'verbosity', 'check', 'listhosts', 'listtasks',
        'listtags', 'syntax'])

    def __init__(self, hosts, inventory_file=None, passwords=None, **kwargs):
        # set ansible options
        for x in self._default_options:
            kwargs[x] = kwargs[x] if x in kwargs else None
        Options = namedtuple('Options', kwargs.keys())
        self.options = Options(**kwargs)
        # set passwords
        passwords = passwords if passwords else dict()
        if hasattr(self.options, 'private_key_file') and \
                self.options.private_key_file and \
                isinstance(passwords, dict) and 'conn_pass' in passwords:
            passwords.pop('conn_pass')
        # hosts must be a list
        self.hosts = hosts
        self.passwords = passwords
        self.variable_manager = VariableManager()
        self.loader = DataLoader()
        if inventory_file is not None:
            self.inventory = Inventory(
                loader=self.loader,
                variable_manager=self.variable_manager,
                host_list=inventory_file)
        else:
            self.inventory = Inventory(
                loader=self.loader,
                variable_manager=self.variable_manager,
                host_list=self.hosts)
        self.variable_manager.set_inventory(self.inventory)

    def run(self, module, args):
        """ run an ansible 2.0+ play
        """
        play_source = dict(
            name='Ansible Task',
            hosts='all',
            gather_facts='no',
            tasks=[dict(
                action=dict(module=module, args=args),
                register='out')])
        play = Play().load(
            play_source, variable_manager=self.variable_manager,
            loader=self.loader)
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback='default')
            state = tqm.run(play)
            hostvars = tqm.hostvars
            stats = tqm._stats
            stats_sum = dict()
            results = dict()
            for host in self.hosts:
                t = stats.summarize(host)
                stats_sum[host] = t
                hostvar = hostvars[host]
                results[host] = hostvar['out']
            return state, stats_sum, results
        finally:
            if tqm is not None:
                tqm.cleanup()

    def run_pb(self, playbook_path, run_data=None):
        if run_data is not None:
            self.variable_manager.extra_vars = run_data
        pbex = playbook_executor.PlaybookExecutor(
            playbooks=[playbook_path],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=self.options,
            passwords=self.passwords)
        state = pbex.run()
        stats = pbex._tqm._stats
        stats_sum = dict()
        for host in self.hosts:
            t = stats.summarize(host)
            stats_sum[host] = t
        return state, stats_sum


"""
    ETCD Adapter
"""
from etcd import Client


class EtcdAPIException(Exception):
    pass


# check if etcd server is connected
def etcd_check_connect(func):
    def ret(self, method):
        self.__checkStatus__()
        return func(self, method)
    return ret


class EtcdAPI(object):
    """ ETCD API

    Usage:

        client = EtcdAPI(
            host='your-etcd-address', port=2379,
            cert=('etcd-client.crt', 'etcd-client-key.pem'),
            ca_cert='etcd-ca.crt', protocol='https',
            allow_reconnect=True)
        client.connect()
        result = client.read(key='/')

    Supported Methods:

        ['read', 'write', 'upadte', 'delete', 'watch', 'pop']

    More method and argument details see:

        https://github.com/coreos/etcd
        http://python-etcd.readthedocs.io/en/latest/

    Note: Methods haven't been list upon may not be supported by EtcdAPI.
    """
    __connected = False
    __default_args = dict(
        host='127.0.0.1', port=4001, srv_domain=None, version_prefix='/v2',
        read_timeout=60, allow_redirect=True, protocol='http', cert=None,
        ca_cert=None, username=None, password=None, allow_reconnect=False,
        use_proxies=False, expected_cluster_id=None, per_host_pool_size=10,
        lock_prefix='/_locks')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.__default_args:
                self.__default_args[k] = v
        self._method = frozenset(
            ['read', 'write', 'upadte', 'delete', 'watch', 'pop'])

    def connect(self):
        self.__client = Client(**self.__default_args)
        self.__connected = True

    def __contains__(self, key):
        return self.__client.__contains__(key=key)

    # connection status for etcd
    def is_connect(self):
        return self.__connected

    # check connection status for etcd
    def __checkStatus__(self):
        if not self.is_connect():
            raise EtcdAPIException('Etcd NOT Connected')

    def __getattr__(self, method):
        def func(*args, **kwargs):
            if method not in self._method:
                raise EtcdAPIException('No Such Etcd API: %s' % method)
            return self.proxy_api(method=method)(*args, **kwargs)
        return func

    @etcd_check_connect
    def proxy_api(self, method):
        return eval('self._%s__client.%s' % (self.__class__.__name__, method))


"""
    ZABBIX Adapter
"""


class ZabbixAPIException(Exception):
    pass


class ZabbixAPI(object):
    """ Zabbix 2.0 API for Python

    Usage:

        zapi = ZabbixAPI(
            url='http://127.0.0.1/zabbix', user='your-name',
            password='your-password')
        zapi.login()
        result = zapi.host.get(
            {
                'output': ['hostid', 'name', 'status'],
                'selectInterfaces': ['interfaceid', 'ip'],
                'filter': {'hostid': ''}
            })

    Supported Objects:

        action, alert, apiinfo, application, dcheck,
        dhost, drule, dservice, event, draph, draphitem,
        history, host, hostgroup, hostinterface, image,
        item, maintenance, map, mediatype, proxy, screen,
        script, template, trigger, user, usergroup,
        usermacro, usermedia

    More object details see:

        https://www.zabbix.com/documentation/2.4/manual/api

    Note: Objects haven't been list upon may not be supported by ZabbixAPI.
    """
    __auth = ''
    __id = 0
    _state = {}

    # create a new ZabbixAPI Object if not exists
    def __new__(cls, *args, **kw):
        if cls not in cls._state:
            cls._state[cls] = super(ZabbixAPI, cls).__new__(cls, *args, **kw)
        return cls._state[cls]

    # constructor : zabbix api's [url, username, userpassword, object list]
    def __init__(self, url, user, password):
        self.__url = url.rstrip('/') + '/api_jsonrpc.php'
        self.__user = user
        self.__password = password
        self._zabbix_api_object_list = (
            'action', 'alert', 'apiinfo', 'application', 'dcheck',
            'dhost', 'drule', 'dservice', 'event', 'draph', 'draphitem',
            'history', 'host', 'hostgroup', 'hostinterface', 'image',
            'item', 'maintenance', 'map', 'mediatype', 'proxy', 'screen',
            'script', 'template', 'trigger', 'user', 'usergroup',
            'usermacro', 'usermedia')

    # create a ZabbixAPIObjectFactory Object
    # named 'Action', 'Alert', ..., as a member of self
    def __getattr__(self, name):
        name = name.lower()
        if name not in self._zabbix_api_object_list:
            raise ZabbixAPIException('No such Zabbix API object: %s' % name)
        if name not in self.__dict__:
            self.__dict__[name] = ZabbixAPIObjectFactory(self, name)
        return self.__dict__[name]

    # user login for zabbix api which returns an authorization token
    # as self.__auth
    def login(self):
        user_info = {'user': self.__user,
                     'password': self.__password}
        obj = self.json_obj('user.login', user_info)
        try:
            content = self.post_request(obj)
        except urllib2.HTTPError:
            raise ZabbixAPIException('Zabbix URL Error')
        try:
            self.__auth = content['result']
        except KeyError, e:
            e = content['error']['data']
            raise ZabbixAPIException(e)

    # check user login status for zabbix
    def is_login(self):
        return self.__auth != ''

    # check user authorization for zabbix
    def __checkAuth__(self):
        if not self.is_login():
            raise ZabbixAPIException('Zabbix NOT Logged In')

    # jsonify parameters for zabbix api request
    def json_obj(self, method, params):
        obj = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': self.__id}
        if method != 'user.login':
            obj['auth'] = self.__auth
        return json.dumps(obj)

    # request a zabbix api
    def post_request(self, json_obj):
        headers = {'Content-Type': 'application/json',
                   'User-Agent': 'ZabbixAPI'}
        req = urllib2.Request(self.__url, json_obj, headers)
        opener = urllib2.urlopen(req)
        content = json.loads(opener.read())
        self.__id += 1
        return content


# add to verify authorization
def zabbix_check_auth(func):
    def ret(self, *args):
        self.__checkAuth__()
        return func(self, *args)
    return ret


# add to get pure zabbix api response
def zabbix_api_object_method(func):
    def wrapper(self, method_name, params):
        try:
            content = self.post_request(self.json_obj(method_name, params))
            return content['result']
        except KeyError, e:
            e = content['error']['data']
            raise ZabbixAPIException(e)
    return wrapper


class ZabbixAPIObjectFactory(object):
    """ Zabbix 2.0 API Object API (Action, Alert, Host, Item, etc.)
    """
    # the construtor
    def __init__(self, zapi, object_name=''):
        # a ZabbixAPI Object
        self.__zapi = zapi
        # a zabbix api object name like 'Action', 'Alert', ...
        self.__object_name = object_name

    # verify user authorization for zabbix using the ZabbixAPI Object
    def __checkAuth__(self):
        self.__zapi.__checkAuth__()

    # request a zabbix api using the ZabbixAPI Object
    def post_request(self, json_obj):
        return self.__zapi.post_request(json_obj)

    # jsonify parameters for zabbix api request using the ZabbixAPI Object
    def json_obj(self, method, param):
        return self.__zapi.json_obj(method, param)

    # request a zabbix api object's inner method __object_name.method_name
    # like "host.get", "host.create", ...
    def __getattr__(self, method_name):
        def method(params):
            return self.proxy_method(
                '%s.%s' % (self.__object_name, method_name), params)
        return method

    # the request proxy method
    @zabbix_check_auth
    @zabbix_api_object_method
    def proxy_method(self, method_name, params):
        pass


"""
    MYSQL Adapter
"""
from MySQLdb import Connection
from MySQLdb.cursors import DictCursor


class MySQLAPIException(Exception):
    pass


# check if database is connected
def db_check_connect(func):
    def ret(self, *args, **kwargs):
        self.__checkStatus__()
        return func(self, *args, **kwargs)
    return ret


class MySQLAPI(object):
    """ MySQL API

    Usage:

        client = MySQLAPI(
            host='127.0.0.1', port=3306, user='your-name',
            password='your-password', db='your-database-name')
        client.connect()
        result = client.query('select * from table_a')

    """
    __connected = False

    def __init__(
            self, host, port, user, password, db, timeout=3):
        self.__host = host
        self.__user = user
        self.__password = password
        self.__db = db
        self.__port = port
        self.__timeout = timeout

    def connect(self):
        try:
            self.__connect = Connection(
                host=self.__host, user=self.__user, passwd=self.__password,
                db=self.__db, port=self.__port, connect_timeout=self.__timeout)
            self.__cursor = self.__connect.cursor(DictCursor)
            self.__connected = True
        except Exception as e:
            raise MySQLAPIException(e)

    # connection status for etcd
    def is_connect(self):
        return self.__connected

    # check connection status for etcd
    def __checkStatus__(self):
        if not self.is_connect():
            raise MySQLAPIException('Database NOT Connected')

    def __del__(self):
        try:
            if self.is_connect():
                self.__cursor = None
                self.__connect.close()
                self.__connected = False
        except Exception as e:
            raise MySQLAPIException(e)

    @db_check_connect
    def query(self, sql):
        try:
            self.__cursor.execute(sql)
            return self.__cursor.fetchall()
        except Exception as e:
            raise MySQLAPIException(e)


"""
    MINIO Adapter
"""
from minio import Minio


class MinioAPIException(Exception):
    pass


# check if minio server is connected
def minio_check_connect(func):
    def ret(self, method):
        self.__checkStatus__()
        return func(self, method)
    return ret


class MinioAPI(object):
    """ Minio API

    Usage:

        client = MinioAPI(
            endpoint='127.0.0.1:9000', access_key='your-access-key',
            secret_key='your-secret-key')
        client.connect()
        objects = client.list_objects(
            bucket_name='mybucket', prefix='myprefix', recursive=False)


    Bucket Options:

    :method make_bucket                : Creates a new bucket.
        param bucket_name
        param location (defaults to 'us-east-1')
    :method list_buckets               : Lists all buckets.
    :method bucket_exists              : Checks if a bucket exists.
        param bucket_name
    :method remove_bucket              : Removes a bucket.
        param bucket_name
    :method list_objects               : Lists objects in a bucket.
        param bucket_name
        param prefix
        param recursive (defaults to False)
    :method list_incomplete_uploads    : Lists partially uploaded objects in a
                                        bucket.
        param bucket_name
        param prefix
        param recursive (defaults to False)

    Object Options:

    :method get_object                 : Downloads an object.
        :param bucket_name
        :param object_name
        :param request_headers (defaults to None)
    :method put_object                 : Add a new object to the object storage
                                         server.
        :param bucket_name
        :param object_name
        :param data
        :param length
        :param content_type (defaults to 'application/octet-stream')
        :param metadata (defaults to None)
    :method copy_object                : Copy a source object on object storage
                                         server to a new object.
        :param bucket_name
        :param object_name
        :param object_source
        :param copy_conditions (defaults to None)
    :method stat_object                : Gets metadata of an object.
        :param bucket_name
        :param object_name
    :method remove_object              : Removes an object.
        :param bucket_name
        :param object_name
    :method remove_objects             : Removes multiple objects in a bucket.
        :param bucket_name
        :param objects_iter (should be list , tuple or iterator)
    :method fput_object                : Uploads contents from a file to object
                                         name.
        :param bucket_name
        :param object_name
        :param file_path
        :param content_type (defaults to 'application/octet-stream')
        :param metadata (defaults to None)
    :method fget_object                : Downloads and saves the object as a
                                         file in the local filesystem.
        :param bucket_name
        :param object_name
        :param file_path
        :param request_headers (defaults to None)
    :method remove_incomplete_upload   : Removes a partially uploaded object.
        :param bucket_name
        :param object_name

    More method details see:

        https://docs.minio.io/docs/python-client-api-reference
        https://github.com/minio/minio-py/blob/master/minio/api.py

    Note: Methods haven't been list upon may not be supported by MinioAPI.
    """
    __connected = False

    def __init__(self, endpoint, access_key, secret_key, secure=False):
        self.__endpoint = endpoint
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__secure = secure
        self._method = frozenset(
            ['make_bucket', 'remove_bucket', 'list_buckets', 'bucket_exists',
             'list_objects', 'get_object', 'put_object', 'copy_object',
             'stat_object', 'remove_object', 'remove_objects', 'fput_object',
             'fget_object', 'list_incomplete_uploads',
             'remove_incomplete_upload'])

    def connect(self):
        self.__client = Minio(
            endpoint=self.__endpoint, access_key=self.__access_key,
            secret_key=self.__secret_key, secure=self.__secure)
        self.__connected = True

    def disconnect(self):
        self.__client = None
        delattr(self, '_MinioAPI__client')
        self.__connected = False

    # connection status for minio
    def is_connect(self):
        return self.__connected

    # check connection status for minio
    def __checkStatus__(self):
        if not self.is_connect():
            raise MinioAPIException('Minio NOT Connected')

    def __getattr__(self, method):
        def func(*args, **kwargs):
            if method not in self._method:
                raise MinioAPIException('No Such Minio API: %s' % method)
            return self.proxy_api(method=method)(*args, **kwargs)
        return func

    @minio_check_connect
    def proxy_api(self, method):
        return eval('self._%s__client.%s' % (self.__class__.__name__, method))


import redis


def init_redisclient(host, port, password, db=0):
    redis_pool = redis.ConnectionPool(
        host=host, port=port, password=password, db=db)
    return redis.Redis(connection_pool=redis_pool)
