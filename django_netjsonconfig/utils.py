from django.shortcuts import get_object_or_404
from django.http import (HttpResponse,
                         Http404,
                         HttpResponseBadRequest,
                         HttpResponseForbidden)

from django_netjsonconfig.models import Device


def get_device_or_404(pk, **kwargs):
    kwargs.update({
        'pk': pk
    })
    try:
        return get_object_or_404(Device, **kwargs)
    except ValueError:
        raise Http404()


def send_file(filename, contents):
    response = HttpResponse(contents, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
    return response


def forbid_unallowed(request, device):
    key = request.GET.get('key')
    if not key:
        return HttpResponseBadRequest('missing required parameter "key"')
    if key != device.key:
        return HttpResponseForbidden('wrong key')
