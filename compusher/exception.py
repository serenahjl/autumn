# -*- coding: utf-8 -*-
"""
    Exception: 2 basic custom Exception classes,
    1. api calling exception, means exterior error(client exception)
    2. module calling exception, means internal error(server exception)
"""


class ClientError(Exception):
    """
        invalid API usage, belongs to client exception,
        use the 4xx status_code
    """
    status_code = 400
    message = 'The request cannot be fulfilled due to bad syntax.'

    def __init__(self, message=None, status_code=None, payload=None):
        # setLevel can be [debug, info, warning, error, critical]
        Exception.__init__(self)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class ServerError(Exception):
    """
        invalid module calling, belongs to server exception,
        use the 5xx status_code
    """
    status_code = 500
    message = 'The server encountered an unexpected condition which \
              prevented it from fulfilling the request.'

    def __init__(self, message=None, status_code=None, payload=None):
        # setLevel can be [debug, info, warning, error, critical]
        Exception.__init__(self)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class ClientUnauthError(ClientError):
    status_code = 401
    message = 'Client unauthorized.'


class ClientUnprocEntError(ClientError):
    status_code = 422
    message = "Unprocessable Entity"