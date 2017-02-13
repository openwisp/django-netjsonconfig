import json

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from .. import settings
from ..utils import (ControllerResponse, forbid_unallowed, get_object_or_404,
                     send_config, update_last_ip)


class BaseConfigView(SingleObjectMixin, View):
    """
    Base view that implements a ``get_object`` method
    Subclassed by all views dealing with existing objects
    """
    def get_object(self, *args, **kwargs):
        return get_object_or_404(self.model, *args, **kwargs)


class CsrfExtemptMixin(object):
    """
    Mixin that makes the view extempt from CSFR protection
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CsrfExtemptMixin, self).dispatch(request, *args, **kwargs)


class UpdateLastIpMixin(object):
    def update_last_ip(self, config, request):
        update_last_ip(config, request)


class BaseChecksumView(UpdateLastIpMixin, BaseConfigView):
    """
    returns configuration checksum
    """
    def get(self, request, *args, **kwargs):
        config = self.get_object(*args, **kwargs)
        bad_request = forbid_unallowed(request, 'GET', 'key', config.key)
        if bad_request:
            return bad_request
        self.update_last_ip(config, request)
        return ControllerResponse(config.checksum, content_type='text/plain')


class BaseDownloadConfigView(BaseConfigView):
    """
    returns configuration archive as attachment
    """
    def get(self, request, *args, **kwargs):
        config = self.get_object(*args, **kwargs)
        return (forbid_unallowed(request, 'GET', 'key', config.key) or
                send_config(config, request))


class BaseReportStatusView(CsrfExtemptMixin, BaseConfigView):
    """
    updates status of config objects
    """
    def post(self, request, *args, **kwargs):
        config = self.get_object(*args, **kwargs)
        # ensure request is well formed and authorized
        allowed_status = [choices[0] for choices in self.model.STATUS]
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


class BaseRegisterView(UpdateLastIpMixin, CsrfExtemptMixin, View):
    """
    registers new Config objects
    """
    def init_object(self, **kwargs):
        options = {}
        for attr in kwargs.keys():
            # skip attributes that are not model fields
            try:
                self.model._meta.get_field(attr)
            except FieldDoesNotExist:
                continue
            options[attr] = kwargs.get(attr)
        # do not specify key if:
        #   settings.CONSISTENT_REGISTRATION is False
        #   if key is ``None`` (it would cause exception)
        if 'key' in options and (settings.CONSISTENT_REGISTRATION is False
                                 or options['key'] is None):
            del options['key']
        return self.model(**options)

    def invalid(self, request):
        """
        ensures request is well formed
        """
        allowed_backends = [path for path, name in settings.BACKENDS]
        required_params = [('secret', None),
                           ('name', None),
                           ('mac_address', None),
                           ('backend', allowed_backends)]
        # valid required params or forbid
        for key, value in required_params:
            invalid_response = forbid_unallowed(request, 'POST', key, value)
            if invalid_response:
                return invalid_response

    def forbidden(self, request):
        """
        ensures request is authorized:
            - secret matches settings.NETJSONCONFIG_SHARED_SECRET
        """
        return forbid_unallowed(request, 'POST', 'secret', settings.SHARED_SECRET)

    def post(self, request, *args, **kwargs):
        """
        POST logic
        """
        if not settings.REGISTRATION_ENABLED:
            return ControllerResponse(status=404)
        # ensure request is valid
        bad_response = self.invalid(request)
        if bad_response:
            return bad_response
        # ensure request is allowed
        forbidden = self.forbidden(request)
        if forbidden:
            return forbidden
        # prepare model attributes
        key = None
        last_ip = request.META.get('REMOTE_ADDR')
        if settings.CONSISTENT_REGISTRATION:
            key = request.POST.get('key')
        # try retrieving existing Config first
        # (key is not None only if CONSISTENT_REGISTRATION is enabled)
        try:
            config = self.model.objects.get(key=key)
        # otherwise create new Config
        except self.model.DoesNotExist:
            new = True
            config = self.init_object(last_ip=last_ip, **request.POST.dict())
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
            self.update_last_ip(config, request)
        # return id and key in response
        s = 'registration-result: success\n' \
            'uuid: {id}\n' \
            'key: {key}\n' \
            'hostname: {name}\n'
        s += 'is-new: %s\n' % (int(new))
        attributes = config.__dict__
        attributes['id'] = config.pk.hex
        return ControllerResponse(s.format(**attributes),
                                  content_type='text/plain',
                                  status=201)
