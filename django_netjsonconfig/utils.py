import logging

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from django_netjsonconfig.models import Config

logger = logging.getLogger(__name__)


def get_config_or_404(pk, **kwargs):
    kwargs.update({'pk': pk})
    try:
        return get_object_or_404(Config, **kwargs)
    except ValueError:
        raise Http404()


class ControllerResponse(HttpResponse):
    def __init__(self, *args, **kwargs):
        super(ControllerResponse, self).__init__(*args, **kwargs)
        self['X-Openwisp-Controller'] = 'true'


def send_file(filename, contents):
    response = ControllerResponse(contents, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
    return response


def send_config(config, request):
    """
    sends config in http response and updates last_ip
    """
    update_last_ip(config, request)
    return send_file(filename='{0}.tar.gz'.format(config.name),
                     contents=config.generate().getvalue())


def update_last_ip(config, request):
    """
    updates last_ip if necessary
    """
    latest_ip = request.META.get('REMOTE_ADDR')
    if config.last_ip != latest_ip:
        config.last_ip = latest_ip
        config.save()


def forbid_unallowed(request, param_group, param, allowed_values=None):
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
