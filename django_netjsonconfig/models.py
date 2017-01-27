from .base.config import AbstractConfig, TemplatesVpnMixin
from .base.template import AbstractTemplate
from .base.vpn import AbstractVpn, AbstractVpnClient


class Config(TemplatesVpnMixin, AbstractConfig):
    """
    Concrete Config model
    """


class Template(AbstractTemplate):
    """
    Concrete Template model
    """


class VpnClient(AbstractVpnClient):
    """
    Concrete VpnClient model
    """


class Vpn(AbstractVpn):
    """
    Concrete VPN model
    """
