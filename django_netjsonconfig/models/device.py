import json
import hashlib
import collections

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.module_loading import import_string
from django.utils.functional import cached_property
from django.utils.crypto import get_random_string

from jsonfield import JSONField
from sortedm2m.fields import SortedManyToManyField
from netjsonconfig.exceptions import ValidationError as SchemaError

from ..base import TimeStampedEditableModel
from ..settings import BACKENDS
from ..validators import key_validator


def get_random_key():
    return get_random_string(length=32)


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
        self.validate_netjsonconfig_backend(self.backend_instance)

    @classmethod
    def validate_netjsonconfig_backend(self, backend):
        """
        this is needed to avoid having OrderedDict
        in an eventual ValidationError message
        which would make the error hard to read
        """
        backend.config = json.loads(json.dumps(backend.config))
        try:
            backend.validate()
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

    def generate(self):
        """ shortcut for self.backend_instance.generate() """
        return self.backend_instance.generate()

    @property
    def checksum(self):
        """ returns checksum of configuration """
        config = self.generate().getvalue()
        return hashlib.md5(config).hexdigest()

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
    key = models.CharField(max_length=64,
                           unique=True,
                           db_index=True,
                           default=get_random_key,
                           validators=[key_validator],
                           help_text=_('unique key that can be used to '
                                       'download the configuration'))

    class Meta:
        abstract = True


class TemplatesMixin(models.Model):
    """
    Provides a mixins that adds a m2m relationship
    with the concrete Template model
    """
    templates = SortedManyToManyField('django_netjsonconfig.Template',
                                      verbose_name=_('templates'),
                                      blank=True,
                                      help_text=_('configuration templates, applied from'
                                                  'first to last'))

    @classmethod
    def clean_templates(cls, action, instance, pk_set, **kwargs):
        """
        validates resulting configuration of device + templates
        raises a ValidationError if invalid
        must be called from forms or APIs
        """
        if action != 'pre_add':
            return
        # coming from signal
        if isinstance(pk_set, set):
            template_model = cls.templates.rel.model
            templates = template_model.objects.filter(pk__in=list(pk_set))
        # coming from admin ModelForm
        else:
            templates = pk_set
        backend = instance.get_backend_instance(template_instances=templates)
        try:
            cls.validate_netjsonconfig_backend(backend)
        except ValidationError as e:
            message = 'There is a conflict with the specified templates. {0}'
            message = message.format(e.message)
            raise ValidationError(message)

    class Meta:
        abstract = True


class Device(BaseDevice, TemplatesMixin):
    """
    Concrete Device model
    """
    pass
