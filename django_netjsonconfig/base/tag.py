import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from taggit.models import GenericUUIDTaggedItemBase, TagBase, TaggedItemBase


class AbstractTemplateTag(TagBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')


class AbstractTaggedTemplate(GenericUUIDTaggedItemBase, TaggedItemBase):
    tag = models.ForeignKey('django_netjsonconfig.TemplateTag',
                            related_name='%(app_label)s_%(class)s_items',
                            on_delete=models.CASCADE)

    class Meta:
        abstract = True
        verbose_name = _('Tagged item')
        verbose_name_plural = _('Tags')
