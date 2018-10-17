# -*- coding:utf-8 -*-
# !/usr/bin/env.conf python
#
# Author: Shawn.T
# Email: dai.sheng@139.com
# Maintainer: Gao Xirong
# Email: gaoxirong@shsnc.com
#
# This is the scene module of scene package,
#
import os
import tarfile
from urllib2 import quote

import werkzeug.datastructures
from flask import make_response
from flask import request
from flask_restful import reqparse, Resource
from gryphon.msclient import token_decode

from . import utils
from .application import app
from .models import Explorer

playbook_bkname = app.config['COMPN_PBS_BKNAME']
pkgs_bkname = app.config['COMPN_PKGS_BKNAME']
roles_bkname = app.config['COMPN_ROLES_BKNAME']

COMPN_PACK_EXTENSIONS = {'zip', 'tar.gz'}
COMPN_TEXT_EXTENSIONS = {'yml', 'py', 'sh', 'txt'}


class ExplorerAPI(Resource):
    """
    API class of ExplorerAPI
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(ExplorerAPI, self).__init__()

    def post(self):
        [folder, _file, filename] = self._post_arg_check()

        if folder is None and _file is None:
            raise utils.ClientUnprocEntError('need target folder or file.')

        current_username = self._get_current_username()

        ex = Explorer(is_minio=True)
        if _file is not None:
            file_path = ex.save_filestorage(
                fs=_file, bkname=current_username, prefix=folder,
                filename=filename)
            if file_path is None:
                msg = 'save file<' + filename + '> faild.'
                app.logger.info(utils.logmsg(msg))
            else:
                msg = 'save file <' + file_path + '> in user folder.'
                app.logger.info(utils.logmsg(msg))
        else:
            folder_path = ex.crt_folder(bkname=current_username,
                                        folder=folder)
            if folder_path is None:
                msg = 'create folder<' + folder + '> faild.'
            else:
                msg = 'create folder <' + folder_path + '> in user folder.'
                app.logger.info(utils.logmsg(msg))

        return {'message': msg}, 200

    def _post_arg_check(self):
        self.reqparse.add_argument(
            'folder', type=unicode, location='args',
            help='new folder path is a string.')
        self.reqparse.add_argument(
            'filename', type=unicode, location='args')
        self.reqparse.add_argument(
            'file', type=werkzeug.datastructures.FileStorage, location='files',
            help='upload file must be a file.')

        args = self.reqparse.parse_args()

        folder = args['folder']
        _file = args['file']
        filename = args['filename']
        if _file is not None and filename is None:
            raise utils.ClientUnprocEntError('need filename of upload file.')
        if filename is not None and _file is None:
            raise utils.ClientUnprocEntError('need file data of ' + filename)

        return [folder, _file, filename]

    def _get_token_payload(self):
        token = request.headers.get('Authorization')
        return token_decode(token)

    def _get_current_username(self):
        return self._get_token_payload()['username']

    def _get_current_user_id(self):
        return self._get_token_payload()['user_id']

    def delete(self):
        path = self._delete_arg_check()

        ex = Explorer(is_minio=True)
        current_username = self._get_current_username()
        ex.del_folder(bkname=current_username, folderpath=path)
        ex.del_file(bkname=current_username, filepath=path)
        msg = 'path <' + path + '> in user folder deleted.'
        app.logger.info(utils.logmsg(msg))
        return {'message': msg}, 200

    def _delete_arg_check(self):
        self.reqparse.add_argument(
            'path', type=unicode, location='args',
            required=True, help='path is unicode.')
        args = self.reqparse.parse_args()

        path = args['path']

        return path

    def get(self):
        filepath = self._get_arg_check()
        ex = Explorer(is_minio=True)
        current_username = self._get_current_username()
        if filepath is None:
            if not ex.bk_exists(bkname=current_username):
                ex.crt_bk(bkname=current_username)
            result = {'message': 'user files.',
                      'files': ex.explor(bkname=current_username)}
            return result, 200
        else:
            data = ex.get_file(bkname=current_username, filepath=filepath)
            if data is None:
                raise utils.ClientUnprocEntError('file not found.')
            response = make_response(data)
            filepath_encoded = os.path.basename(filepath).encode('utf-8')
            response.headers["Content-Disposition"] = \
                "attachment; filename*=utf8''%s" % quote(filepath_encoded)
            response.headers["content-type"] = utils.get_content_type(filepath)
            return response

    def _get_arg_check(self):
        self.reqparse.add_argument(
            'filepath', type=unicode, location='args',
            help='filepath is unicode.')
        args = self.reqparse.parse_args()
        filepath = args['filepath']
        return filepath


class CompnExplorerAPI(Resource):
    """docstring for CompnExplorerAPI"""

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(CompnExplorerAPI, self).__init__()

    def post(self):
        [yml_file, role_pkg, force] = self._post_arg_check()
        if yml_file is None and role_pkg is None:
            return {"message": "no files upload."}, 200

        msgs = ''
        if yml_file is not None:
            self._save_yml_file(yml_file, force)
            msgs = msgs + 'yml file<' + yml_file.filename + '> saved. '

        if role_pkg is not None:
            self._save_roles_pkg(role_pkg, force)
            msgs = msgs + 'role pkg file<' + role_pkg.filename + '> saved. '

        return {'message': msgs}, 200

    def _post_arg_check(self):
        self.reqparse.add_argument(
            'yml_file', type=werkzeug.datastructures.FileStorage,
            location='files',
            help='yml_file must be a file.')
        self.reqparse.add_argument(
            'role_pkg', type=werkzeug.datastructures.FileStorage,
            location='files',
            help='role_pkg must be a package, '
                 'it will be extracted under "roles" folder.')
        self.reqparse.add_argument(
            'force', type=int, location='args',
            help='force must be 0 or 1. Default is 0.')

        args = self.reqparse.parse_args()

        yml_file = args['yml_file']
        if yml_file is not None:
            if not Explorer._file_allowed(yml_file.filename, ['yml']):
                msg = 'wrong yml file extension({} is not allowed).' \
                    .format(yml_file.filename)
                app.logger.info(utils.logmsg(msg))
                raise utils.ClientUnprocEntError(msg)
        role_pkg = args['role_pkg']
        if role_pkg is not None:
            if not Explorer._file_allowed(role_pkg.filename,
                                          COMPN_PACK_EXTENSIONS):
                msg = 'wrong role package file name extension' \
                      '({} is not allowed).' \
                    .format(role_pkg.filename)
                app.logger.info(utils.logmsg(msg))
                raise utils.ClientUnprocEntError(msg)
        force = args['force']
        if not force == 1:
            force = 0
        return [yml_file, role_pkg, force]

    @staticmethod
    def _save_yml_file(yml_file, force=0):
        # save yml file
        if yml_file is None:
            app.logger.error(utils.logmsg('yml file is None.'))
            raise utils.ServerError('yml file is None.')

        ex = Explorer(is_minio=False)
        if ex.file_exists(bkname=playbook_bkname, filepath=yml_file.filename):
            if force == 0:
                raise utils.ClientUnprocEntError(
                    'yml file exists.use force params to cover.')

        filepath = ex.save_filestorage(fs=yml_file, bkname=playbook_bkname)
        if filepath is None:
            raise utils.ServerError('save yml file faild.')
        else:
            app.logger.debug(utils.logmsg('yml file saved in ' + filepath))

        return 'yml file saved.'

    @staticmethod
    def _save_roles_pkg(role_pkg, force=0):
        roles_folder = os.path.join(app.config['STORAGE_FOLDER'],
                                    roles_bkname)
        # save roles package
        if role_pkg is None:
            app.logger.error(utils.logmsg('role pkg file is None.'))

        ex = Explorer(is_minio=False)
        if ex.file_exists(bkname=pkgs_bkname, filepath=role_pkg.filename):
            if force == 0:
                raise utils.ClientUnprocEntError(
                    'role pkg file exists.use force params to cover.')

        filepath = ex.save_filestorage(fs=role_pkg, bkname=pkgs_bkname)
        if filepath is None:
            raise utils.ServerError('save role package faild.')
        else:
            app.logger.debug(utils.logmsg('role pkg file saved in ' +
                                          filepath))

        ex.init_folder(bkname=roles_bkname)
        try:
            f = tarfile.open(
                os.path.join(app.config['STORAGE_FOLDER'], pkgs_bkname,
                             filepath))
            f.extractall(path=roles_folder)
        except Exception as e:
            app.logger.error(e)
            raise utils.ServerError('couldnot extract roles package file')

        return 'role pkg saved in {}. ' \
               'And roles package extracted.'.format(roles_folder)

    def get(self):
        ex = ExplorerInf(is_minio=False)

        return {'message': 'files list.',
                'playbooks': ex.explor(bkname=playbook_bkname),
                'roles': ex.explor(bkname=roles_bkname),
                'packages': ex.explor(bkname=pkgs_bkname)}, 200


class ExplorerInf(object):
    """docstring for ExplorerInf"""

    def __init__(self, is_minio=False):
        super(ExplorerInf, self).__init__()
        self.explorer = Explorer(is_minio=is_minio)

    def explor(self, bkname=None):
        if bkname is None:
            return None
        return self.explorer.explor(bkname=bkname)

    def crt_bk(self, bkname):
        self.explorer.crt_bk(bkname=bkname)

    def bk_exists(self, bkname):
        self.explorer.bk_exists(bkname)

    def file_exists(self, bkname, filepath):
        return self.explorer.file_exists(bkname, filepath)
