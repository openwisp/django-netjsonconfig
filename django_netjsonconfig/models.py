from celery.decorators import periodic_task
from celery.schedules import crontab
from django_x509.models import Ca, Cert

from .base.config import AbstractConfig, TemplatesVpnMixin
from .base.device import AbstractDevice
from .base.subscription import AbstractTemplateSubscription
from .base.tag import AbstractTaggedTemplate, AbstractTemplateTag
from .base.template import AbstractTemplate
from .base.vpn import AbstractVpn, AbstractVpnClient
from .tasks import base_sync_template_content


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
        if self.sharing == 'import':
            data = self._get_remote_template_data()
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


@periodic_task(run_every=crontab(minute='0', hour='0'))
def sync_template_content():
    template_subscribers = TemplateSubscription.objects.filter(subscribe=True)
    for subscription in template_subscribers:
        base_sync_template_content(subscription.subscriber, subscription.template.pk)
