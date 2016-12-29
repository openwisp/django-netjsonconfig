import random

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from model_utils.fields import StatusField
from sortedm2m.fields import SortedManyToManyField

from .. import settings as app_settings
from ..validators import key_validator, mac_address_validator
from .base import AbstractConfig


def get_random_key():
    return get_random_string(length=32)


def get_random_mac():
    """
    used mainly to migrate from 0.3.x to 0.4.x and in tests
    """
    return '52:54:00:%02x:%02x:%02x' % (random.randint(0, 255),
                                        random.randint(0, 255),
                                        random.randint(0, 255))


class BaseConfig(AbstractConfig):
    """
    Abstract model implementing the
    NetJSON DeviceConfiguration object
    """
    STATUS = Choices('modified', 'running', 'error')
    status = StatusField(help_text=_(
        'modified means the configuration is not applied yet; '
        'running means applied and running; '
        'error means the configuration caused issues and it was rolledback'
    ))
    key = models.CharField(max_length=64,
                           unique=True,
                           db_index=True,
                           default=get_random_key,
                           validators=[key_validator],
                           help_text=_('unique key that can be used to '
                                       'download the configuration'))
    mac_address = models.CharField(max_length=17,
                                   unique=True,
                                   validators=[mac_address_validator])
    last_ip = models.GenericIPAddressField(blank=True,
                                           null=True,
                                           help_text=_('indicates the last ip from which the '
                                                       'configuration was downloaded from '
                                                       '(except downloads from this page)'))

    class Meta:
        abstract = True

    def clean(self):
        """
        modifies status if key attributes of the configuration
        have changed (queries the database)
        """
        super(BaseConfig, self).clean()
        if self._state.adding:
            return
        current = self.__class__.objects.get(pk=self.pk)
        for attr in ['name', 'backend', 'config']:
            if getattr(self, attr) != getattr(current, attr):
                self.status = 'modified'
                break

    def get_context(self):
        """
        additional context passed to netjsonconfig
        """
        c = {
            'id': str(self.id),
            'key': self.key,
            'name': self.name,
            'mac_address': self.mac_address
        }
        c.update(app_settings.CONTEXT)
        return c


BaseConfig._meta.get_field('config').blank = True


class TemplatesVpnMixin(models.Model):
    """
    Provides a mixin that adds two m2m relationships:
        * Template
        * Vpn
    """
    templates = SortedManyToManyField('django_netjsonconfig.Template',
                                      related_name='config_relations',
                                      verbose_name=_('templates'),
                                      blank=True,
                                      help_text=_('configuration templates, applied from'
                                                  'first to last'))
    vpn = models.ManyToManyField('django_netjsonconfig.Vpn',
                                 through='django_netjsonconfig.VpnClient',
                                 related_name='vpn_relations',
                                 verbose_name=_('VPN'),
                                 blank=True,
                                 help_text=_('Automated VPN configurations'))

    def save(self, *args, **kwargs):
        created = self._state.adding
        super(TemplatesVpnMixin, self).save(*args, **kwargs)
        if created:
            default = self.templates.model.objects.filter(default=True)
            if default:
                self.templates.add(*default)

    @classmethod
    def clean_templates(cls, action, instance, pk_set, **kwargs):
        """
        validates resulting configuration of config + templates
        raises a ValidationError if invalid
        must be called from forms or APIs
        this method is called from a django signal (m2m_changed)
        see django_netjsonconfig.apps.DjangoNetjsonconfigApp.connect_signals
        """
        if action != 'pre_add':
            return
        # coming from signal
        if isinstance(pk_set, set):
            template_model = cls.templates.rel.model
            templates = template_model.objects.filter(pk__in=list(pk_set))
        # coming from admin ModelForm
        else:
            templates = pk_set
        backend = instance.get_backend_instance(template_instances=templates)
        try:
            cls.clean_netjsonconfig_backend(backend)
        except ValidationError as e:
            message = 'There is a conflict with the specified templates. {0}'
            message = message.format(e.message)
            raise ValidationError(message)

    @classmethod
    def templates_changed(cls, action, instance, **kwargs):
        """
        this method is called from a django signal (m2m_changed)
        see django_netjsonconfig.apps.DjangoNetjsonconfigApp.connect_signals
        """
        if action not in ['post_add', 'post_remove', 'post_clear']:
            return
        if instance.status != 'modified':
            instance.status = 'modified'
            instance.save()

    @classmethod
    def manage_vpn_clients(cls, action, instance, pk_set, **kwargs):
        """
        automatically manages associated vpn clients if the
        instance is using templates which have type set to "VPN"
        and "auto_cert" set to True.
        This method is called from a django signal (m2m_changed)
        see django_netjsonconfig.apps.DjangoNetjsonconfigApp.connect_signals
        """
        if action not in ['post_add', 'post_remove', 'post_clear']:
            return
        vpn_client_model = cls.vpn.through
        # coming from signal
        if isinstance(pk_set, set):
            template_model = cls.templates.rel.model
            templates = template_model.objects.filter(pk__in=list(pk_set))
        # coming from admin ModelForm
        else:
            templates = pk_set
        # when clearing all templates
        if action == 'post_clear':
            for client in instance.vpnclient_set.all():
                client.delete()
            return
        # when adding or removing specific templates
        for template in templates.filter(type='vpn'):
            if action == 'post_add':
                client = vpn_client_model(config=instance,
                                          vpn=template.vpn,
                                          auto_cert=template.auto_cert)
                client.full_clean()
                client.save()
            elif action == 'post_remove':
                for client in instance.vpnclient_set.filter(vpn=template.vpn):
                    client.delete()

    def get_context(self):
        """
        adds VPN client certificates to configuration context
        """
        c = super(TemplatesVpnMixin, self).get_context()
        for vpnclient in self.vpnclient_set.all().select_related('vpn', 'cert'):
            vpn = vpnclient.vpn
            vpn_id = vpn.pk.hex
            context_keys = vpn._get_auto_context_keys()
            ca = vpn.ca
            cert = vpnclient.cert
            # CA
            ca_filename = 'ca-{0}-{1}.pem'.format(ca.pk, ca.common_name)
            ca_path = '{0}/{1}'.format(app_settings.CERT_PATH, ca_filename)
            # update context
            c.update({
                context_keys['ca_path']: ca_path,
                context_keys['ca_contents']: ca.certificate
            })
            # conditional needed for VPN without x509 authentication
            # eg: simple password authentication
            if cert:
                # cert
                cert_filename = 'client-{0}.pem'.format(vpn_id)
                cert_path = '{0}/{1}'.format(app_settings.CERT_PATH, cert_filename)
                # key
                key_filename = 'key-{0}.pem'.format(vpn_id)
                key_path = '{0}/{1}'.format(app_settings.CERT_PATH, key_filename)
                # update context
                c.update({
                    context_keys['cert_path']: cert_path,
                    context_keys['cert_contents']: cert.certificate,
                    context_keys['key_path']: key_path,
                    context_keys['key_contents']: cert.private_key,
                })
        return c

    class Meta:
        abstract = True


class Config(TemplatesVpnMixin, BaseConfig):
    """
    Concrete Config model
    """
    class Meta:
        verbose_name = _('configuration')
        verbose_name_plural = _('configurations')
