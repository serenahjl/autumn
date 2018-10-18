#!/usr/bin/env.conf python
# -*- coding:utf-8 -*-
import sys
sys.path.append('.')

from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from compusher import app, db
from compusher .models import Compn, Enum


migrate = Migrate(app, db)
manager = Manager(app, usage="Perform database operations")
manager.add_command('db', MigrateCommand)
default_bind_key = '__all__'


@manager.command
def initdb(bind=default_bind_key):
    """ initialize database tables"""
    db.create_all(bind=bind)
    if bind == '__all__':
        print 'Database inited, location:\r\n[%-10s] %s' % (
            'DEFAULT', app.config['SQLALCHEMY_DATABASE_URI'], )
    elif bind is None:
        print 'Database inited, location:\r\n[%-10s] %s' % (
            'DEFAULT', app.config['SQLALCHEMY_DATABASE_URI'], )
    else:
        print 'Unknown database: [%+10s].' % bind.upper()


@manager.command
def dropdb(bind=default_bind_key):
    """ Drops database tables"""
    db.drop_all(bind=bind)
    if bind == '__all__':
        print 'Database dropped, location:\r\n[%-10s] %s' % (
            'DEFAULT', app.config['SQLALCHEMY_DATABASE_URI'], )
        if app.config['SQLALCHEMY_BINDS']:
            for k, w in app.config['SQLALCHEMY_BINDS'].items():
                print '[%-10s] %s' % (k.upper(), w)
    elif bind is None:
        print 'Database dropped, location:\r\n[%-10s] %s' % (
            'DEFAULT', app.config['SQLALCHEMY_DATABASE_URI'], )
    else:
        print 'Unknown database: [%+10s].' % bind.upper()


@manager.command
def recreatedb():
    """Recreates database tables \
    (same as issuing 'drop', 'create' and then 'import')"""
    dropdb()
    initdb()


def _make_context():
    return dict(app=app, db=db)


manager.add_command("shell", Shell(make_context=_make_context))


if __name__ == '__main__':
    manager.run()
