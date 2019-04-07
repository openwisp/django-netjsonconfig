import logging

from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from openwisp_utils.admin import TimeReadonlyAdminMixin

from .. import settings as app_settings
from ..utils import send_file
from ..widgets import JsonSchemaWidget

logger = logging.getLogger(__name__)
prefix = 'django-netjsonconfig/'

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin as ModelAdmin
else:  # pragma: nocover
    from django.contrib.admin import ModelAdmin


class BaseAdmin(TimeReadonlyAdminMixin, ModelAdmin):
    pass


class BaseConfigAdmin(BaseAdmin):
    preview_template = None
    actions_on_bottom = True
    save_on_top = True

    class Media:
        css = {'all': (static('{0}css/admin.css'.format(prefix)),)}
        js = [static('{0}js/{1}'.format(prefix, f))
              for f in ('tabs.js',
                        'preview.js',
                        'unsaved_changes.js',
                        'uuid.js',
                        'switcher.js')]

    def get_extra_context(self, pk=None):
        prefix = 'admin:{0}_{1}'.format(self.opts.app_label, self.model.__name__.lower())
        text = _('Preview configuration')
        ctx = {
            'additional_buttons': [
                {
                    'type': 'button',
                    'url': reverse('{0}_preview'.format(prefix)),
                    'class': 'previewlink',
                    'value': text,
                    'title': '{0} (ALT+P)'.format(text)
                }
            ]
        }
        if pk:
            ctx['download_url'] = reverse('{0}_download'.format(prefix), args=[pk])
            if self.model.__name__ == 'Device' and not self.model.objects.get(pk=pk)._has_config():
                ctx['download_url'] = None
        return ctx

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(self.get_extra_context())
        instance = self.model()
        if hasattr(instance, 'get_default_templates'):
            templates = instance.get_default_templates()
            templates = [str(t.id) for t in templates]
            extra_context.update({'default_templates': templates})
        return super(BaseConfigAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = self.get_extra_context(object_id)
        return super(BaseConfigAdmin, self).change_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        options = getattr(self.model, '_meta')
        url_prefix = '{0}_{1}'.format(options.app_label, options.model_name)
        return [
            url(r'^download/(?P<pk>[^/]+)/$',
                self.admin_site.admin_view(self.download_view),
                name='{0}_download'.format(url_prefix)),
            url(r'^preview/$',
                self.admin_site.admin_view(self.preview_view),
                name='{0}_preview'.format(url_prefix))
        ] + super(BaseConfigAdmin, self).get_urls()

    def _get_config_model(self):
        model = self.model
        if hasattr(model, 'get_backend_instance'):
            return model
        return model.get_config_model()

    def _get_preview_instance(self, request):
        """
        returns a temporary preview instance used for preview
        """
        kwargs = {}
        config_model = self._get_config_model()
        for key, value in request.POST.items():
            # skip keys that are not model fields
            try:
                field = config_model._meta.get_field(key)
            except FieldDoesNotExist:
                continue
            # skip m2m
            if field.many_to_many:
                continue
            # skip if falsy value and PK or relations
            elif not value and any([field.primary_key, field.is_relation]):
                continue
            # adapt attribute names to the fact that we only
            # have pk of relations, therefore use {relation}_id
            elif field.is_relation:
                key = '{relation}_id'.format(relation=key)
                # pass non-empty string or None
                kwargs[key] = value or None
            # put regular field values in kwargs dict
            else:
                kwargs[key] = value
        # default context to None to avoid exception
        if 'context' in kwargs:
            kwargs['context'] = kwargs['context'] or None
        # this object is instanciated only to generate the preview
        # it won't be saved to the database
        instance = config_model(**kwargs)
        instance.full_clean(exclude=['device'],
                            validate_unique=False)
        return instance

    preview_error_msg = _('Preview for {0} with name {1} failed')

    def preview_view(self, request):
        if request.method != 'POST':
            msg = _('Preview: request method {0} is not allowed').format(request.method)
            logger.warning(msg, extra={'request': request, 'stack': True})
            return HttpResponse(status=405)
        config_model = self._get_config_model()
        error = None
        output = None
        # error message for eventual exceptions
        error_msg = self.preview_error_msg.format(config_model.__name__, request.POST.get('name'))
        try:
            instance = self._get_preview_instance(request)
        except Exception as e:
            logger.exception(error_msg, extra={'request': request})
            # return 400 for validation errors, otherwise 500
            status = 400 if e.__class__ is ValidationError else 500
            return HttpResponse(str(e), status=status)
        template_ids = request.POST.get('templates')
        if template_ids:
            template_model = config_model.get_template_model()
            templates = template_model.objects.filter(pk__in=template_ids.split(','))
            try:
                templates = list(templates)  # evaluating queryset performs query
            except ValidationError as e:
                logger.exception(error_msg, extra={'request': request})
                return HttpResponse(str(e), status=400)
        else:
            templates = None
        if not error:
            backend = instance.get_backend_instance(template_instances=templates)
            try:
                instance.clean_netjsonconfig_backend(backend)
                output = backend.render()
            except ValidationError as e:
                error = str(e)
        context = self.admin_site.each_context(request)
        opts = self.model._meta
        context.update({
            'is_popup': True,
            'opts': opts,
            'change': False,
            'output': output,
            'media': self.media,
            'error': error,
        })
        return TemplateResponse(request, self.preview_template or [
            'admin/%s/%s/preview.html' % (opts.app_label, opts.model_name),
            'admin/%s/preview.html' % opts.app_label
        ], context)

    def download_view(self, request, pk):
        instance = get_object_or_404(self.model, pk=pk)
        if hasattr(instance, 'generate'):
            config = instance
        elif hasattr(instance, 'config'):
            config = instance.config
        else:
            raise Http404()
        config_archive = config.generate()
        return send_file(filename='{0}.tar.gz'.format(config.name),
                         contents=config_archive.getvalue())


class BaseForm(forms.ModelForm):
    """
    Adds support for ``NETJSONCONFIG_DEFAULT_BACKEND``
    """
    if app_settings.DEFAULT_BACKEND:
        def __init__(self, *args, **kwargs):
            # set initial backend value to use the default
            # backend but only for new instances
            if 'instance' not in kwargs:
                kwargs.setdefault('initial', {})
                kwargs['initial'].update({'backend': app_settings.DEFAULT_BACKEND})
            super(BaseForm, self).__init__(*args, **kwargs)

    class Meta:
        exclude = []
        widgets = {'config': JsonSchemaWidget}


class AbstractConfigForm(BaseForm):
    def get_temp_model_instance(self, **options):
        return self.Meta.model(**options)

    def clean_templates(self):
        config_model = self.Meta.model
        # copy cleaned_data to avoid tampering with it
        data = self.cleaned_data.copy()
        templates = data.pop('templates', [])
        if self.instance._state.adding:
            # when adding self.instance is empty, we need to create a
            # temporary instance that we'll use just for validation
            config = self.get_temp_model_instance(**data)
        else:
            config = self.instance
        if config.backend and templates:
            config_model.clean_templates(action='pre_add',
                                         instance=config,
                                         sender=config.templates,
                                         reverse=False,
                                         model=config.templates.model,
                                         pk_set=templates)
        return templates


class AbstractConfigInline(TimeReadonlyAdminMixin, admin.StackedInline):
    verbose_name_plural = _('Device configuration details')
    readonly_fields = ['status']
    fields = ['backend',
              'status',
              'templates',
              'context',
              'config',
              'created',
              'modified']
    change_select_related = ('device',)

    def get_queryset(self, request):
        qs = super(AbstractConfigInline, self).get_queryset(request)
        return qs.select_related(*self.change_select_related)


class AbstractDeviceAdmin(BaseConfigAdmin):
    list_display = ['name', 'backend', 'config_status',
                    'ip', 'created', 'modified']
    search_fields = ['id', 'name', 'mac_address', 'key', 'model', 'os', 'system']
    list_filter = ['config__backend',
                   'config__templates',
                   'config__status',
                   'created']
    list_select_related = ('config',)
    readonly_fields = ['id_hex', 'last_ip', 'management_ip']
    fields = ['name',
              'mac_address',
              'id_hex',
              'key',
              'last_ip',
              'management_ip',
              'model',
              'os',
              'system',
              'notes',
              'created',
              'modified']
    if app_settings.HARDWARE_ID_ENABLED:
        list_display.insert(0, 'hardware_id')
        search_fields.insert(1, 'hardware_id')
        fields.insert(0, 'hardware_id')

    def id_hex(self, obj):
        return obj.pk.hex

    id_hex.short_description = 'UUID'

    def ip(self, obj):
        mngmt_ip = obj.management_ip if app_settings.MANAGEMENT_IP_DEVICE_LIST else None
        return mngmt_ip or obj.last_ip

    ip.short_description = _('IP address')

    def config_status(self, obj):
        return obj.config.status

    config_status.short_description = _('config status')

    def _get_fields(self, fields, request, obj=None):
        """
        removes readonly_fields in add view
        """
        if obj:
            return fields
        new_fields = fields[:]
        for field in self.readonly_fields:
            if field in new_fields:
                new_fields.remove(field)
        return new_fields

    def get_fields(self, request, obj=None):
        return self._get_fields(self.fields, request, obj)

    def get_readonly_fields(self, request, obj=None):
        return self._get_fields(self.readonly_fields, request, obj)

    def _get_preview_instance(self, request):
        c = super(AbstractDeviceAdmin, self)._get_preview_instance(request)
        c.device = self.model(id=request.POST.get('id'),
                              name=request.POST.get('name'),
                              mac_address=request.POST.get('mac_address'),
                              key=request.POST.get('key'))
        return c


if not app_settings.BACKEND_DEVICE_LIST:  # pragma: nocover
    AbstractDeviceAdmin.list_display.remove('backend')
    AbstractDeviceAdmin.list_filter.remove('config__backend')


class AbstractTemplateAdmin(BaseConfigAdmin):
    list_display = ['name', 'type', 'backend', 'default', 'created', 'modified']
    list_filter = ['backend', 'type', 'default', 'created']
    search_fields = ['name']
    fields = ['name',
              'type',
              'backend',
              'vpn',
              'auto_cert',
              'tags',
              'default',
              'config',
              'created',
              'modified']


class AbstractVpnForm(forms.ModelForm):
    """
    Adds support for ``NETJSONCONFIG_DEFAULT_BACKEND``
    """
    if app_settings.DEFAULT_VPN_BACKEND:
        def __init__(self, *args, **kwargs):
            if 'initial' in kwargs:
                kwargs['initial'].update({'backend': app_settings.DEFAULT_VPN_BACKEND})
            super(AbstractVpnForm, self).__init__(*args, **kwargs)

    class Meta:
        widgets = {
            'config': JsonSchemaWidget,
            'dh': forms.widgets.HiddenInput
        }
        exclude = []


class AbstractVpnAdmin(BaseConfigAdmin):
    list_display = ['name', 'backend', 'created', 'modified']
    list_filter = ['backend', 'ca', 'created']
    search_fields = ['id', 'name', 'host']
    fields = ['name',
              'host',
              'ca',
              'cert',
              'backend',
              'notes',
              'dh',
              'config',
              'created',
              'modified']
