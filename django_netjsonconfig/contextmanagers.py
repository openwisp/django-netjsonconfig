import logging
logger = logging.getLogger(__name__)
from contextlib import contextmanager


@contextmanager
def log_on_fail(action, obj):
    try:
        yield
    except Exception as e:
        msg = 'Failed to perform {0} on {1}'.format(action, obj.__repr__())
        logger.exception(msg)
        print('{0}: {1}\nSee error log for more '
              'information\n'.format(msg, e.__class__.__name__))
