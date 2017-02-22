import logging

from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib.admin.templatetags.admin_static import static
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from .. import settings as app_settings
from ..utils import send_file
from ..widgets import JsonSchemaWidget
from .config import get_random_mac

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
        prefix = 'admin:{0}_{1}'.format(self.opts.app_label, self.model.__name__.lower())
        ctx = {'preview_url': reverse('{0}_preview'.format(prefix))}
        if pk:
            ctx.update({'download_url': reverse('{0}_download'.format(prefix), args=[pk])})
        return ctx

    def add_view(self, request, form_url='', extra_context={}):
        extra_context.update(self.get_extra_context())
        if 'config' in self.model.__name__.lower():
            template_model = self.model.templates.rel.model
            extra_context.update({
                'default_templates': [str(t.id) for t in template_model.objects.filter(default=True)]
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
        kwargs = {}
        unique = {}
        for key, value in request.POST.items():
            # skip keys that are not model fields
            try:
                field = self.model._meta.get_field(key)
            except FieldDoesNotExist:
                continue
            # skip m2m
            if field.many_to_many:
                continue
            # set aside unique field values
            if field.unique:
                unique[key] = value
            # adapt attribute names to the fact that we only
            # have pk of relations, therefore use {relation}_id
            elif field.is_relation:
                key = '{relation}_id'.format(relation=key)
                kwargs[key] = value
            # put regular field values in kwargs dict
            else:
                kwargs[key] = value
        # randomize name
        kwargs['name'] = self.model().pk.hex
        # include a random mac address to pass validation
        if 'mac_address' in request.POST:
            kwargs['mac_address'] = get_random_mac()
        # this object is instanciated only to generate the preview
        # it won't be saved to the database
        model = self.model(**kwargs)
        model.full_clean()
        # some field values must be filled-in after
        # validation in order to avoid unique checks
        for key, value in unique.items():
            setattr(model, key, value)
        return model

    preview_error_msg = _('Preview for {0} with name {1} failed')

    def preview_view(self, request):
        if request.method != 'POST':
            msg = _('Preview: request method {0} is not allowed').format(request.method)
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
            template_model = self.model.templates.rel.model
            templates = template_model.objects.filter(pk__in=template_ids.split(','))
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

    class Meta:
        exclude = []
        widgets = {'config': JsonSchemaWidget}


class AbstractConfigForm(BaseForm):
    def clean_templates(self):
        config_model = self.Meta.model
        # copy cleaned_data to avoid tampering with it
        data = self.cleaned_data.copy()
        templates = data.pop('templates', [])
        if self.instance._state.adding:
            # when adding self.instance is empty, we need to create a
            # temporary instance that we'll use just for validation
            config = config_model(**data)
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


class AbstractConfigAdmin(BaseConfigAdmin):
    list_display = ['name', 'backend', 'status', 'last_ip', 'created', 'modified']
    list_filter = ['backend', 'status', 'created']
    search_fields = ['id', 'name', 'key', 'mac_address', 'last_ip']
    readonly_fields = ['id_hex', 'status', 'last_ip']
    fields = ['name',
              'backend',
              'id_hex',
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

    def id_hex(self, obj):
        return obj.pk.hex

    id_hex.short_description = "UUID"

    def _get_fields(self, fields, request, obj=None):
        """
        removes "id" field in add view
        """
        if obj:
            return fields
        new_fields = fields[:]
        if 'id_hex' in new_fields:
            new_fields.remove('id_hex')
        return new_fields

    def get_fields(self, request, obj=None):
        return self._get_fields(self.fields, request, obj)

    def get_readonly_fields(self, request, obj=None):
        return self._get_fields(self.readonly_fields, request, obj)


class AbstractTemplateAdmin(BaseConfigAdmin):
    list_display = ['name', 'type', 'backend', 'default', 'created', 'modified']
    list_filter = ['backend', 'type', 'default', 'created']
    search_fields = ['name']
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
    actions_on_bottom = True
    save_on_top = True
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
