from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models import Config
from ..settings import BACKENDS, REGISTRATION_ENABLED, SHARED_SECRET
from ..utils import (ControllerResponse, forbid_unallowed, get_config_or_404,
                     send_config, update_last_ip)


@require_http_methods(['GET'])
def checksum(request, pk):
    """
    returns configuration checksum
    """
    config = get_config_or_404(pk)
    bad_request = forbid_unallowed(request.GET, 'key', config.key)
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
    return (forbid_unallowed(request.GET, 'key', config.key) or
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
        bad_response = forbid_unallowed(request.POST, key, value)
        if bad_response:
            return bad_response
    config.status = request.POST.get('status')
    config.save()
    return ControllerResponse('report-result: success\n'
                              'current-status: {}\n'.format(config.status),
                              content_type='text/plain')


if REGISTRATION_ENABLED:
    @csrf_exempt
    @require_http_methods(['POST'])
    def register(request):
        """
        registers new config
        """
        # ensure request is well formed and authorized
        allowed_backends = [path for path, name in BACKENDS]
        required_params = [('secret', SHARED_SECRET),
                           ('name', None),
                           ('backend', allowed_backends)]
        for key, value in required_params:
            bad_response = forbid_unallowed(request.POST, key, value)
            if bad_response:
                return bad_response
        # create new Config
        config = Config.objects.create(name=request.POST.get('name'),
                                       backend=request.POST.get('backend'),
                                       last_ip=request.META.get('REMOTE_ADDR'))
        # return id and key in response
        s = 'registration-result: success\n' \
            'uuid: {id}\n' \
            'key: {key}\n'
        return ControllerResponse(s.format(**config.__dict__),
                                  content_type='text/plain',
                                  status=201)
