from .base.config import AbstractConfig, TemplatesVpnMixin
from .base.template import AbstractTemplate
from .base.vpn import AbstractVpn, AbstractVpnClient


class Config(TemplatesVpnMixin, AbstractConfig):
    """
    Concrete Config model
    """
    class Meta(AbstractConfig.Meta):
        abstract = False


def sortedm2m__str__(self):
    """
    Improves string representation of m2m relationship objects
    """
    return self.template.name


Config.templates.through.__str__ = sortedm2m__str__


class Template(AbstractTemplate):
    """
    Concrete Template model
    """
    class Meta(AbstractTemplate.Meta):
        abstract = False


class VpnClient(AbstractVpnClient):
    """
    Concrete VpnClient model
    """
    class Meta(AbstractVpnClient.Meta):
        abstract = False


class Vpn(AbstractVpn):
    """
    Concrete VPN model
    """
    class Meta(AbstractVpn.Meta):
        abstract = False
