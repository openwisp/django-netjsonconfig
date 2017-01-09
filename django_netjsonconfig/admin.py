from django.contrib import admin

from .base.admin import (AbstractConfigAdmin, AbstractConfigForm,
                         AbstractTemplateAdmin, AbstractVpnAdmin,
                         AbstractVpnForm, BaseForm)
from .models import Config, Template, Vpn


class ConfigForm(AbstractConfigForm):
    class Meta(AbstractConfigForm.Meta):
        model = Config


class ConfigAdmin(AbstractConfigAdmin):
    form = ConfigForm


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


admin.site.register(Config, ConfigAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Vpn, VpnAdmin)
