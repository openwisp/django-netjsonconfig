from django.contrib import admin
from django import forms
from django.conf.urls import url
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from .models import Template, Device
from .base import TimeStampedEditableAdmin


class TemplateAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'created', 'modified')
    list_filter = ('created',)
    search_fields = ('name',)


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

    def get_urls(self):
        options = getattr(self.model, '_meta')
        url_prefix = '{0}_{1}'.format(options.app_label, options.model_name)
        return [
            url(r'^download/(?P<pk>[^/]+)/$',
                self.admin_site.admin_view(self.download_view),
                name='{0}_download'.format(url_prefix))
        ] + super(DeviceAdmin, self).get_urls()

    def download_view(self, request, pk=None):
        device = get_object_or_404(self.model, pk=pk)
        device.backend_instance.generate(device.name)
        # TODO: avoid writing on disk
        # requires solving this https://github.com/openwisp/netjsonconfig/issues/32
        filename = '{0}.tar.gz'.format(device.name)
        f = open(filename, 'rb')
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        return response


admin.site.register(Template, TemplateAdmin)
admin.site.register(Device, DeviceAdmin)
