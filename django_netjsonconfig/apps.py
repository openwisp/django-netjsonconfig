from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import m2m_changed, post_delete
from django.utils.translation import ugettext_lazy as _

from .settings import REGISTRATION_ENABLED, SHARED_SECRET


class DjangoNetjsonconfigApp(AppConfig):
    name = 'django_netjsonconfig'
    label = 'django_netjsonconfig'
    verbose_name = _('Network Configuration')

    def __setmodels__(self):
        """
        This method allows third party apps to set their own custom models
        """
        from .models import Config, VpnClient
        self.config_model = Config
        self.vpnclient_model = VpnClient

    def connect_signals(self):
        """
        * m2m validation before templates are added/removed to a config
        * automatic vpn client management on m2m_changed
        * automatic vpn client removal
        """
        m2m_changed.connect(self.config_model.clean_templates,
                            sender=self.config_model.templates.through)
        m2m_changed.connect(self.config_model.templates_changed,
                            sender=self.config_model.templates.through)
        m2m_changed.connect(self.config_model.manage_vpn_clients,
                            sender=self.config_model.templates.through)
        post_delete.connect(self.vpnclient_model.post_delete,
                            sender=self.vpnclient_model)

    def check_settings(self):
        if settings.DEBUG is False and REGISTRATION_ENABLED and not SHARED_SECRET:  # pragma: nocover
            raise ImproperlyConfigured('Security error: NETJSONCONFIG_SHARED_SECRET is not set. '
                                       'Please set it or disable auto-registration by setting '
                                       'NETJSONCONFIG_REGISTRATION_ENABLED to False')

    def ready(self):
        self.__setmodels__()
        self.check_settings()
        self.connect_signals()
