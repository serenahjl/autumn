# -*- coding: utf-8 -*-
import os

from flask import Flask
from flask.ext.cors import CORS

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
if os.path.isfile(os.path.join(app.config['ABS_BASEDIR'],
                               'instance/config.py')):
    app.config.from_pyfile('config.py')

cors = CORS(app, allow_headers='*', expose_headers='Content-Disposition')
