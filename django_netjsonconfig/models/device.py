import json
import collections

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.module_loading import import_string
from django.utils.functional import cached_property

from jsonfield import JSONField
from sortedm2m.fields import SortedManyToManyField
from netjsonconfig.exceptions import ValidationError as SchemaError

from ..base import TimeStampedEditableModel
from ..settings import BACKENDS


@python_2_unicode_compatible
class AbstractConfig(TimeStampedEditableModel):
    """
    Abstract model shared between BaseDevice and BaseTemplate
    """
    name = models.CharField(max_length=63)
    backend = models.CharField(_('backend'),
                               choices=BACKENDS,
                               max_length=128,
                               help_text=_('Select netjsonconfig backend'))
    config = JSONField(_('configuration'),
                       default=dict,
                       help_text=_('configuration in NetJSON DeviceConfiguration format'),
                       load_kwargs={'object_pairs_hook': collections.OrderedDict},
                       dump_kwargs={'indent': 4})

    def clean(self):
        """
        performs netjsonconfig backend validation
        """
        b = self.backend_instance
        # this is needed to avoid having OrderedDict
        # in an eventual ValidationError message
        # which would make the error hard to read
        b.config = json.loads(json.dumps(b.config))
        try:
            b.validate()
        except SchemaError as e:
            path = [str(el) for el in e.details.path]
            trigger = '/'.join(path)
            error = e.details.message
            message = 'Invalid configuration triggered by "#/{0}"; '\
                      'validator says: {1}'.format(trigger, error)
            raise ValidationError(message)

    @cached_property
    def backend_class(self):
        return import_string(self.backend)

    @cached_property
    def backend_instance(self):
        return self.get_backend_instance()

    def get_backend_instance(self, config=None, template_instances=None):
        """
        allows overriding config and templates
        needed for pre validation of m2m
        """
        backend = self.backend_class
        kwargs = {'config': config or self.config}
        # determine if we can pass templates
        # expecting a many2many relationship
        if hasattr(self, 'templates'):
            if template_instances is None:
                template_instances = self.templates.all()
            kwargs['templates'] = [t.config for t in template_instances]
        return backend(**kwargs)

    def json(self, dict=False, **kwargs):
        config = self.backend_instance.config
        if dict:
            return config
        return json.dumps(config, **kwargs)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class BaseDevice(AbstractConfig):
    """
    Abstract model implementing the
    NetJSON DeviceConfiguration object
    """
    class Meta:
        abstract = True


class TemplatesMixin(models.Model):
    """
    Provides a mixins that adds a m2m relationship
    with the concrete Template model
    """
    templates = SortedManyToManyField('netjsonconfig.Template',
                                      verbose_name=_('templates'),
                                      blank=True,
                                      help_text=_('configuration templates, applied from'
                                                  'first to last'))

    class Meta:
        abstract = True


class Device(BaseDevice, TemplatesMixin):
    """
    Concrete Device model
    """
    pass
