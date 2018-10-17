# -*- coding:utf-8 -*-
# !/usr/bin/env.conf python

"""
    database
"""
SQLALCHEMY_DATABASE_URI = 'mysql://root@192.168.182.51:3306/autumn-ci'
SQLALCHEMY_POOL_RECYCLE = 5
PROPAGATE_EXCEPTIONS = True

"""
    celery
"""
CELERY_BROKER_URL = 'amqp://promise-dev-ci:111111@192.168.182.52:5672/autumn-ci'
CELERY_RESULT_BACKEND = 'rpc://'

"""
    redis
"""
REDIS_HOST = '192.168.182.51'
REDIS_PORT = 6379
REDIS_PWD = 'qwe123'