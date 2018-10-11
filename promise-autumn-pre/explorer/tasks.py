# -*- coding:utf-8 -*-
# !/usr/bin/env python
#
# Author: Shawn.T
# Email: shawntai.ds@gmail.com
#
# This is the model module for the user package
# holding user, token, role and  privilege models, etc.
#
from __future__ import absolute_import

import json
import os

from celery.result import AsyncResult
from gryphon.api import Ansible2API as AnsibleAPI

from . import utils
from .models import Explorer


from celery import Celery
from explorer.application import app as backend


def make_celery(application):
    _celery = Celery(application.import_name,
                     broker=application.config['CELERY_BROKER_URL'],
                     include=['explorer.tasks'])
    _celery.conf.update(application.config)
    task_base_cls = _celery.Task

    class ContextTask(task_base_cls):
        abstract = True

        def __call__(self, *args, **kwargs):
            with application.app_context():
                return task_base_cls.__call__(self, *args, **kwargs)

    _celery.Task = ContextTask
    return _celery


app = make_celery(backend)


@app.task(bind=True, name='fetch_task',
          queue='filesync', ignore_result=True)
def fetch_task(self, remote_paths_ips, bkname, local_path):
    self.update_state(state='FETCHING')
    temp_fetch_folder = utils.temp_fetch_folder()
    state, stats_sum, results = fetch_file(remote_paths_ips, temp_fetch_folder)
    if state:
        app.logger.error(utils.logmsg(json.dumps(results)))
        self.update_state(state='FETCHING_FAILD')
    app.logger.info(utils.logmsg('file(s) fetched.'))
    self.update_state(state='UPLOADING')
    explorer = Explorer(is_minio=True)
    try:
        explorer.save_to_minio(local_folderpath=temp_fetch_folder,
                               bkname=bkname,
                               prefix=local_path)
    except Exception as e:
        app.logger.error(e)
        self.update_state(state='UPLOADING_FAILD')
    app.logger.info(utils.logmsg('file(s) uploaded info minio.'))
    self.update_state(state='SUCCESS')


def fetch_task_forapplet(remote_paths_ips, bkname, local_path):
    temp_fetch_folder = utils.temp_fetch_folder()
    state, stats_sum, results = fetch_file(remote_paths_ips, temp_fetch_folder)
    if state:
        app.logger.error(utils.logmsg(json.dumps(results)))
        return state, stats_sum, results, 'FETCHING_FAILD'
    app.logger.info(utils.logmsg('file(s) fetched.'))

    explorer = Explorer(is_minio=True)
    try:
        explorer.save_to_minio(local_folderpath=temp_fetch_folder,
                               bkname=bkname,
                               prefix=local_path)
    except Exception as e:
        app.logger.error(e)
        return 1, stats_sum, results, 'UPLOADING_FAILD'
    app.logger.info(utils.logmsg('file(s) uploaded info minio.'))
    return state, stats_sum, results, 'SUCCESS'


def fetch_file(remote_paths_ips, temp_fetch_folder):
    tt_state = 0
    tt_stats_sum = dict()
    tt_results = dict()
    for path_ips in remote_paths_ips:
        ansible = AnsibleAPI(hosts=path_ips['ips'])
        file_path = path_ips['path']
        args = 'src=%s dest=%s/{{ inventory_hostname }}-%s flat=yes' % \
               (file_path, temp_fetch_folder, os.path.basename(file_path))
        [state, stats_sum, results] = ansible.run(module='fetch', args=args)
        tt_state = tt_state + state
        tt_stats_sum = dict(tt_stats_sum, **stats_sum)
        tt_results = dict(tt_results, **results)
    return tt_state, tt_stats_sum, tt_results


def get_task_status(task_id):
    res = AsyncResult(task_id, app=app)
    return res.status
