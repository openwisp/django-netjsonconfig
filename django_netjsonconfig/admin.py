import logging

from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from . import settings as app_settings
from .models import Config, Template, Vpn
from .models.config import get_random_mac
from .utils import send_file
from .widgets import JsonSchemaWidget

logger = logging.getLogger(__name__)
prefix = 'django-netjsonconfig/'

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin as BaseAdmin
else:  # pragma: nocover
    from django.contrib.admin import ModelAdmin as BaseAdmin


class TimeStampedEditableAdmin(BaseAdmin):
    """
    ModelAdmin for TimeStampedEditableModel
    """
    def __init__(self, *args, **kwargs):
        self.readonly_fields += ('created', 'modified',)
        super(TimeStampedEditableAdmin, self).__init__(*args, **kwargs)


class BaseConfigAdmin(TimeStampedEditableAdmin):
    preview_template = None

    class Media:
        css = {'all': (static('{0}css/admin.css'.format(prefix)),)}
        js = [static('{0}/js/{1}'.format(prefix, f))
              for f in ('preview.js',
                        'unsaved_changes.js',
                        'uuid.js',
                        'switcher.js')]

    def get_extra_context(self, pk=None):
        prefix = 'admin:django_netjsonconfig_{}'.format(self.model.__name__.lower())
        ctx = {'preview_url': reverse('{0}_preview'.format(prefix))}
        if pk:
            ctx.update({'download_url': reverse('{0}_download'.format(prefix), args=[pk])})
        return ctx

    def add_view(self, request, form_url='', extra_context={}):
        extra_context.update(self.get_extra_context())
        if 'config' in self.model.__name__.lower():
            extra_context.update({
                'default_templates': [str(t.id) for t in Template.objects.filter(default=True)]
            })
        return super(BaseConfigAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, pk, form_url='', extra_context={}):
        extra_context.update(self.get_extra_context(pk))
        return super(BaseConfigAdmin, self).change_view(request, pk, form_url, extra_context)

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

    def _prepare_preview_model(self, request):
        # this object is instanciated only to generate the preview
        # it won't be saved to the database
        model = self.model(name=self.model().pk.hex,  # randomize
                           backend=request.POST.get('backend'),
                           config=request.POST.get('config'))
        # fill attributes that are not shared between all models conditionally
        for attr in ['host', 'ca', 'cert', 'dh']:
            attr_name = attr
            # relations are a special case
            if attr in ['ca', 'cert']:
                attr_name = '{0}_id'.format(attr)
            if request.POST.get(attr) is not None:
                setattr(model, attr_name, request.POST[attr])
        if request.POST.get('mac_address') is not None:
            model.mac_address = get_random_mac()
        model.full_clean()
        # some attributes must be added in after validation to avoid unique checks
        check_after = ['id', 'key', 'name', 'mac_address']
        for attr in check_after:
            if request.POST.get(attr) is not None:
                setattr(model, attr, request.POST[attr])
        return model

    preview_error_msg = 'Preview for {0} with name {1} failed'

    def preview_view(self, request):
        if request.method != 'POST':
            msg = 'Preview: request method {0} is not allowed'.format(request.method)
            logger.warning(msg, extra={'request': request, 'stack': True})
            return HttpResponse(status=405)
        error = None
        output = None
        # error message for eventual exceptions
        error_msg = self.preview_error_msg.format(self.model.__name__, request.POST.get('name'))
        try:
            model = self._prepare_preview_model(request)
        except ValidationError as e:
            logger.exception(error_msg, extra={'request': request})
            return HttpResponse(str(e), status=400)
        template_ids = request.POST.get('templates')
        if template_ids:
            templates = Template.objects.filter(pk__in=template_ids.split(','))
            try:
                templates = list(templates)  # evaluating queryset performs query
            except ValueError as e:
                logger.exception(error_msg, extra={'request': request})
                return HttpResponse(str(e), status=400)
        else:
            templates = None
        if not error:
            backend = model.get_backend_instance(template_instances=templates)
            try:
                model.clean_netjsonconfig_backend(backend)
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
        config = get_object_or_404(self.model, pk=pk)
        config_archive = config.generate()
        return send_file(filename='{0}.tar.gz'.format(config.name),
                         contents=config_archive.getvalue())


