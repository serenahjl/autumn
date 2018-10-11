# -*- coding:utf-8 -*-
# !/usr/bin/env python
#
# Author: Shawn.T
# Email: dai.sheng@139.com
#
# This is the model module for the compenont package


from . import db, app
from . import utils
from . import exception
#from ..user.models import User, Role
from butler import user
from explorer.explorer import ExplorerInf
from sqlalchemy import and_, or_
from sqlalchemy.dialects.mysql import TEXT, LONGTEXT
# from .. import celery
from . import celery
from celery.contrib.methods import task_method
import datetime
import json
import re
import os
from celery.exceptions import SoftTimeLimitExceeded
#from promise.eater.interfaces import toWalkerGetPass, toWalkerAddSoftware, toWalkerGetHost
#from promise.eater.interfaces import toWalkerGetGroup, toWalkerGetResponsible, toWalkerGetEnv
#from promise.eater.interfaces import toWalkerCheckTemplate, toWalkerGetOwner, toWalkerGetPassAndIP
#from promise.adapter.models import AnsibleAPIwithPasswd
from gryphon.api import Ansible2API
#from promise.eater.models import Responsibility, Software, OSUser


class Enum(tuple):
    __getattr__ = tuple.index


COMPNINST_STATE = Enum(['compn_not_ready', 'pending', 'running', 'faild', 'success', 'timeout'])
pbs_path = os.path.join(app.config['STORAGE_FOLDER'], app.config['COMPN_PBS_BKNAME'])


