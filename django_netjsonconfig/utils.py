from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404

from django_netjsonconfig.models import Config


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


def forbid_unallowed(params, param, allowed_values=None):
    value = params.get(param)
    if not value:
        return ControllerResponse('error: missing required parameter "{}"\n'.format(param),
                                  content_type='text/plain',
                                  status=400)
    if allowed_values and not isinstance(allowed_values, list):
        allowed_values = [allowed_values]
    if allowed_values is not None and value not in allowed_values:
        return ControllerResponse('error: wrong {}\n'.format(param),
                                  content_type='text/plain',
                                  status=403)
