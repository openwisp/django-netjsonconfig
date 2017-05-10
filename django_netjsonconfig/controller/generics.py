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
        kwargs['config__isnull'] = False
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
        device = self.get_object(*args, **kwargs)
        bad_request = forbid_unallowed(request, 'GET', 'key', device.key)
        if bad_request:
            return bad_request
        self.update_last_ip(device.config, request)
        return ControllerResponse(device.config.checksum, content_type='text/plain')


class BaseDownloadConfigView(BaseConfigView):
    """
    returns configuration archive as attachment
    """
    def get(self, request, *args, **kwargs):
        device = self.get_object(*args, **kwargs)
        return (forbid_unallowed(request, 'GET', 'key', device.key) or
                send_config(device.config, request))


class BaseReportStatusView(CsrfExtemptMixin, BaseConfigView):
    """
    updates status of config objects
    """
    def post(self, request, *args, **kwargs):
        device = self.get_object(*args, **kwargs)
        config = device.config
        # ensure request is well formed and authorized
        allowed_status = [choices[0] for choices in config.STATUS]
        required_params = [('key', device.key),
                           ('status', allowed_status)]
        for key, value in required_params:
            bad_response = forbid_unallowed(request, 'POST', key, value)
            if bad_response:
                return bad_response
        # call set_status_{status} method on Config model
        method_name = 'set_status_{status}'.format(**request.POST.dict())
        getattr(config, method_name)()
        return ControllerResponse('report-result: success\n'
                                  'current-status: {}\n'.format(config.status),
                                  content_type='text/plain')


class BaseRegisterView(UpdateLastIpMixin, CsrfExtemptMixin, View):
    """
    registers new Config objects
    """
    def init_object(self, **kwargs):
        """
        initializes Config object with incoming POST data
        """
        device_model = self.model
        config_model = device_model.get_config_model()
        options = {}
        for attr in kwargs.keys():
            # skip attributes that are not model fields
            try:
                device_model._meta.get_field(attr)
            except FieldDoesNotExist:
                continue
            options[attr] = kwargs.get(attr)
        # do not specify key if:
        #   settings.CONSISTENT_REGISTRATION is False
        #   if key is ``None`` (it would cause exception)
        if 'key' in options and (settings.CONSISTENT_REGISTRATION is False
                                 or options['key'] is None):
            del options['key']
        return config_model(device=device_model(**options),
                            backend=kwargs['backend'],
                            last_ip=kwargs['last_ip'])

    def get_template_queryset(self, config):
        """
        returns Template model queryset
        """
        # dynamically get Template model (avoid breaking third party extensions)
        template_model = config.__class__.templates.rel.model
        return template_model.objects.all()

    def add_tagged_templates(self, config, request):
        """
        adds templates specified in incoming POST tag setting
        """
        tags = request.POST.get('tags')
        if not tags:
            return
        # retrieve tags and add them to current config
        tags = tags.split()
        queryset = self.get_template_queryset(config)
        templates = queryset.filter(tags__name__in=tags) \
                            .only('id') \
                            .distinct()
        for template in templates:
            config.templates.add(template)

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
        # try retrieving existing Device first
        # (key is not None only if CONSISTENT_REGISTRATION is enabled)
        try:
            device = self.model.objects.get(key=key)
            config = device.config
        # otherwise create new Device and Config
        except self.model.DoesNotExist:
            new = True
            config = self.init_object(last_ip=last_ip, **request.POST.dict())
            device = config.device
            try:
                device.full_clean()
                device.save()
                config.full_clean()
                config.save()
            except ValidationError as e:
                # dump message_dict as JSON,
                # this should make it easy to debug
                return ControllerResponse(json.dumps(e.message_dict, indent=4, sort_keys=True),
                                          content_type='text/plain',
                                          status=400)
        # update last_ip on existing configs
        else:
            new = False
            self.update_last_ip(config, request)
        # add templates specified in tags
        self.add_tagged_templates(config, request)
        # prepare response
        s = 'registration-result: success\n' \
            'uuid: {id}\n' \
            'key: {key}\n' \
            'hostname: {name}\n' \
            'is-new: {is_new}\n'
        attributes = device.__dict__.copy()
        attributes.update({
            'id': device.pk.hex,
            'key': device.key,
            'is_new': int(new)
        })
        return ControllerResponse(s.format(**attributes),
                                  content_type='text/plain',
                                  status=201)
