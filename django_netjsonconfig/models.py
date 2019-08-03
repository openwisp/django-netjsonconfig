from django.core.exceptions import ValidationError
from django_x509.models import Ca, Cert

from .base.config import AbstractConfig, TemplatesVpnMixin
from .base.device import AbstractDevice
from .base.subscription import AbstractTemplateSubscription
from .base.tag import AbstractTaggedTemplate, AbstractTemplateTag
from .base.template import AbstractTemplate
from .base.vpn import AbstractVpn, AbstractVpnClient
from .utils import get_remote_template_data


class Config(TemplatesVpnMixin, AbstractConfig):
    """
    Concrete Config model
    """
    class Meta(AbstractConfig.Meta):
        abstract = False


class Device(AbstractDevice):
    """
    Concrete device model
    """
    class Meta(AbstractDevice.Meta):
        abstract = False


class TemplateTag(AbstractTemplateTag):
    """
    Concrete template tag model
    """
    class Meta(AbstractTemplateTag.Meta):
        abstract = False


class TaggedTemplate(AbstractTaggedTemplate):
    """
    tagged item model with support for UUID primary keys
    """
    class Meta(AbstractTaggedTemplate.Meta):
        abstract = False


class Vpn(AbstractVpn):
    """
    Concrete VPN model
    """
    class Meta(AbstractVpn.Meta):
        abstract = False


class Template(AbstractTemplate):
    """
    Concrete Template model
    """
    class Meta(AbstractTemplate.Meta):
        abstract = False

    # Define django_x509 concret model which will be
    # use at the abstract model.
    vpn_model = Vpn
    ca_model = Ca
    cert_model = Cert

    def clean(self):
        if self.sharing == 'import' or self.url:
            if not self.url:
                raise ValidationError({'url': 'URL is required for import of templates'})
            else:
                data = get_remote_template_data(self.url)
                self._set_field_values(data)
        super(Template, self).clean()


class VpnClient(AbstractVpnClient):
    """
    Concrete VpnClient model
    """
    class Meta(AbstractVpnClient.Meta):
        abstract = False


class TemplateSubscription(AbstractTemplateSubscription):
    """
    Concrete Template Subscription model
    """
    class Meta(AbstractTemplateSubscription.Meta):
        abstract = False
