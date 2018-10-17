#!/usr/bin/env.conf python
# -*- coding:utf-8 -*-
#
# Author: Shawn.T, Leann Mak
# Email: shawntai.ds@gmail.com, leannmak@139.com
#
# This is the config file of global package of promise.
# You can create your own instance/config.py which will cover this file.
# Also instance/nosetests_config.py has higher priority when testing.
#
import os
import logging

"""
    common
"""
API_VERSION = 'v0.0'
# ENVIRONMENTS = ('qa', 'online')
ENVIRONMENTS = ('qa', )
POOLS = ('nfjd', 'bfjd')
ABS_BASEDIR = os.path.split(os.path.realpath(__file__))[0]
BASEDIR = os.path.abspath(os.path.dirname('..'))
DATA_FOLDER = os.path.join(BASEDIR, '.data')
LOG_FOLDER = os.path.join(BASEDIR, '.log')
LOGGER_FILE = os.path.join(LOG_FOLDER, 'debug.log')
TMP_FOLDER = os.path.join(BASEDIR, '.tmp')
CA_FOLDER = os.path.join(BASEDIR, '.ca')
UPLOAD_FOLDER = os.path.join(DATA_FOLDER, 'upload')
BACKUP_FOLDER = os.path.join(DATA_FOLDER, 'backup')
DEFAULT_LOGLEVEL = logging.ERROR
STORAGE_FOLDER = '/apps/sharedstorage'


"""
    database
"""
# database access string setting, by default we use mysql
# for common using
SQLALCHEMY_DATABASE_URI = 'mysql://root@127.0.0.1:3306/common'
# for eater:
SQLALCHEMY_BINDS = {
    'eater': 'mysql://root@127.0.0.1:3306/common',
    'spider': 'mysql://root@127.0.0.1:3306/common'
}
SQLALCHEMY_POOL_RECYCLE = 5
PROPAGATE_EXCEPTIONS = True


"""
    celery
"""
# CELERY_BROKER_URL = 'amqp://promise-dev-ci:111111@192.168.182.52:5672/devci'
CELERY_BROKER_URL = 'amqp://guest@localhost//'
CELERY_RESULT_BACKEND = 'amqp'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = True
CELERYBEAT_SCHEDULE_FILENAME = os.path.join(DATA_FOLDER, 'celerybeat-schedule')
# CELERY_IGNORE_RESULT = True
# CELERY_TRACK_STARTED = True
# CELERY_REDIRECT_STDOUTS_LEVEL = 'DEBUG'
# CELERY_IMPORTS = ['promise.brusher.tasks', 'promise.eater.tasks']
# CELERYD_POOL_RESTARTS = True
from kombu import Queue, Exchange
from kombu.common import Broadcast
DEFAULT_EXCHANGE = Exchange('promise')
CELERY_QUEUES = (
    Broadcast('compupdate', exchange=DEFAULT_EXCHANGE),
    Queue('mail', DEFAULT_EXCHANGE, routing_key='mail'),
    Queue('applet', DEFAULT_EXCHANGE, routing_key='applet'),
    Queue('compn', DEFAULT_EXCHANGE, routing_key='compn'),
    Queue('cmdb', DEFAULT_EXCHANGE, routing_key='cmdb'),
    Queue('period', DEFAULT_EXCHANGE, routing_key='period'),
    Queue('virtman', DEFAULT_EXCHANGE, routing_key='virtman'))
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'

CELERYD_TASK_TIME_LIMIT = 600
CELERYD_TASK_SOFT_TIME_LIMIT = 300

from celery import platforms
platforms.C_FORCE_ROOT = True
platforms.PYTHONOPTIMIZE = 1



"""
    ansible
"""
ANSIBLE_REMOTE_USER = 'apps'
ANSIBLE_BECOME_METHOD = 'sudo'
ANSIBLE_REMOTE_USER_PASSWORDS = dict(conn_pass='8UJ0yRaG', become_pass='')
ANSIBLE_SSH_KEY = ''


