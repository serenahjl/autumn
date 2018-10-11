#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Author: Daisheng
# Email: shawntai.ds@gmail.com
# (c) 2018
# this is a client to connect to the micro-services of promise.

import copy
from requests import Session
import json


LOGIN_PATH = '/auth'


class MSClient(object):
    """docstring for micro-service client of promise"""

    _state = {}
    _session = None
    _token = None

    # create a new MSClient Object if not exists
    def __new__(cls, *args, **kw):
        if cls not in cls._state:
            cls._state[cls] = super(MSClient, cls).__new__(cls, *args, **kw)
        return cls._state[cls]

    def __init__(self, base_url, username, password, timeout=10, login_path=LOGIN_PATH):
        """
        :param base_url: kong api base url
        """
        self.__base_headers = {
            'User-Agent': 'promise-gryphon',
            'Accept': 'application/json',
        }
        self.__base_url = base_url
        self.__timeout = timeout
        self.__username = username
        self.__password = password
        self.__login_path = login_path
        if self._session is None:
            self._session = Session()
        if self._token is None:
            self._login()

    def _login(self):
        json_d = dict(username=self.__username, password=self.__password)
        resp_data = self._execute(http_method='POST', path=self.__login_path, json_d=json_d)
        self._token = resp_data['token']
        return resp_data['token']

    def execute(self, http_method, path, json_d=None, url_d=None, content_type='application/json'):
        retry = False
        if self._token is None:
            self._login()
        try:
            resp_data = self._execute(http_method=http_method, path=path, json_d=json_d,
                                      url_d=url_d, token=self._token, content_type=content_type)
        except ForbiddenError as e:
            if "Invalid signature" in e.message or "No credentials found" in e.message or \
               "token expired" in e.message:
                self._login()
                resp_data = self._execute(http_method=http_method, path=path, json_d=json_d,
                                          url_d=url_d, token=self._token, content_type=content_type)
            else:
                raise
        return resp_data

    def _execute(self, http_method, path, json_d=None, url_d=None, token=None,
                 content_type='application/json'):

        url = self.__base_url + self.format_path(path)
        req_params = dict()

        # check the method
        http_method = http_method.upper()
        if http_method not in ['POST', 'PUT', 'PATCH', 'GET', 'DELETE']:
            raise MethodNotAllowedError('Wrong http_method: %s' % http_method)

        # header init
        req_params['headers'] = copy.deepcopy(self.__base_headers)
        if http_method in ('POST', 'PUT', 'PATCH'):
            req_params['headers']['content-type'] = content_type
        if token is not None:
            req_params['headers']['Authorization'] = 'Bearer %s' % token

        # setup json-body or url-params
        if json_d is not None:
            req_params['data'] = json.dumps(json_d, cls=ResourceEncoder)
        if url_d is not None:
            req_params['params'] = url_d
        resp = self._session.request(http_method, url, timeout=self.__timeout, **req_params)
        return self.parse_body(resp)

    def parse_body(self, resp):
        if resp.status_code in error_codes:
            req = resp.request
            req_info = dict(
                url=req.url,
                method=req.method,
                headers=dict(req.headers),
                data=req.body)
            resp_info = dict(
                status_code=resp.status_code,
                content=resp.content)
            message = json.dumps(dict(request=req_info, response=resp_info))
            raise error_codes[resp.status_code](resp.content, req_info, resp_info)

        if resp.content and resp.content.strip():
            try:
                # use supplied or inferred encoding to decode the
                # response content
                decoded_body = resp.content.decode(resp.encoding or resp.apparent_encoding)
                data = json.loads(decoded_body)
                return data
            except Exception, e:
                raise RequestError(e)

    @staticmethod
    def format_path(path=None):
        """set path into '/xx/xx/xx' format."""
        if path is None or path == '/' or len(path) == 0:
            return ''
        if not path[0] == '/':
            path = '/' + path
        if path[-1] == '/':
            path = path[:-1]
        return path


class ResourceEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'attributes'):
            # handle API resources
            return o.attributes
        return super(ResourceEncoder, self).default(o)


class RequestError(Exception):

    def __init__(self, message=None, req_info=None, resp_info=None):
        super(RequestError, self).__init__(message)
        self.message = message
        self.req_info = req_info
        self.resp_info = resp_info


class ResourceNotFoundError(RequestError):
    pass


class MethodNotAllowedError(RequestError):
    pass


class AuthenticationError(RequestError):
    pass


class ServerError(RequestError):
    pass


class BadGatewayError(RequestError):
    pass


class ServiceUnavailableError(RequestError):
    pass


class BadRequestError(RequestError):
    pass


class ForbiddenError(RequestError):
    pass


class RateLimitExceededError(RequestError):
    pass


class MultipleMatchingUsersError(RequestError):
    pass


class UnexpectedError(RequestError):
    pass


class TokenUnauthorizedError(RequestError):
    pass


class ConflictError(RequestError):
    pass


class UnsupportedMediaTypeError(RequestError):
    pass


error_codes = {
    400: BadRequestError,
    401: AuthenticationError,
    403: ForbiddenError,
    404: ResourceNotFoundError,
    405: MethodNotAllowedError,
    409: ConflictError,
    415: UnsupportedMediaTypeError,
    500: ServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError
}


import jwt
from jwt.exceptions import InvalidSignatureError


def token_decode(auth_in_header, secret=None, token_algorithm='HS256'):
    # :params auth_in_header : 'Authorization' params from the request headers
    token = auth_in_header.split(' ')[1]
    if secret is None:
        return jwt.decode(token, verify=False, algorithm=token_algorithm)
    else:
        try:
            return jwt.decode(token, secret, algorithm=token_algorithm)
        except InvalidSignatureError:
            return None
