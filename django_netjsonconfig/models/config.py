import collections
import hashlib
import json
from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from model_utils import Choices
from model_utils.fields import StatusField
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
    Abstract model shared between BaseConfig and BaseTemplate
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

    __template__ = False

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def clean(self):
        """
        * ensures config is not ``None``
        * performs netjsonconfig backend validation
        * tries to render the configuration and catches any exception
        """
        if self.config is None:
            self.config = {}
        # perform validation only if backend is defined, otherwise
        # django will take care of notifying blank field error
        if not self.backend:
            return
        try:
            backend = self.backend_instance
        except ImportError as e:
            message = 'Error while importing "{0}": {1}'.format(self.backend, e)
            raise ValidationError({'backend': message})
        else:
            self.clean_netjsonconfig_backend(backend)
        try:
            backend.render()
        except Exception as e:
            # possible exceptions catched:
            #   * ``jinja2.exceptions.SecurityError``
            message = '{0}: {1}'.format(e.__class__.__name__, e)
            raise ValidationError({'config': message})

    def get_config(self):
        """
        config preprocessing (skipped for templates):
            * inserts hostname automatically if not present in config
        """
        config = self.config or {}  # might be ``None`` in some corner cases
        if self.__template__:
            return config
        c = deepcopy(config)
        c.setdefault('general', {})
        if 'hostname' not in c['general']:
            c['general']['hostname'] = self.name
        return c

    @classmethod
    def validate_netjsonconfig_backend(self, backend):
        """
        calls ``validate`` method of netjsonconfig backend
        might trigger SchemaError
        """
        # the following line is a trick needed to avoid cluttering
        # an eventual ``ValidationError`` message with ``OrderedDict``
        # which would make the error message hard to read
        backend.config = json.loads(json.dumps(backend.config))
        backend.validate()

    @classmethod
    def clean_netjsonconfig_backend(self, backend):
        """
        catches any ``SchemaError`` which will be redirected
        to ``django.core.exceptions.ValdiationError``
        """
        try:
            self.validate_netjsonconfig_backend(backend)
        except SchemaError as e:
            path = [str(el) for el in e.details.path]
            trigger = '/'.join(path)
            error = e.details.message
            message = 'Invalid configuration triggered by "#/{0}", '\
                      'validator says:\n\n{1}'.format(trigger, error)
            raise ValidationError(message)

    @cached_property
    def backend_class(self):
        return import_string(self.backend)

    @cached_property
    def backend_instance(self):
        return self.get_backend_instance()

    def get_backend_instance(self, template_instances=None):
        """
        allows overriding config and templates
        needed for pre validation of m2m
        """
        backend = self.backend_class
        kwargs = {'config': self.get_config()}
        # determine if we can pass templates
        # expecting a many2many relationship
        if hasattr(self, 'templates'):
            if template_instances is None:
                template_instances = self.templates.all()
            kwargs['templates'] = [t.config for t in template_instances]
        # pass context to backend if get_context method is defined
        if hasattr(self, 'get_context'):
            kwargs['context'] = self.get_context()
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


class BaseConfig(AbstractConfig):
    """
    Abstract model implementing the
    NetJSON DeviceConfiguration object
    """
    STATUS = Choices('modified', 'running', 'error')
    status = StatusField(help_text=_(
        'modified means the configuration is not applied yet; '
        'running means applied and running; '
        'error means the configuration caused issues and it was rolledback'
    ))
    key = models.CharField(max_length=64,
                           unique=True,
                           db_index=True,
                           default=get_random_key,
                           validators=[key_validator],
                           help_text=_('unique key that can be used to '
                                       'download the configuration'))
    last_ip = models.GenericIPAddressField(blank=True,
                                           null=True,
                                           help_text=_('indicates the last ip from which the '
                                                       'configuration was downloaded from '
                                                       '(except downloads from this page)'))

    def clean(self):
        """
        modifies status if key attributes of the configuration
        have changed (queries the database)
        """
        super(BaseConfig, self).clean()
        if self._state.adding:
            return
        current = self.__class__.objects.get(pk=self.pk)
        for attr in ['name', 'backend', 'config']:
            if getattr(self, attr) != getattr(current, attr):
                self.status = 'modified'
                break

    def get_context(self):
        """
        additional context passed to netjsonconfig
        """
        return {
            'id': str(self.id),
            'key': self.key,
            'name': self.name
        }

    class Meta:
        abstract = True

BaseConfig._meta.get_field('config').blank = True


class TemplatesMixin(models.Model):
    """
    Provides a mixins that adds a m2m relationship
    with the concrete Template model
    """
    templates = SortedManyToManyField('django_netjsonconfig.Template',
                                      related_name='config_relations',
                                      verbose_name=_('templates'),
                                      blank=True,
                                      help_text=_('configuration templates, applied from'
                                                  'first to last'))

    @classmethod
    def clean_templates(cls, action, instance, pk_set, **kwargs):
        """
        validates resulting configuration of config + templates
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
            cls.clean_netjsonconfig_backend(backend)
        except ValidationError as e:
            message = 'There is a conflict with the specified templates. {0}'
            message = message.format(e.message)
            raise ValidationError(message)

    @classmethod
    def templates_changed(cls, action, instance, **kwargs):
        """
        called from m2m_changed signal
        """
        if action not in ['post_add', 'post_remove', 'post_clear']:
            return
        if instance.status != 'modified':
            instance.status = 'modified'
            instance.save()

    class Meta:
        abstract = True


class Config(BaseConfig, TemplatesMixin):
    """
    Concrete Config model
    """
    class Meta:
        verbose_name = _('configuration')
        verbose_name_plural = _('configurations')
