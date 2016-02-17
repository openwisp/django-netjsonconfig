from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .base import TimeStampedEditableAdmin
from .models import Config, Template
from .utils import send_file


class BaseConfigAdmin(TimeStampedEditableAdmin):
    preview_template = None

    class Media:
        css = {'all': ('css/admin/django-netjsonconfig.css',)}
        js = (
            'js/admin/preview.js',
            'js/admin/unsaved_changes.js',
            'js/admin/uuid.js'
        )

    def get_extra_context(self, pk=None):
        prefix = 'admin:django_netjsonconfig_{}'.format(self.model.__name__.lower())
        ctx = {'preview_url': reverse('{0}_preview'.format(prefix))}
        if pk:
            ctx.update({'download_url': reverse('{0}_download'.format(prefix), args=[pk])})
        return ctx

    def add_view(self, request, form_url='', extra_context={}):
        extra_context.update(self.get_extra_context())
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
            model = self.model(name=request.POST.get('name'),
                               backend=request.POST.get('backend'),
                               config=request.POST.get('config'))
            model.full_clean()
        except ValidationError as e:
            return HttpResponse(str(e), status=400)
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


class TemplateAdmin(BaseConfigAdmin):
    list_display = ('name', 'backend', 'created', 'modified')
    list_filter = ('backend', 'created',)
    search_fields = ('name',)
    actions_on_bottom = True
    save_on_top = True


class ConfigForm(forms.ModelForm):
    class Meta:
        model = Config
        exclude = []

    def clean_templates(self):
        templates = self.cleaned_data.get('templates', [])
        if self.instance._state.adding:
            # when adding self.instance is empty, we need to create a
            # temporary instance that we'll use just for validation
            config = Config(backend=self.data.get('backend'),
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
              'id',
              'key',
              'status',
              'last_ip',
              'templates',
              'backend',
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

admin.site.register(Template, TemplateAdmin)
admin.site.register(Config, ConfigAdmin)
