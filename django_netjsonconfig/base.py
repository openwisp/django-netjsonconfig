import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from model_utils.fields import AutoCreatedField, AutoLastModifiedField

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin as BaseAdmin
else:  # pragma: nocover
    from django.contrib.admin import ModelAdmin as BaseAdmin


class TimeStampedEditableModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = AutoCreatedField(_('created'), editable=True)
    modified = AutoLastModifiedField(_('modified'), editable=True)

    class Meta:
        abstract = True


class TimeStampedEditableAdmin(BaseAdmin):
    """
    ModelAdmin for TimeStampedEditableModel
    """
    def __init__(self, *args, **kwargs):
        self.readonly_fields += ('created', 'modified',)
        super(TimeStampedEditableAdmin, self).__init__(*args, **kwargs)
