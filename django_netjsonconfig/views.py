import json
from copy import deepcopy

from django.http import HttpResponse
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _
from django.views.decorators.http import last_modified

from .settings import BACKENDS, VPN_BACKENDS

ALL_BACKENDS = BACKENDS + VPN_BACKENDS

# ``available_schemas`` and ``available_schemas_json``
# will be generated only once at startup
available_schemas = {}
for backend_path, label in ALL_BACKENDS:  # noqa
    backend = import_string(backend_path)
    schema = deepcopy(backend.schema)
    # must use conditional because some custom backends might not specify an hostname
    if 'general' in schema['properties']:
        # hide hostname because it's handled via models
        if 'hostname' in schema['properties']['general']['properties']:
            del schema['properties']['general']['properties']['hostname']
        # remove hosname from required properties
        if 'hostname' in schema['properties']['general'].get('required', []):
            del schema['properties']['general']['required']
    # start editor empty by default, except for VPN schemas
    if (backend_path, label) not in VPN_BACKENDS:
        schema['defaultProperties'] = []
    available_schemas[backend_path] = schema
available_schemas_json = json.dumps(available_schemas)

login_required_error = json.dumps({'error': _('login required')})

# ``start_time`` will contain the datetime of the moment in which the
# application server is started and it is used in the last-modified
# header of the HTTP response of ``schema`` view
start_time = timezone.now()


@last_modified(lambda request: start_time)
def schema(request):
    """
    returns configuration checksum
    """
    if request.user.is_authenticated():
        c = available_schemas_json
        status = 200
    else:
        c = login_required_error
        status = 403
    return HttpResponse(c, status=status, content_type='application/json')
