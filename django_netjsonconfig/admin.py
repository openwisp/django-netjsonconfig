from django.contrib import admin
from django import forms

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


admin.site.register(Template, TemplateAdmin)
admin.site.register(Device, DeviceAdmin)