class Compn(db.Model):
    """
    component model
    components' roles folder, yml file & config template files will be saved in
    'COMPN_FOLDER/<compn_id>'
    the path is,
    * roles folder: COMPN_FOLDER/<compn_id>/<roles_name>
    * yml file: COMPN_FOLDER/<compn_id>/<roles_name>
    * config files: COMPN_FOLDER/<compn_id>/<config_template_name>
    """
    __tablename__ = 'compn'
    compn_id = db.Column(db.String(64), primary_key=True)
    compn_name = db.Column(db.String(64), nullable=False)
    description = db.Column(TEXT)

    #owner_id = db.Column(db.String(64), db.ForeignKey('user.user_id'))

    deleted = db.Column(db.SmallInteger, nullable=False)
    call_times = db.Column(db.BigInteger)

    # for component push playbooks
    default_params = db.Column(db.TEXT)
    yml_fname = db.Column(db.String(64))

    # for eater
    # eater_version = db.Column(db.String(64), nullable=False)
    # eater_owner_id = db.Column(db.String(64))
    # eater_port = db.Column(db.Integer)
    # eater_reload_cmd = db.Column(db.TEXT)
    # eater_check_cmd = db.Column(db.TEXT)
    # eater_runtime_id = db.Column(db.String(64))
    # eater_mid_type = db.Column(db.String(64))

    # configuration files
    confs = db.relationship('Conf', backref='compn', lazy='dynamic')
    compninsts = db.relationship('CompnInst', backref='compn', lazy='select')

    def __repr__(self):
        return '<compn %r>' % self.compn_id

    def __init__(
            self, compn_name, description, owner, yml_fname,
            #eater_reload_cmd, eater_version=None, eater_owner_id=None, eater_port=None,
           # eater_runtime_id=None, eater_mid_type=None,
            confs=None, deleted=0, default_params=None):
        self.compn_id = utils.genUuid()
        self.compn_name = compn_name
        self.description = description
        self.owner_id = owner.user_id
        self.yml_fname = yml_fname

        if default_params is not None:
            self.default_params = default_params

        # self.eater_reload_cmd = eater_reload_cmd
        # if eater_version is not None:
        #     self.eater_version = eater_version
        # else:
        #     self.eater_version = 'v1.0'
        #
        # if eater_port is not None and eater_port is not '':
        #     self.eater_port = eater_port
        # if eater_runtime_id is not None:
        #     self.eater_runtime_id = eater_runtime_id
        # if eater_mid_type is not None:
        #     self.eater_mid_type = eater_mid_type
        #
        # if eater_owner_id is not None:
        #     self.eater_owner_id = eater_owner_id
        # else:
        #     eater_owner = OSUser.query.filter_by(name=app.config['COMPN_REMOTE_USER']).first()
        #     if eater_owner is not None:
        #         self.eater_owner_id = eater_owner.id

        self.deleted = 0
        self.call_times = 0

    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
            msg = utils.logmsg('save compn:' + self.compn_id)
            app.logger.debug(msg)
            state = True
        except Exception, e:
            db.session.rollback()
            msg = utils.logmsg('exception: %s.' % e)
            app.logger.info(msg)
            state = False
        return [state, msg]

    def update(self, yml_fname=None, compn_name=None, description=None,
               #eater_reload_cmd=None, eater_version=None, eater_port=None, eater_runtime_id=None,
               #eater_mid_type=None, eater_owner_id=None,
               confs=None, default_params=None,):
        if yml_fname is not None:
            self.yml_fname = yml_fname
        if compn_name is not None:
            self.compn_name = compn_name
        if description is not None:
            self.description = description

        if default_params is not None:
            self.default_params = default_params

        # if eater_reload_cmd is not None:
        #     self.eater_reload_cmd = eater_reload_cmd
        # if eater_version is not None:
        #     self.eater_version = eater_version
        # if eater_port is not None and eater_port is not '':
        #     self.eater_port = eater_port
        # if eater_runtime_id is not None:
        #     self.eater_runtime_id = eater_runtime_id
        # if eater_mid_type is not None:
        #     self.eater_mid_type = eater_mid_type
        # if eater_owner_id is not None:
        #     self.eater_owner_id = eater_owner_id

        if confs is not None:
            self.confs = confs
        [state, msg] = self.save()
        return [state, msg]

    def delete(self):
        self.deleted = 1
        [state, msg] = self.save()
        if not state:
            app.logger.error(utils.logmsg(msg))
            return [False, 'delete compn faile ' + self.compn_id]
        return [True, 'applet ' + self.compn_id + ' deleted.']

    def chk_files_status(self):
        ex = ExplorerInf(is_minio=False)
        if not ex.file_exists(bkname=app.config['COMPN_PBS_BKNAME'], filepath=self.yml_fname):
            return [False, 'compn playbook file not exists.']
        return [True, 'component playbook file ready.']

    @classmethod
    def get_compns(cls, compn_name=None, compn_id=None, owner_id=None, deleted=0):
        args = dict()
        if compn_name is not None:
            args['compn_name'] = compn_name
        if compn_id is not None:
            args['compn_id'] = compn_id
        if owner_id is not None:
            args['owner_id'] = owner_id
        if deleted is not None:
            args['deleted'] = deleted
        return cls.query.filter_by(**args).all()

    def get_dict_info(self):
        ext_dict = dict()

        # get owner info

        owner = User.query.get(self.owner_id)
        ext_dict['owner'] = owner.get_short_dict_info()

        # eater_owner = toWalkerGetOwner(self.eater_owner_id)
        # if eater_owner is not None:
        #     ext_dict['eater_owner'] = eater_owner.to_dict(ignore=['conn_pass', 'it', 'software'])
        # else:
        #     ext_dict['eater_owner'] = dict(eater_owner_id=self.eater_owner_id)

        compn_info = utils.to_dict(
            self, except_clm_list=['deleted', 'owner_id', 'eater_owner_id_try'], ext_dict=ext_dict)

        return compn_info

    def add_calltimes(self):
        self.call_times += 1
        return self.save()


