from django.contrib import admin

from .base.admin import (AbstractConfigForm, AbstractConfigInline, AbstractDeviceAdmin, AbstractTemplateAdmin,
                         AbstractVpnAdmin, AbstractVpnForm, BaseForm)
from .models import Config, Device, Template, TemplateSubscription, Vpn


class ConfigForm(AbstractConfigForm):
    class Meta(AbstractConfigForm.Meta):
        model = Config


class TemplateForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = Template


class TemplateAdmin(AbstractTemplateAdmin):
    form = TemplateForm
    # Vpn model will be used to delete any Vpn and Ca
    # which wwere associated with this Template
    # during unsubscription.
    # Template Subscription model is used to get number of
    # of subscribers for list_display
    template_subscription_model = TemplateSubscription
    vpn_model = Vpn


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