"""
    user module
"""
# encryption keys
SECRET_KEY = 'your SECRET_KEY'
# salt used by token generation
AUTH_SALT = 'your AUTH SALT'
# salt used by password md5 hash
PSW_SALT = 'your PSW SALT'
# token duration (in seconds), 2hours by default
# TOKEN_DURATION = 7200  # in second
ACCESS_TOKEN_EXPIRATION = 3600  # in second
REFRESH_TOKEN_EXPIRATION = 86400  # in second
# root user default setting
DEFAULT_ROOT_USERNAME = 'admin'
DEFAULT_ROOT_PASSWORD = 'admin'
PRIV_SETTINGS = list()
PRIV_SETTINGS.append(dict(priv_name='userAdmin', description='用户管理权限'))
PRIV_SETTINGS.append(dict(priv_name='inventoryAdmin', description='配置管理权限'))
PRIV_SETTINGS.append(dict(priv_name='shellExec', description='shell执行权限'))
PRIV_SETTINGS.append(dict(priv_name='scriptExec', description='脚本执行权限'))
PRIV_SETTINGS.append(dict(priv_name='sceneCrt', description='场景小程序执行权限'))
PRIV_SETTINGS.append(dict(priv_name='sceneExec', description='场景小程序创建权限'))
PRIV_SETTINGS.append(dict(priv_name='compnmgmt', description='组件管理权限'))
PRIV_SETTINGS.append(dict(priv_name='basePriv', description='基础权限'))
PRIV_SETTINGS.append(dict(priv_name='networkInfoMan', description='网络信息维护权限'))
PRIV_SETTINGS.append(dict(priv_name='networkExec', description='网络管理权限'))




"""
    compush module
"""
COMPN_PBS_BKNAME = 'playbooks'
COMPN_ROLES_BKNAME = 'roles'
COMPN_PKGS_BKNAME = 'pkgs'
COMPN_REMOTE_USER = 'apps'
COMPN_SSH_KEY = os.path.join(BASEDIR, '.ssh_key/apps_id_rsa')


"""
    email configuration
"""
PROMISE_MAIL = "ecloudops@yeah.net"
# MAIL_AUTHS = list()
# MAIL_AUTHS.append(dict(
#     MAIL_SERVER='123.58.177.132', MAIL_PORT=25, MAIL_USE_TLS=False,
#     MAIL_USERNAME='ecloudops@yeah.net', MAIL_PASSWORD='Ecloud10086nj'))
# MAIL_AUTHS.append(dict(
#     MAIL_SERVER='220.181.15.112', MAIL_PORT=25, MAIL_USE_TLS=False,
#     MAIL_USERNAME='ecloudops@126.com', MAIL_PASSWORD='Ecloud10086nj'))

"""
    minio
"""
MINIO_ENDPOINT = '192.168.182.2:9000'
MINIO_ACCESS_KEY = '7M3LTEM3H3MVIYAV2U3I'
MINIO_SECRET_KEY = 'LJqZRt/gL/WEjg3i6hLT1wjYcEmd7QtQ7EzlOQeZ'
MINIO_SECURE = False

"""
    redis
"""
REDIS_HOST = '192.168.182.51'
REDIS_PORT = 6379
REDIS_PWD = 'qwe123'



"""
    Kong & privileges
"""
KONGADM_URL = 'http://192.168.182.52:8001'
KONGADM_APIKEY = None
KONGADM_BASICAUTH_USERNAME = None
KONGADM_BASICAUTH_PASSWORD = None

ANONYMOUS_API_NAMES = ['auth',
                       'spiderman-options',
                       'virtman-options',
                       'dora-options',
                       'butler-options',
                       'jarvis-options',
                       'agamotto-options',
                       'explorer-options',
                       'applet-options',
                       'sakura-options',
                       'magneto-options']
NOACL_API_NAMES = ['butler-user-myself', 'token']

DEFAULT_ROOT_USERNAME = 'admin'
DEFAULT_ROOT_PASSWORD = 'admin'
DEFAULT_ROOT_ROLENAME = 'root_role'
# DEFAULT_BASE_ROLENAME = 'base_role'

# encryption keys
SECRET_KEY = 'your SECRET_KEY'
# salt used by token generation
AUTH_SALT = 'your AUTH SALT'
# salt used by password md5 hash
PSW_SALT = 'your PSW SALT'

"""
    kong
"""
KONG_URL = 'http://172.40.224.15:8000'
KONG_USER = 'butler'
KONG_PWD = '0f3ea81cc87742c74dff0abac1d6bcc45356bd7e52c' \
           'c852866d6d0fb53980e2a72d03fe4321b573503fd8c' \
           '7f3c9a35572d0a5208dd3ba982f457aa174423506b'


