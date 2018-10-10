import uuid
from . import app
from ..import db, app,api
from flask import request, make_response, json
import datetime
import re
import urllib3


def genUuid(seq=None):
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


"""
    logger
"""
# Init the Logging Handler
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(app.config['LOGGER_FILE'],
                              maxBytes=102400,
                              backupCount=1)
handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
handler.setLevel(app.config['DEFAULT_LOGLEVEL'])


def logmsg(msg):
    """
        to format the log message: add remote ip and target url
        add other info if u need more
    """
    try:
        logmsg = msg + '[from ' + request.remote_addr + \
            ' to ' + request.url + ']'
    except:
        logmsg = msg
    return logmsg



def to_dict(inst, cls=None, except_clm_list=None, target_clm_list=None, ext_dict=None):
    if type(inst) is list:
        if not len(inst):
            return inst
        if cls is None:
            cls = inst[0].__class__
        inst_list = inst
        instdict_list = list()
        for inst in inst_list:
            instdict_list.append(
                _to_dict(
                    inst=inst,
                    cls=cls,
                    except_clm_list=except_clm_list,
                    target_clm_list=target_clm_list,
                    ext_dict=ext_dict))
        return instdict_list
    else:
        if cls is None:
            cls = inst.__class__
        return _to_dict(
            inst, cls, except_clm_list=except_clm_list, target_clm_list=target_clm_list,
            ext_dict=ext_dict)


def _to_dict(inst, cls, except_clm_list=None, target_clm_list=None, ext_dict=None):
    """
    Jsonify the sql alchemy query result.
    """
    # print cls.__mapper__.columns.__dict__['_data'].items()
    # print cls.__mapper__.columns.__dict__['_data'].keys()
    # target_columns = cls.__mapper__.columns.__dict__['_data'].keys()
    convert = dict()
    convert['DATETIME'] = datetime.datetime.isoformat
    # add your coversions for things like datetime's
    # and what-not that aren't serializable.
    d = dict()
    if except_clm_list is None:
        except_clm_list = []
    if target_clm_list is None:
        target_clm_list = []
    # for c in cls.__table__.columns:
    for c in cls.__mapper__.columns:
        if len(target_clm_list) and c.name not in target_clm_list:
            continue
        if c.name not in except_clm_list:
            v = getattr(inst, c.name)
            if c.type in convert.keys() and v is not None:
                try:
                    d[c.name] = convert[c.type](v)
                except:
                    d[c.name] = "Error:  Failed to covert using ", \
                        str(convert[c.type])
            elif v is None:
                d[c.name] = str()
            else:
                d[c.name] = v
    if ext_dict is not None:
        d = dict(d, **ext_dict)
    return d



def sort_dict(target_dict, target_key, reverse=False):
    return sorted(target_dict, key=lambda k: k[target_key], reverse=reverse)


def try_load_json(json_str):
    try:
        return json.loads(json_str)
    except:
        return json_str