class Conf(db.Model):
    """
    configuration model
    configuration file saved in minio:/compn/<compn_id>/<fname>
    """
    __tablename__ = 'conf'
    conf_id = db.Column(db.String(64), primary_key=True)
    fname = db.Column(db.String(64), nullable=False)
    compn_id = db.Column(db.String(64), db.ForeignKey('compn.compn_id'), nullable=False)
    description = db.Column(TEXT)
    keys = db.Column(TEXT)
    deleted = db.Column(db.SmallInteger, nullable=False)

    def __init__(self, fname, path, compn, deleted=0, description=None, keys=None):
        self.conf_id = utils.genUuid()
        self.fname = fname
        self.compn_id = compn.compn_id
        self.description = description
        self.keys = ','.join(keys)
        self.deleted = deleted


class CompnInst(db.Model):
    """docstring for CompnInst"""
    __tablename__ = 'compn_inst'
    compninst_id = db.Column(db.String(64), primary_key=True)
    description = db.Column(TEXT)
    #owner_id = db.Column(db.String(64), db.ForeignKey('user.user_id'))
    #假owner_id
    owner_id = db.Column(db.String(64))
    deleted = db.Column(db.SmallInteger, nullable=False)
    compn_id = db.Column(db.String(64), db.ForeignKey('compn.compn_id'), nullable=False)

    hosts_params = db.Column(TEXT)

    time_create = db.Column(db.DATETIME)
    time_begin = db.Column(db.DATETIME)
    time_ended = db.Column(db.DATETIME)

    state = db.Column(db.SmallInteger)
    result_details = db.Column(LONGTEXT)
    result_stats_sum = db.Column(TEXT)
    result_state = db.Column(db.SmallInteger)

    software_id = db.Column(db.String(64))

    def __init__(self, compn, description, owner, hosts_params, deleted=0):
        self.compninst_id = utils.genUuid()
        self.compn_id = compn.compn_id
        self.description = description
        self.owner_id = owner.user_id
        self.hosts_params = json.dumps(hosts_params)
        self.deleted = deleted
        [state, msg] = compn.chk_files_status()
        print msg
        if not state:
            self.state = COMPNINST_STATE.compn_not_ready
        else:
            self.state = COMPNINST_STATE.pending
        self.time_create = datetime.datetime.utcnow()
        compn.add_calltimes()

    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
            msg = utils.logmsg('save compn_inst:' + self.compninst_id)
            app.logger.debug(msg)
            state = True
        except Exception, e:
            db.session.rollback()
            msg = utils.logmsg('exception: %s.' % e)
            app.logger.info(msg)
            state = False
        return [state, msg]

    def set_state(self, state):
        self.state = state
        return self.save()

    @classmethod
    def get_compninsts(cls, compninst_id=None, compn_id=None, owner_id=None, deleted=0):
        args = dict()
        if compninst_id is not None:
            args['compninst_id'] = compninst_id
        if compn_id is not None:
            args['compn_id'] = compn_id
        if owner_id is not None:
            args['owner_id'] = owner_id
        if deleted is not None:
            args['deleted'] = deleted
        return cls.query.filter_by(**args).all()

    def get_dict_info(self):
        ext_dict = dict()

        # get owner info
        owner = User.query.get(self.owner_id)
        ext_dict['owner'] = owner.get_short_dict_info()

        # get compn info
        compn = Compn.query.get(self.compn_id)
        ext_dict['compn'] = compn.get_dict_info()
        ext_dict['state'] = COMPNINST_STATE[self.state]
        ext_dict['result_stats_sum'] = utils.try_load_json(self.result_stats_sum)
        ext_dict['hosts_params'] = utils.try_load_json(self.hosts_params)
        if isinstance(ext_dict['result_stats_sum'], dict):
            ext_dict['ip_list'] = ext_dict['result_stats_sum'].keys()
        # if self.software_id is not None:
        #     software = Software().getObject(id=self.software_id)
        #     if software:
        #         ext_dict['software'] = software.to_dict()

        compninst_info = utils.to_dict(
            self,
            except_clm_list=['deleted', 'owner_id', 'hosts_params', 'result_stats_sum'],
            ext_dict=ext_dict)

        return compninst_info

    @celery.task(
        bind=True, filter=task_method, name='compn_execute', queue='compn', ignore_result=True)
    def asyn_push(task_self, self):
        self.push()

    def push(self):
        if self.state == COMPNINST_STATE.compn_not_ready:
            app.logger.error('compn not ready.')
            raise exception.ServerError('compn not ready.')
        run_data = {'compninst_id': self.compninst_id}

        compn = Compn.get_compns(compn_id=self.compn_id)[0]

        hosts_params = json.loads(self.hosts_params)
        host_pass_list = list()
        hosts = list()
        for host_params in hosts_params:

            # hosts.append(toWalkerGetHost(id=host_params['host_id']))
            # ip, password = toWalkerGetPassAndIP(
            #     owner_id=compn.eater_owner_id,
            #     host_id=host_params['host_id'])
