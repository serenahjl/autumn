# -*- coding:utf-8 -*-
# !/usr/bin/env.conf python
#
# Author: Shawn.T, Leann Mak
# Email: shawntai.ds@gmail.com, leannmak@139.com
#
# This is the utils of scene package,
# holding some useful tools for the filer package

import logging
import os
import uuid

import urllib3.fields
from flask import request

from .exceptions import *  # noqa
from explorer.application import app

from .utils import *  # noqa

logger = logging.getLogger(__file__)


def gen_uuid(seq=None):
    """
        generate a 64Byte uuid code
        first 32Byte: hashed timestamp string,
        last 32Byte: hashed 'seq' string in its namespace
        in the user package, it is used to create 'User.user_id'
    """
    if seq is not None:
        return uuid.uuid1().hex + uuid.uuid3(uuid.NAMESPACE_DNS, seq).hex
    return uuid.uuid1().hex + uuid.uuid3(
        uuid.NAMESPACE_DNS, uuid.uuid1().hex).hex


def temp_upload_folder():
    return os.path.join(app.config['TMP_FOLDER'],
                        'temp-upload-file-{}'.format(gen_uuid()))


def temp_fetch_folder():
    return os.path.join(app.config['TMP_FOLDER'],
                        'temp-fetch-file-{}'.format(gen_uuid()))


def logmsg(msg):
    """
        to format the log message: add remote ip and target url
        add other info if u need more
    """
    try:
        msg = msg + '[from ' + request.remote_addr + ' to ' + request.url + ']'
    except Exception as e:
        logger.error(e)
        msg = msg
    return msg


def get_content_type(filename):
    return urllib3.fields.guess_content_type(filename)
