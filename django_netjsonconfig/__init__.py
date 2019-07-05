from __future__ import absolute_import, unicode_literals
from .celery import app as celery_app

__all__ = ['celery_app']

VERSION = (0, 9, 0, 'alpha')
__version__ = VERSION  # alias


def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            try:
                rev = VERSION[4]
            except IndexError:
                rev = 0
            version = '%s%s%s' % (version, VERSION[3][0:1], rev)
    return version


default_app_config = 'django_netjsonconfig.apps.DjangoNetjsonconfigApp'
