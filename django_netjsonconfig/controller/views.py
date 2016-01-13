from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import Config
from ..utils import get_config_or_404, send_file, forbid_unallowed
from ..settings import REGISTRATION_ENABLED, SHARED_SECRET, BACKENDS


@require_http_methods(['GET'])
def checksum(request, pk):
    """
    returns configuration checksum
    """
    config = get_config_or_404(pk)
    return (forbid_unallowed(request.GET, 'key', config.key) or
            HttpResponse(config.checksum, content_type='text/plain'))


@require_http_methods(['GET'])
def download_config(request, pk):
    """
    returns configuration archive as attachment
    """
    config = get_config_or_404(pk)
    return (forbid_unallowed(request.GET, 'key', config.key) or
            send_file(filename='{0}.tar.gz'.format(config.name),
                      contents=config.generate().getvalue()))


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
                                       backend=request.POST.get('backend'))
        # return id and key in response
        content = '{id}\n{key}'.format(**config.__dict__)
        return HttpResponse(content, content_type='text/plain', status=201)
