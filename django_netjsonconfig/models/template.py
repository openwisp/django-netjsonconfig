from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from ..settings import DEFAULT_AUTO_CERT
from .base import AbstractConfig

TYPE_CHOICES = (
    ('generic', _('Generic')),
    ('vpn', _('VPN-client')),
)


def default_auto_cert():
    """
    returns the default value for auto_cert field
    (this avoids to set the exact default value in the database migration)
    """
    return DEFAULT_AUTO_CERT


@python_2_unicode_compatible
class BaseTemplate(AbstractConfig):
    """
    Abstract model implementing a
    netjsonconfig template
    """
    vpn = models.ForeignKey('django_netjsonconfig.Vpn',
                            verbose_name=_('VPN'),
                            blank=True,
                            null=True)
    type = models.CharField(_('type'),
                            max_length=16,
                            choices=TYPE_CHOICES,
                            default='generic',
                            db_index=True,
                            help_text=_('template type, determines which '
                                        'features are available'))
    default = models.BooleanField(_('enabled by default'),
                                  default=False,
                                  db_index=True,
                                  help_text=_('whether new configurations will have '
                                              'this template enabled by default'))
    auto_cert = models.BooleanField(_('auto certificate'),
                                    default=default_auto_cert,
                                    db_index=True,
                                    help_text=_('whether x509 client certificates should '
                                                'be automatically managed behind the scenes '
                                                'for each configuration using this template, '
                                                'valid only for the VPN type'))
    __template__ = True

    class Meta:
        abstract = True

    def __str__(self):
        return '[{0}-{1}] {2}'.format(self.get_type_display(),
                                      self.get_backend_display(),
                                      self.name)

    def save(self, *args, **kwargs):
        """
        modifies status of related configs
        if key attributes have changed (queries the database)
        """
        update_related_config_status = False
        if not self._state.adding:
            current = self.__class__.objects.get(pk=self.pk)
            for attr in ['backend', 'config']:
                if getattr(self, attr) != getattr(current, attr):
                    update_related_config_status = True
                    break
        # save current changes
        super(BaseTemplate, self).save(*args, **kwargs)
        # update relations
        if update_related_config_status:
            self.config_relations.update(status='modified')

    def clean(self, *args, **kwargs):
        """
        * ensures VPN is selected if type is VPN
        * clears VPN specific fields if type is not VPN
        * automatically determines configuration if necessary
        """
        super(BaseTemplate, self).clean(*args, **kwargs)
        if self.type == 'vpn' and not self.vpn:
            raise ValidationError({
                'vpn': _('A VPN must be selected when template type is "VPN"')
            })
        elif self.type != 'vpn':
            self.vpn = None
            self.auto_cert = False
        if self.type == 'vpn' and not self.config:
            self.config = self.vpn.auto_client(auto_cert=self.auto_cert)


BaseTemplate._meta.get_field('config').blank = True


class Template(BaseTemplate):
    """
    Concrete Template model
    """
    pass