class BaseForm(forms.ModelForm):
    """
    Adds support for ``NETJSONCONFIG_DEFAULT_BACKEND``
    """
    if app_settings.DEFAULT_BACKEND:
        def __init__(self, *args, **kwargs):
            if 'initial' in kwargs:
                kwargs['initial'].update({'backend': app_settings.DEFAULT_BACKEND})
            super(BaseForm, self).__init__(*args, **kwargs)


class TemplateForm(BaseForm):
    class Meta:
        model = Template
        exclude = []
        widgets = {'config': JsonSchemaWidget}


class TemplateAdmin(BaseConfigAdmin):
    list_display = ('name', 'type', 'backend', 'default', 'created', 'modified')
    list_filter = ('backend', 'type', 'default', 'created',)
    search_fields = ('name',)
    fields = ['name',
              'type',
              'backend',
              'vpn',
              'auto_cert',
              'default',
              'config',
              'created',
              'modified']
    actions_on_bottom = True
    save_on_top = True
    form = TemplateForm


class ConfigForm(BaseForm):
    class Meta:
        model = Config
        exclude = []
        widgets = {'config': JsonSchemaWidget}

    def clean_templates(self):
        templates = self.cleaned_data.get('templates', [])
        if self.instance._state.adding:
            # when adding self.instance is empty, we need to create a
            # temporary instance that we'll use just for validation
            config = Config(name=self.data.get('name'),
                            backend=self.data.get('backend'),
                            config=self.data.get('config'))
        else:
            config = self.instance
        if config.backend and templates:
            Config.clean_templates(action='pre_add',
                                   instance=config,
                                   sender=config.templates,
                                   reverse=False,
                                   model=config.templates.model,
                                   pk_set=templates)
        return templates


class ConfigAdmin(BaseConfigAdmin):
    list_display = ('name', 'backend', 'status', 'last_ip', 'created', 'modified')
    list_filter = ('backend', 'status', 'created',)
    search_fields = ('id', 'name', 'key', 'mac_address', 'last_ip')
    readonly_fields = ['id', 'status', 'last_ip']
    fields = ['name',
              'backend',
              'id',
              'key',
              'mac_address',
              'status',
              'last_ip',
              'templates',
              'config',
              'created',
              'modified']
    actions_on_bottom = True
    save_on_top = True
    form = ConfigForm

    def _get_fields(self, fields, request, obj=None):
        """
        removes "id" field in add view
        """
        if obj:
            return fields
        new_fields = fields[:]
        if 'id' in new_fields:
            new_fields.remove('id')
        return new_fields

    def get_fields(self, request, obj=None):
        return self._get_fields(self.fields, request, obj)

    def get_readonly_fields(self, request, obj=None):
        return self._get_fields(self.readonly_fields, request, obj)


class VpnForm(forms.ModelForm):
    """
    Adds support for ``NETJSONCONFIG_DEFAULT_BACKEND``
    """
    if app_settings.DEFAULT_VPN_BACKEND:
        def __init__(self, *args, **kwargs):
            if 'initial' in kwargs:
                kwargs['initial'].update({'backend': app_settings.DEFAULT_VPN_BACKEND})
            super(VpnForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Vpn
        widgets = {
            'config': JsonSchemaWidget,
            'dh': forms.widgets.HiddenInput
        }
        exclude = []
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


class VpnAdmin(BaseConfigAdmin):
    list_display = ('name', 'backend', 'created', 'modified')
    list_filter = ('backend', 'ca', 'created',)
    search_fields = ('id', 'name', 'host')
    actions_on_bottom = True
    save_on_top = True
    form = VpnForm


admin.site.register(Template, TemplateAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Vpn, VpnAdmin)
