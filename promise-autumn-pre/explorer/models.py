# -*- coding:utf-8 -*-
# !/usr/bin/env python
#
# Author: Shawn.T
# Email: shawntai.ds@gmail.com
#
# This is the model module for the user package
# holding user, token, role and  privilege models, etc.
#
import datetime
import logging
import os

from gryphon.api import MinioAPI

from . import utils
from .application import app

TEXT_EXTENSIONS = {'yml', 'py', 'sh', 'txt', 'md'}
IGNORE_HIDDEN = True
TEXT_DISP_MAXSIZE = 1048676
EMPTY_FILE_NAME = '.empty.tmp'

logger = logging.getLogger(__name__)


class Explorer(object):
    """docstring for explorer"""

    def __init__(self, is_minio=False):
        super(Explorer, self).__init__()
        self.is_minio = is_minio
        if is_minio:
            self.minio = MinioAPI(endpoint=app.config['MINION_ENDPOINT'],
                                  access_key=app.config['MINION_ACCESS_KEY'],
                                  secret_key=app.config['MINION_SECRET_KEY'])
            self.minio.connect()
            self._tmpfile_path = os.path.join(app.config['TMP_FOLDER'],
                                              EMPTY_FILE_NAME)
            f = open(self._tmpfile_path, 'w')
            f.close()
        else:
            self.storage_folder = app.config['STORAGE_FOLDER']

    def bk_exists(self, bkname):
        if self.is_minio:
            if self.minio.bucket_exists(bkname):
                return True
            return False
        else:
            if os.path.join(self.storage_folder, bkname):
                return True
            return False

    def file_exists(self, bkname, filepath):
        if self.is_minio:
            try:
                obj = self.minio.get_object(bucket_name=bkname,
                                            object_name=filepath)
            except Exception as e:
                app.logger.error(e)
                return False
            if obj is not None:
                return True
        else:
            full_filepath = os.path.join(app.config['STORAGE_FOLDER'],
                                         bkname,
                                         filepath)
            if os.path.isfile(full_filepath):
                return True
            else:
                return False

    def crt_bk(self, bkname):
        if self.is_minio:
            if not self.bk_exists(bkname):
                try:
                    self.minio.make_bucket(bucket_name=bkname)
                except Exception as e:
                    logger.error(e)
                    return False
            return True
        else:
            if not self.bk_exists(bkname):
                try:
                    os.mkdir(os.path.join(app.config['STORAGE_FOLDER'],
                                          bkname))
                except Exception as e:
                    logger.error(e)
                    return False
                return True

    def crt_folder(self, bkname, folder):
        self.crt_bk(bkname)
        if self.is_minio:
            folder = self._format_prefix_minio(folder)
            if folder == '':
                return folder
            foldernames = folder[:-1].split('/')
            tar_folder = ''
            for foldername in foldernames:
                tar_folder += "%s/" % foldername
                try:
                    self.minio.fput_object(
                        bucket_name=bkname,
                        object_name=os.path.join(tar_folder, EMPTY_FILE_NAME),
                        file_path=self._tmpfile_path)
                except Exception as e:
                    logger.error(e)
                    return None
        else:
            os.makedirs(os.path.join(app.config['STORAGE_FOLDER'],
                                     bkname,
                                     folder))
        return folder

    def del_folder(self, bkname, folderpath):
        folderpath = self._format_prefix_minio(folderpath)
        if self.is_minio:
            del_objs = self.minio.list_objects(
                bucket_name=bkname, prefix=folderpath, recursive=True)
            for del_obj in del_objs:
                self.minio.remove_object(bucket_name=bkname,
                                         object_name=del_obj.object_name)
                msg = 'delete file <' + del_obj.object_name + '>'
                app.logger.info(utils.logmsg(msg))
        else:
            pass

    def del_file(self, bkname, filepath):
        if self.is_minio:
            filepath = self._format_filepath_minio(filepath)
            self.minio.remove_object(bucket_name=bkname, object_name=filepath)
        else:
            pass

    def get_file(self, bkname, filepath):
        if self.is_minio:
            filepath = self._format_filepath_minio(filepath)
            if filepath is None:
                return None
            return self._get_file_minio(bkname, filepath)
        else:
            pass

    def _get_file_minio(self, bkname, filepath):
        try:
            obj = self.minio.get_object(bucket_name=bkname,
                                        object_name=filepath)
        except Exception as e:
            logger.error(e)
            return None
        return obj.data

    def explor(self, bkname, showtxt=True):
        if self.is_minio:
            return self._explor_minio(bkname=bkname, showtxt=showtxt)
        else:
            return self._explor(bkname=bkname, showtxt=showtxt)

    def _explor_minio(self, bkname, showtxt):
        if not self.bk_exists(bkname):
            return None
        else:
            return self._scan_files_minio(bkname=bkname, showtxt=showtxt)

    def _scan_files_minio(self, bkname, showtxt, prefix=None):
        if prefix is None:
            prefix = ''
        file_objs_i = self.minio.list_objects(bucket_name=bkname,
                                              prefix=prefix)
        files_info = list()
        for file_o in file_objs_i:
            # pfname: prefix + filename
            # fname: filename
            pfname = file_o.object_name
            if file_o.is_dir:
                fname = os.path.basename(pfname[:-1])
                file_info = dict(
                    name=fname,
                    is_dir=file_o.is_dir,
                    branches=self._scan_files_minio(bkname=bkname,
                                                    showtxt=showtxt,
                                                    prefix=pfname))
            else:
                fname = os.path.basename(pfname)
                if fname == EMPTY_FILE_NAME:
                    continue
                file_info = dict(
                    name=fname,
                    is_dir=file_o.is_dir,
                    last_modf=file_o.last_modified,
                    size=self._disp_size(file_o.size))
                if showtxt and file_o.size < TEXT_DISP_MAXSIZE and \
                        self._file_allowed(fname, TEXT_EXTENSIONS):
                    f = self.minio.get_object(bucket_name=bkname,
                                              object_name=pfname)
                    file_info['content'] = f.data
            files_info.append(file_info)
        return files_info

    @classmethod
    def _explor(cls, bkname, showtxt):
        bk_path = os.path.join(app.config['STORAGE_FOLDER'], bkname)
        if not os.path.isdir(bk_path):
            return None
        else:
            return cls._scan_files(showtxt=showtxt, path=bk_path)

    @classmethod
    def _scan_files(cls, showtxt, path=None):
        files_info = list()
        if path is not None:
            filenames = cls._get_filenames(path=path)
            for filename in filenames:
                files_info.append(
                    cls._file_st(showtxt=showtxt,
                                 file_path=os.path.join(path, filename)))
        return files_info

    @classmethod
    def _file_st(cls, showtxt, file_path):
        st = os.stat(file_path)
        if os.path.isdir(file_path):
            file_st = dict(
                name=os.path.basename(file_path),
                is_dir=True,
                branches=cls._scan_files(showtxt=showtxt, path=file_path))
        else:
            file_st = dict(
                name=os.path.basename(file_path),
                is_dir=False,
                last_modf=datetime.datetime.utcfromtimestamp(st.st_mtime),
                size=cls._disp_size(st.st_size))
            if showtxt and st.st_size < TEXT_DISP_MAXSIZE \
                    and cls._file_allowed(file_path, TEXT_EXTENSIONS):
                f = open(file_path)
                file_st['content'] = f.read()
        return file_st

    @staticmethod
    def _disp_size(size_byte):
        size = size_byte
        units = ['Byte', 'KB', 'MB', 'GB', 'TB']
        for unit in units:
            if size < 1024:
                break
            else:
                size = size / 1024
        return str(size) + unit

    @staticmethod
    def _file_allowed(filename, allowed_ext):
        if '.' in filename:
            fn_list = filename.split('.')
            if fn_list[-1] in allowed_ext:
                return True
            if '.'.join(fn_list[-2:]) in allowed_ext:
                return True
        return False

    @staticmethod
    def _get_filenames(path):
        filenames = os.listdir(path)
        if not IGNORE_HIDDEN:
            return filenames
        else:
            tar_fns = []
            for filename in filenames:
                if not filename[0] == '.':
                    tar_fns.append(filename)
            return tar_fns

    def init_folder(self, bkname, prefix=None):
        self.crt_bk(bkname)
        if not self.is_minio:
            if prefix is None:
                tar_folder = os.path.join(app.config['STORAGE_FOLDER'], bkname)
            else:
                tar_folder = os.path.join(app.config['STORAGE_FOLDER'],
                                          bkname,
                                          prefix)
            if not os.path.isdir(tar_folder):
                os.makedirs(tar_folder)

    def save_filestorage(self, fs, bkname, prefix=None, filename=None):
        """
            # fs : werkzeug.datastrctures.FileStorage object type
            # bkname: bucket name
            # prefix: folder path in the bucket to store this file
        """
        if filename is None:
            filename = fs.filename
        filename = utils.to_str(filename)
        prefix = utils.to_str(prefix)
        self.init_folder(bkname, prefix)
        if self.is_minio:
            return self._save_filestorage_minio(fs, bkname, filename, prefix)
        else:
            return self._save_filestorage(fs, bkname, filename, prefix)

    def _save_filestorage_minio(self, fs, bkname, filename, prefix):
        tmp_folder = utils.temp_upload_folder()
        os.mkdir(tmp_folder)

        # fs.filename is a string-escape type string,
        # should be decoded before being used.
        # fn = fs.filename.decode('string-escape')
        # tmp_file_path = os.path.join(tmp_folder, fn)
        tmp_file_path = os.path.join(tmp_folder, filename)
        fs.save(tmp_file_path)

        self.crt_folder(bkname=bkname, folder=prefix)

        object_name = os.path.join(self._format_prefix_minio(prefix), filename)

        try:
            self.minio.fput_object(
                bucket_name=bkname, object_name=object_name,
                file_path=tmp_file_path)
        except Exception as e:
            logger.error(e)
            return None
        return object_name

    def _save_filestorage(self, fs, bkname, filename, prefix=None):
        if prefix is None:
            full_filepath = os.path.join(app.config['STORAGE_FOLDER'], bkname,
                                         filename)
            filepath = filename
        else:
            if prefix[-1] == '/' or prefix[-1] == '\\':
                prefix = prefix[:-1]
            full_filepath = os.path.join(app.config['STORAGE_FOLDER'], bkname,
                                         prefix, filename)
            filepath = os.path.join(prefix, filename)
        try:
            fs.save(full_filepath)
        except Exception as e:
            app.logger.error(utils.logmsg('save file error: %s' % e))
            return None
        app.logger.debug(utils.logmsg('file saved in ' + full_filepath))
        return filepath

    @staticmethod
    def _format_prefix_minio(prefix):
        """
        format prefix into empty string or "xxx/xxx/xxx/"
        """
        if prefix is None or prefix == '':
            return ''
        if prefix == '/':
            return ''
        if prefix[0] == '/':
            prefix = prefix[1:]
        if not prefix[-1] == '/':
            prefix += '/'
        return prefix

    @staticmethod
    def _format_filepath_minio(filepath):
        """
        format filepath into "xxx/xxx"
        """
        if filepath == '' or filepath[-1] == '/':
            return None
        if filepath[0] == '/':
            filepath = filepath[1:]
        return filepath

    def save_to_minio(self, bkname, prefix, local_filepath=None,
                      local_folderpath=None):
        if self.is_minio is not True:
            return None

        self.crt_folder(bkname=bkname, folder=prefix)

        if local_filepath is not None:
            object_name = os.path.join(
                self._format_prefix_minio(prefix),
                os.path.basename(local_filepath))
            self.minio.fput_object(
                bucket_name=bkname, object_name=object_name,
                file_path=local_filepath)
        if local_folderpath is not None:
            filenames = os.listdir(local_folderpath)
            for filename in filenames:
                object_name = os.path.join(
                    self._format_prefix_minio(prefix), filename)
                self.minio.fput_object(
                    bucket_name=bkname,
                    object_name=object_name,
                    file_path=os.path.join(local_folderpath, filename))
        return object_name
