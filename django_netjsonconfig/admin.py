from django.contrib import admin

from .base.admin import (AbstractConfigForm, AbstractConfigInline, AbstractDeviceAdmin, AbstractTemplateAdmin,
                         AbstractVpnAdmin, AbstractVpnForm, BaseForm)
from .models import Config, Device, Template, Vpn


class ConfigForm(AbstractConfigForm):
    class Meta(AbstractConfigForm.Meta):
        model = Config


class TemplateForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = Template


class TemplateAdmin(AbstractTemplateAdmin):
    form = TemplateForm


class VpnForm(AbstractVpnForm):
    class Meta(AbstractVpnForm.Meta):
        model = Vpn


class VpnAdmin(AbstractVpnAdmin):
    form = VpnForm


class ConfigInline(AbstractConfigInline):
    model = Config
    form = ConfigForm
    extra = 0


class DeviceAdmin(AbstractDeviceAdmin):
    inlines = [ConfigInline]


admin.site.register(Device, DeviceAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Vpn, VpnAdmin)
