from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import m2m_changed
from django.utils.translation import ugettext_lazy as _

from .settings import REGISTRATION_ENABLED, SHARED_SECRET


class DjangoNetjsonconfigApp(AppConfig):
    name = 'django_netjsonconfig'
    label = 'django_netjsonconfig'
    verbose_name = _('Device Configurations')

    def connect_signals(self):
        """
        * m2m validation before templates are added to a config
        """
        from .models import Config
        m2m_changed.connect(Config.clean_templates,
                            sender=Config.templates.through)
        m2m_changed.connect(Config.templates_changed,
                            sender=Config.templates.through)

    def check_settings(self):
        if settings.DEBUG is False and REGISTRATION_ENABLED and not SHARED_SECRET:  # pragma: nocover
            raise ImproperlyConfigured('Security error: NETJSONCONFIG_SHARED_SECRET is not set. '
                                       'Please set it or disable auto-registration by setting '
                                       'NETJSONCONFIG_REGISTRATION_ENABLED to False')

    def ready(self):
        self.check_settings()
        self.connect_signals()
