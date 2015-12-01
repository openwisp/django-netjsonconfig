from django.contrib import admin

from .models import Template, Device
from .base import TimeStampedEditableAdmin


class TemplateAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'created', 'modified')
    list_filter = ('created',)
    search_fields = ('name',)


class DeviceAdmin(TimeStampedEditableAdmin):
    list_display = ('name', 'created', 'modified')
    list_filter = ('created',)
    search_fields = ('name',)


admin.site.register(Template, TemplateAdmin)
admin.site.register(Device, DeviceAdmin)
