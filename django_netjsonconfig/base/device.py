from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..utils import get_random_key
from ..validators import key_validator, mac_address_validator
from .base import BaseModel


class AbstractDevice(BaseModel):
    """
    Base device model
    Stores information related to the
    physical properties of a network device
    """
    mac_address = models.CharField(max_length=17,
                                   unique=True,
                                   validators=[mac_address_validator],
                                   help_text=_('primary mac address'))
    key = models.CharField(max_length=64,
                           unique=True,
                           db_index=True,
                           default=get_random_key,
                           validators=[key_validator],
                           help_text=_('unique device key'))
    model = models.CharField(max_length=64,
                             blank=True,
                             help_text=_('device model and manufacturer'))
    os = models.CharField(_('operating system'),
                          blank=True,
                          max_length=128,
                          help_text=_('operating system identifier'))
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True

    def clean(self):
        """
        modifies related config status if name
        attribute is changed (queries the database)
        """
        super(AbstractDevice, self).clean()
        if self._state.adding:
            return
        current = self.__class__.objects.get(pk=self.pk)
        if self.name != current.name and self._has_config():
            self.config.status = 'modified'
            self.config.save()

    def _has_config(self):
        return hasattr(self, 'config')

    def _get_config_attr(self, attr):
        """
        gets property or calls method of related config object
        without rasing an exception if config is not set
        """
        if not self._has_config():
            return None
        attr = getattr(self.config, attr)
        return attr() if callable(attr) else attr

    @property
    def backend(self):
        """
        Used as a shortcut for display purposes
        (eg: admin site)
        """
        return self._get_config_attr('get_backend_display')

    @property
    def status(self):
        """
        Used as a shortcut for display purposes
        (eg: admin site)
        """
        return self._get_config_attr('get_status_display')

    @property
    def last_ip(self):
        """
        Used as a shortcut for display purposes
        (eg: admin site)
        """
        return self._get_config_attr('last_ip')

    def get_default_templates(self):
        """
        calls `get_default_templates` of related
        config object (or new config instance)
        """
        if self._has_config():
            c = self.config
        else:
            c = self.get_config_model()()
        return c.get_default_templates()

    @classmethod
    def get_config_model(cls):
        return cls._meta.get_field('config').related_model
