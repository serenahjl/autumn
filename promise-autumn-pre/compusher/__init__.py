
# !/usr/bin/env python
#  -*- coding:utf-8 -*-

from __future__ import absolute_import
import os
from logging import Formatter
from logging.handlers import RotatingFileHandler
from flask import Flask, make_response, json
from flask.ext.restful import Api
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cors import CORS
from flask.ext.cachecontrol import FlaskCacheControl



import config


# initialize flask object
app = Flask(__name__, instance_relative_config=True)

# config.py in folder 'instance' may cover the default config object.
app.config.from_object(config)
if os.path.isfile(os.path.join(app.instance_path, 'config.py')):
    app.config.from_pyfile('config.py')

# initialize folders
if not os.path.exists(app.config['DATA_FOLDER']):
    os.mkdir(app.config['DATA_FOLDER'])
if not os.path.exists(app.config['TMP_FOLDER']):
    os.mkdir(app.config['TMP_FOLDER'])
if not os.path.exists(app.config['LOG_FOLDER']):
    os.mkdir(app.config['LOG_FOLDER'])

# initialize api
api = Api(app)


@api.representation('application/json')
def responseJson(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp

# initialize db
db = SQLAlchemy(app)


# initialize the logging handler
log_handler = RotatingFileHandler(app.config['LOGGER_FILE'],
                                  maxBytes=102400,
                                  backupCount=1)
log_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
log_handler.setLevel(app.config['DEFAULT_LOGLEVEL'])

app.logger.addHandler(log_handler)

# initialize cors
cors = CORS(app, allow_headers='*', expose_headers='Content-Disposition')

# initialize cache control
flask_cache_control = FlaskCacheControl()
flask_cache_control.init_app(app)

# celery init
from celery import Celery

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)


from .interface import CompnAPI, CompnInstAPI
from . import api, app

api.add_resource(
    CompnAPI, '/api/' + app.config['API_VERSION'] + '/compusher/compn',
    endpoint='compn_ep')
# api.add_resource(
#     FilesAPI, '/api/' + app.config['API_VERSION'] + '/compusher/files',
#     endpoint='compn_files_ep')
api.add_resource(
    CompnInstAPI, '/api/' + app.config['API_VERSION'] + '/compusher/compn_inst',
    endpoint='compn_inst_ep')