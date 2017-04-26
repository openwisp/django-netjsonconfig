from .base.config import AbstractConfig, TemplatesVpnMixin, sortedm2m__str__
from .base.tag import AbstractTaggedTemplate, AbstractTemplateTag
from .base.template import AbstractTemplate
from .base.vpn import AbstractVpn, AbstractVpnClient


class Config(TemplatesVpnMixin, AbstractConfig):
    """
    Concrete Config model
    """
    class Meta(AbstractConfig.Meta):
        abstract = False


Config.templates.through.__str__ = sortedm2m__str__


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
