from django.contrib import admin
from django import forms
from django.conf.urls import url
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response

from .models import Template, Device
from .base import TimeStampedEditableAdmin
from .utils import send_file


class TemplateAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'created', 'modified')
    list_filter = ('created',)
    search_fields = ('name',)

    class Media:
        css = {'all': ('css/admin/django-netjsonconfig.css',)}


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        exclude = []

    def clean_templates(self):
        templates = self.cleaned_data.get('templates', [])
        if templates:
            Device.clean_templates(action='pre_add',
                                   instance=self.instance,
                                   sender=self.instance.templates,
                                   reverse=False,
                                   model=self.instance.templates.model,
                                   pk_set=templates)
        return templates


class DeviceAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'created', 'modified')
    list_filter = ('created',)
    search_fields = ('name',)
    form = DeviceForm
    change_form_template = 'admin/device_change_form.html'
    visualize_template = 'admin/visualize_configuration.html'

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
        ] + super(DeviceAdmin, self).get_urls()

    def download_view(self, request, pk):
        device = get_object_or_404(self.model, pk=pk)
        config = device.backend_instance.generate()
        return send_file(filename='{0}.tar.gz'.format(device.name),
                         contents=config.getvalue())

    def visualize_view(self, request, pk):
        device = get_object_or_404(self.model, pk=pk)
        output = device.backend_instance.render()
        context = self.admin_site.each_context(request)
        context.update({
            'title': 'Visualize configuration: %s' % device.name,
            'object_id': device.pk,
            'original': device,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request),
            'change': True,
            'visualize': True,
            'output': output,
            'media': self.media,
        })
        return render_to_response(self.visualize_template, context)


admin.site.register(Template, TemplateAdmin)
admin.site.register(Device, DeviceAdmin)
