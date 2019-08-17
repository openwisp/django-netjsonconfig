import logging

import requests
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openwisp_utils.base import TimeStampedEditableModel

from ..tasks import subscribe_template

logger = logging.getLogger(__name__)


class AbstractTemplateSubscription(TimeStampedEditableModel):
    """
    Abstract model implementing a model
    to handle notifications of template
    subscription
    """
    template = models.ForeignKey('django_netjsonconfig.Template',
                                 verbose_name=_('Template'),
                                 on_delete=models.CASCADE)
    subscriber = models.URLField(_('Subscriber URL'),
                                 max_length=200)
    is_subscription = models.BooleanField(_('Is Subscriber ?'),
                                          default=True,)

    class Meta(TimeStampedEditableModel.Meta):
        abstract = True

    @classmethod
    def subscribe(cls, request, template):
        cls._subscription(request, template, is_subscription=True)

    @classmethod
    def unsubscribe(cls, request, template):
        cls._subscription(request, template)

    @classmethod
    def _subscription(cls, request, template, is_subscription=False):
        subscriber_url = '{0}://{1}'.format(request.scheme, request.get_host())
        subscribe_template.delay(template.id, template.url, subscriber_url, is_subscription)

    @classmethod
    def subscription_count(cls, template):
        return cls.objects.filter(is_subscription=True, template=template).count()

    @classmethod
    def synchronize_templates(cls):
        template_subscribers = cls.objects.filter(is_subscription=True)
        for subscription in template_subscribers:
            path = '{0}{1}'.format(subscription.subscriber, reverse('api:synchronize_template'))
            try:
                requests.post(path, data={'template': subscription.template.pk})
            except Exception as e:
                logger.exception(
                    'Got exception {} while sending '
                    'updates to {}, for template with name {}'.format(
                        type(e), subscription.subscriber, subscription.template.name
                    )
                )
