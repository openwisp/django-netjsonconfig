from collections import OrderedDict

import requests
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from requests.exceptions import ConnectionError
from taggit.managers import TaggableManager

from ..settings import DEFAULT_AUTO_CERT
from ..utils import get_random_key
from ..validators import key_validator
from .base import BaseConfig

TYPE_CHOICES = (
    ('generic', _('Generic')),
    ('vpn', _('VPN-client')),
)
SHARING_CHOICES = (
    ('private', _('Private')),
    ('public', _('Public')),
    ('secret_key', _('Shared via secret key')),
    ('import', _('Import'))
)


def default_auto_cert():
    """
    returns the default value for auto_cert field
    (this avoids to set the exact default value in the database migration)
    """
    return DEFAULT_AUTO_CERT


class AbstractTemplate(BaseConfig):
    """
    Abstract model implementing a
    netjsonconfig template
    """
    tags = TaggableManager(through='django_netjsonconfig.TaggedTemplate', blank=True,
                           help_text=_('A comma-separated list of template tags, may be used '
                                       'to ease auto configuration with specific settings (eg: '
                                       '4G, mesh, WDS, VPN, ecc.)'))
    vpn = models.ForeignKey('django_netjsonconfig.Vpn',
                            verbose_name=_('VPN'),
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE)
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
    sharing = models.CharField(_('Sharing settings'),
                               choices=SHARING_CHOICES,
                               default='private',
                               max_length=16,
                               db_index=True,
                               help_text=_('Whether to keep this template private, share it publicly, '
                                           'share it privately using a secret key or import its '
                                           'contents from another source'))
    key = models.CharField(max_length=64,
                           null=True,
                           blank=True,
                           default=get_random_key,
                           validators=[key_validator],
                           verbose_name=_('Secret key'),
                           help_text=_('Secret key needed to import the template'))
    description = models.TextField(_('Description'),
                                   blank=True,
                                   null=True,
                                   help_text=_('Public description of this template'))
    notes = models.TextField(_('Notes'),
                             blank=True,
                             null=True,
                             help_text=_('Internal notes for administrators'))
    default_values = JSONField(_('Default Values'),
                               default=dict,
                               blank=True,
                               help_text=_('A dictionary containing the default '
                                           'values for the variables used by this '
                                           'template; these default variables will '
                                           'be used during schema validation.'),
                               load_kwargs={'object_pairs_hook': OrderedDict},
                               dump_kwargs={'indent': 4})
    url = models.URLField(_('Import URL'),
                          max_length=200,
                          null=True,
                          blank=True,
                          help_text=_('URL from which the template will be imported'))
    __template__ = True

    class Meta:
        abstract = True
        verbose_name = _('template')
        verbose_name_plural = _('templates')

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
        super(AbstractTemplate, self).save(*args, **kwargs)
        # update relations
        if update_related_config_status:
            self._update_related_config_status()

    def _update_related_config_status(self):
        self.config_relations.update(status='modified')
        for config in self.config_relations.all():
            config._send_config_modified_signal()

    def clean(self, *args, **kwargs):
        """
        * ensures VPN is selected if type is VPN
        * clears VPN specific fields if type is not VPN
        * automatically determines configuration if necessary
        """
        if self.sharing == 'public' or self.sharing == 'secret_key':
            if not self.description:
                raise ValidationError(
                    {'description': _('Please enter a description of the shared template')})
        if self.sharing != 'secret_key':
            self.key = None
        if self.type == 'vpn' and not self.vpn:
            raise ValidationError({
                'vpn': _('A VPN must be selected when template type is "VPN"')
            })
        elif self.type != 'vpn':
            self.vpn = None
            self.auto_cert = False
        if self.type == 'vpn' and not self.config:
            self.config = self.vpn.auto_client(auto_cert=self.auto_cert)
        super(AbstractTemplate, self).clean(*args, **kwargs)

    def get_context(self):
        return self.default_values or {}

    def _get_remote_template_data(self):
        """
        Gets the template data from the
        remote serialization API
        """
        try:
            response = requests.get(self.url)
        except ConnectionError:
            raise ValidationError({'url': 'Connections to the server with this URL has issues'})
        if response.status_code == 404:
            raise ValidationError({'url': 'URL is not reachable'})
        else:
            try:
                data = response.json()
            except ValueError:
                raise ValidationError({'url': 'The content of this URL is not useful'})
            return data

    def _set_field_values(self, data):
        """
        sets the remote data to the respective template fields
        """
        self.id = data['id']
        self.config = data['config']
        self.default_values = data['default_values']
        self.auto_cert = data['auto_cert']
        self.backend = data['backend']
        self.key = data['key']
        for t in data['tags']:
            self.tags.add(t)
        if data['type'] == 'vpn':
            vpn_ca = self.ca_model(**data['vpn']['ca'])
            vpn_ca.full_clean()
            vpn_ca.save()
            data['vpn']['cert']['ca'] = vpn_ca
            vpn_cert = self.cert_model(**data['vpn']['cert'])
            vpn_cert.full_clean()
            vpn_cert.save()
            data['vpn']['ca'] = vpn_ca
            data['vpn']['cert'] = vpn_cert
            vpn = self.vpn_model(**data['vpn'])
            vpn.full_clean()
            vpn.save()
            self.vpn = vpn
        self.type = data['type']


AbstractTemplate._meta.get_field('config').blank = True
