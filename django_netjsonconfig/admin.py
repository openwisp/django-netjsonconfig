from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .base import TimeStampedEditableAdmin
from .models import Config, Template, Vpn
from .settings import DEFAULT_BACKEND
from .utils import send_file
from .widgets import JsonSchemaWidget

prefix = 'django-netjsonconfig/'


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

    def preview_view(self, request):
        if request.method != 'POST':
            return HttpResponse(status=405)
        error = None
        output = None
        try:
            # this object is instanciated only to generate the preview
            # it won't be saved to the database
            model = self.model(name=request.POST.get('name'),
                               backend=request.POST.get('backend'),
                               config=request.POST.get('config'))
            model.full_clean()
        except ValidationError as e:
            return HttpResponse(str(e), status=400)
        # add id and key after validation to avoid unique checks
        if request.POST.get('id') and request.POST.get('key'):
            model.id = request.POST.get('id')
            model.key = request.POST.get('key')
        template_ids = request.POST.get('templates')
        if template_ids:
            templates = Template.objects.filter(pk__in=template_ids.split(','))
            try:
                templates = list(templates)  # evaluating queryset performs query
            except ValueError as e:
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
        config_archive = config.backend_instance.generate()
        return send_file(filename='{0}.tar.gz'.format(config.name),
                         contents=config_archive.getvalue())


class BaseForm(forms.ModelForm):
    """
    Adds support for ``NETJSONCONFIG_DEFAULT_BACKEND``
    """
    if DEFAULT_BACKEND:
        def __init__(self, *args, **kwargs):
            if 'initial' in kwargs:
                kwargs['initial'].update({'backend': DEFAULT_BACKEND})
            super(BaseForm, self).__init__(*args, **kwargs)


class TemplateForm(BaseForm):
    class Meta:
        model = Template
        exclude = []
        widgets = {'config': JsonSchemaWidget}


class TemplateAdmin(BaseConfigAdmin):
    list_display = ('name', 'backend', 'default', 'created', 'modified')
    list_filter = ('backend', 'type', 'default', 'created',)
    search_fields = ('name',)
    fields = ['name',
              'type',
              'backend',
              'vpn',
              'create_cert',
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
    search_fields = ('id', 'name', 'key', 'last_ip')
    readonly_fields = ['id', 'status', 'last_ip']
    fields = ['name',
              'backend',
              'id',
              'key',
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


class VpnAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'backend', 'created', 'modified')
    list_filter = ('backend', 'created',)
    search_fields = ('id', 'name')
    actions_on_bottom = True
    save_on_top = True


admin.site.register(Template, TemplateAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Vpn, VpnAdmin)
