from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from ..utils import get_device_or_404, send_file, forbid_unallowed


@require_http_methods(['GET'])
def checksum(request, pk):
    """
    returns configuration checksum
    """
    device = get_device_or_404(pk)
    return (forbid_unallowed(request, device) or
            HttpResponse(device.checksum, content_type='text/plain'))


@require_http_methods(['GET'])
def download_config(request, pk):
    """
    returns configuration archive as attachment
    """
    device = get_device_or_404(pk)
    return (forbid_unallowed(request, device) or
            send_file(filename='{0}.tar.gz'.format(device.name),
                      contents=device.generate().getvalue()))
