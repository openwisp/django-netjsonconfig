from django.db import models
from django.utils.translation import gettext_lazy as _

from openwisp_utils.base import TimeStampedEditableModel


class AbstractTemplateSubscription(TimeStampedEditableModel):
    """
    Abstract model implementing a model
    to handle notifications of template
    subscription
    """

    template = models.ForeignKey('django_netjsonconfig.Template',
                                 verbose_name=_('Template'),
                                 on_delete=models.CASCADE,
                                 )
    subscriber = models.URLField(_('Subscriber domain'),
                                 max_length=200)
    subscribe = models.BooleanField(_('Is Subscriber ?'),
                                    default=True,)

    class Meta(TimeStampedEditableModel.Meta):
        abstract = True

    def __str__(self):
        return self.subscriber
