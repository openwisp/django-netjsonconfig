import json

from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .. import settings
from ..models import Config
from ..utils import (ControllerResponse, forbid_unallowed, get_config_or_404,
                     send_config, update_last_ip)


@require_http_methods(['GET'])
def checksum(request, pk):
    """
    returns configuration checksum
    """
    config = get_config_or_404(pk)
    bad_request = forbid_unallowed(request, 'GET', 'key', config.key)
    if bad_request:
        return bad_request
    update_last_ip(config, request)
    return ControllerResponse(config.checksum, content_type='text/plain')


@require_http_methods(['GET'])
def download_config(request, pk):
    """
    returns configuration archive as attachment
    """
    config = get_config_or_404(pk)
    return (forbid_unallowed(request, 'GET', 'key', config.key) or
            send_config(config, request))


@csrf_exempt
@require_http_methods(['POST'])
def report_status(request, pk):
    """
    updates status of config objects
    """
    config = get_config_or_404(pk)
    # ensure request is well formed and authorized
    allowed_status = [choices[0] for choices in Config.STATUS]
    required_params = [('key', config.key),
                       ('status', allowed_status)]
    for key, value in required_params:
        bad_response = forbid_unallowed(request, 'POST', key, value)
        if bad_response:
            return bad_response
    config.status = request.POST.get('status')
    config.save()
    return ControllerResponse('report-result: success\n'
                              'current-status: {}\n'.format(config.status),
                              content_type='text/plain')


@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    """
    registers new config
    """
    if not settings.REGISTRATION_ENABLED:
        return ControllerResponse(status=404)
    # ensure request is well formed and authorized
    allowed_backends = [path for path, name in settings.BACKENDS]
    required_params = [('secret', settings.SHARED_SECRET),
                       ('name', None),
                       ('mac_address', None),
                       ('backend', allowed_backends)]
    # valid required params or forbid
    for key, value in required_params:
        bad_response = forbid_unallowed(request, 'POST', key, value)
        if bad_response:
            return bad_response
    key = None
    last_ip = request.META.get('REMOTE_ADDR')
    if settings.CONSISTENT_REGISTRATION:
        key = request.POST.get('key')
    # try retrieving existing Config first
    # (key is filled only if CONSISTENT_REGISTRATION is enabled)
    try:
        config = Config.objects.get(key=key)
    # otherwise create new Config
    except Config.DoesNotExist:
        new = True
        options = dict(name=request.POST.get('name'),
                       mac_address=request.POST.get('mac_address'),
                       backend=request.POST.get('backend'),
                       last_ip=last_ip)
        # do not specify key if ``None``, would cause exception
        if key:
            options['key'] = key
        config = Config(**options)
        try:
            config.full_clean()
        except ValidationError as e:
            # dump message_dict as JSON,
            # this should make it easy to debug
            return ControllerResponse(json.dumps(e.message_dict, indent=4, sort_keys=True),
                                      content_type='text/plain',
                                      status=400)
        else:
            config.save()
    # update last_ip on existing configs
    else:
        new = False
        config.last_ip = last_ip
        config.save()
    # return id and key in response
    s = 'registration-result: success\n' \
        'uuid: {id}\n' \
        'key: {key}\n' \
        'hostname: {name}\n'
    s += 'is-new: %s\n' % (int(new))
    return ControllerResponse(s.format(**config.__dict__),
                              content_type='text/plain',
                              status=201)