#            if password is None:
#                password = toWalkerGetPass(name=app.config['COMPN_REMOTE_USER'])
            host_pass_list.append({
                'host': 'ip_try',
                'params': host_params['params']})
        playbook = "%s/%s" % (pbs_path, compn.yml_fname)
        pb_exec = Ansible2API(
            remote_user=app.config['COMPN_REMOTE_USER'],
            key_file=None,
            become_user=app.config['COMPN_REMOTE_USER'],
            host_pass_list=host_pass_list)
        software = None
        try:
            self.set_state(COMPNINST_STATE.running)
            self.time_begin = datetime.datetime.utcnow()
            self.save()
            result_state, result_stats_sum = pb_exec.run_pb(
                playbook_path=playbook, run_data=run_data)

            self.save_result(result_state, result_stats_sum)
            if not result_state:
                self.set_state(COMPNINST_STATE.success)
                #software = self.eater_save(hosts)
                if software is not None:
                    self.software_id = software['id']
                    self.save()
            else:
                self.set_state(COMPNINST_STATE.faild)

        except SoftTimeLimitExceeded:
            self.set_state(COMPNINST_STATE.timeout)
        except Exception as e:
            msg = "run ansible exceptions: %s" % e.message
            self.save_result_details(msg)
            self.set_state(COMPNINST_STATE.faild)

        finally:
            self.time_ended = datetime.datetime.utcnow()
            self.save()
        return software

    def save_result_details(self, msg):
        self.result_details = msg
        return self.save()

    def save_result(self, result_state, result_stats_sum):
        self.result_state = int(result_state)
        self.result_stats_sum = json.dumps(result_stats_sum)
        if result_state:
            self.state = COMPNINST_STATE.faild
        else:
            self.state = COMPNINST_STATE.success
        return self.save()

    # def eater_save(self, hosts):
    #     compn = self.compn
    #     eater_owner = toWalkerGetOwner(id=compn.eater_owner_id)
    #     owner = User.get_users(user_id=compn.owner_id)[0]
    #     responsible = Responsibility.query.filter_by(name=owner.username).first()
    #
    #     kwargs = dict(
    #         name=compn.compn_name + '_' + str(compn.call_times) + utils.serial_current_time(),
    #         version='v1.0',
    #         owner=eater_owner,
    #         reload_cmd=compn.eater_reload_cmd,
    #         host=hosts,
    #         group=[],
    #         responsible=responsible,
    #         mode='0755',
    #         port=None,
    #         check_cmd=None,
    #         runtime=None,
    #         server=None,
    #         mid_type=None)
    #     if compn.eater_version is not None:
    #         kwargs['version'] = compn.eater_version
    #     if compn.eater_port is not None:
    #         kwargs['port'] = compn.eater_port
    #
    #     try:
    #         software = toWalkerAddSoftware(**kwargs)
    #     except:
    #         app.logger.error('save software to eater faild.')
    #         return None
    #     return software

