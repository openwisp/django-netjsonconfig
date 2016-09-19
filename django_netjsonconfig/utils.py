import logging

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from django_netjsonconfig.models import Config

logger = logging.getLogger(__name__)


def get_config_or_404(pk, **kwargs):
    """
    like ``get_object_or_404``, but handles eventual exceptions
    for malformed UUIDs and by raising an ``Http404`` exception
    """
    kwargs.update({'pk': pk})
    try:
        return get_object_or_404(Config, **kwargs)
    except ValueError:
        raise Http404()


class ControllerResponse(HttpResponse):
    """
    extends ``django.http.HttpResponse`` by adding a custom HTTP header
    """
    def __init__(self, *args, **kwargs):
        super(ControllerResponse, self).__init__(*args, **kwargs)
        self['X-Openwisp-Controller'] = 'true'


def send_file(filename, contents):
    """
    returns a ``ControllerResponse`` object with an attachment
    """
    response = ControllerResponse(contents, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
    return response


def send_config(config, request):
    """
    calls ``update_last_ip`` and returns a ``ControllerResponse``
    which includes the configuration tar.gz as attachment
    """
    update_last_ip(config, request)
    return send_file(filename='{0}.tar.gz'.format(config.name),
                     contents=config.generate().getvalue())


def update_last_ip(config, request):
    """
    updates ``last_ip`` if necessary
    """
    latest_ip = request.META.get('REMOTE_ADDR')
    if config.last_ip != latest_ip:
        config.last_ip = latest_ip
        config.save()


def forbid_unallowed(request, param_group, param, allowed_values=None):
    """
    checks for malformed requests - eg: missing parameters (HTTP 400)
    or unauthorized requests - eg: wrong key (HTTP 403)
    logs suspicious activity
    returns either ``None`` if the request is legitimate
    or a ``ControllerResponse`` with the appropiate HTTP status
    """
    error = None
    value = getattr(request, param_group).get(param)
    if not value:
        error = 'error: missing required parameter "{}"\n'.format(param)
        logger.warning(error, extra={'request': request, 'stack': True})
        return ControllerResponse(error, content_type='text/plain', status=400)
    if allowed_values and not isinstance(allowed_values, list):
        allowed_values = [allowed_values]
    if allowed_values is not None and value not in allowed_values:
        error = 'error: wrong {}\n'.format(param)
        logger.warning(error, extra={'request': request, 'stack': True})
        return ControllerResponse(error, content_type='text/plain', status=403)
