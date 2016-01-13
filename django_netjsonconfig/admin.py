from django.contrib import admin
from django import forms
from django.conf.urls import url
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404

from .models import Template, Config
from .base import TimeStampedEditableAdmin
from .utils import send_file


class TemplateAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'backend', 'created', 'modified')
    list_filter = ('backend', 'created',)
    search_fields = ('name',)
    actions_on_bottom = True
    save_on_top = True

    class Media:
        css = {'all': ('css/admin/django-netjsonconfig.css',)}


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
        if templates:
            Config.clean_templates(action='pre_add',
                                   instance=config,
                                   sender=config.templates,
                                   reverse=False,
                                   model=config.templates.model,
                                   pk_set=templates)
        return templates


class ConfigAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'backend', 'created', 'modified')
    list_filter = ('backend', 'created',)
    search_fields = ('name', 'key')
    fields = ('name',
              'key',
              'templates',
              'backend',
              'config',
              'created',
              'modified')
    actions_on_bottom = True
    save_on_top = True
    form = ConfigForm
    visualize_template = None

    class Media:
        css = {'all': ('css/admin/django-netjsonconfig.css',)}

    def get_urls(self):
        options = getattr(self.model, '_meta')
        url_prefix = '{0}_{1}'.format(options.app_label, options.model_name)
        return [
            url(r'^download/(?P<pk>[^/]+)/$',
                self.admin_site.admin_view(self.download_view),
                name='{0}_download'.format(url_prefix)),
            url(r'^visualize/(?P<pk>[^/]+)/$',
                self.admin_site.admin_view(self.visualize_view),
                name='{0}_visualize'.format(url_prefix))
        ] + super(ConfigAdmin, self).get_urls()

    def download_view(self, request, pk):
        config = get_object_or_404(self.model, pk=pk)
        config_archive = config.backend_instance.generate()
        return send_file(filename='{0}.tar.gz'.format(config.name),
                         contents=config_archive.getvalue())

    def visualize_view(self, request, pk):
        config = get_object_or_404(self.model, pk=pk)
        output = config.backend_instance.render()
        context = self.admin_site.each_context(request)
        opts = self.model._meta
        context.update({
            'title': 'Visualize configuration: %s' % config.name,
            'object_id': config.pk,
            'original': config,
            'opts': opts,
            'has_change_permission': self.has_change_permission(request),
            'change': True,
            'visualize': True,
            'output': output,
            'media': self.media,
        })
        return TemplateResponse(request, self.visualize_template or [
            'admin/%s/%s/visualize_configuration.html' % (opts.app_label, opts.model_name),
        ], context)


admin.site.register(Template, TemplateAdmin)
admin.site.register(Config, ConfigAdmin)
