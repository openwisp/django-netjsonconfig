import collections
import hashlib
import json
import uuid
from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from netjsonconfig.exceptions import ValidationError as SchemaError

from .. import settings as app_settings


@python_2_unicode_compatible
class AbstractConfig(models.Model):
    """
    Base logic shared between BaseConfig and BaseVpn
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    backend = models.CharField(_('backend'),
                               choices=app_settings.BACKENDS,
                               max_length=128,
                               help_text=_('Select netjsonconfig backend'))
    config = JSONField(_('configuration'),
                       default=dict,
                       help_text=_('configuration in NetJSON DeviceConfiguration format'),
                       load_kwargs={'object_pairs_hook': collections.OrderedDict},
                       dump_kwargs={'indent': 4})
    created = AutoCreatedField(_('created'), editable=True)
    modified = AutoLastModifiedField(_('modified'), editable=True)

    __template__ = False
    __vpn__ = False

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def clean(self):
        """
        * ensures config is not ``None``
        * performs netjsonconfig backend validation
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

    def get_config(self):
        """
        config preprocessing (skipped for templates):
            * inserts hostname automatically if not present in config
        """
        config = self.config or {}  # might be ``None`` in some corner cases
        if self.__template__:
            return config
        c = deepcopy(config)
        is_config = not any([self.__template__, self.__vpn__])
        if 'hostname' not in c.get('general', {}) and is_config:
            c.setdefault('general', {})
            c['general']['hostname'] = self.name.replace(':', '-')
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
        """
        returns netjsonconfig backend class
        """
        return import_string(self.backend)

    @cached_property
    def backend_instance(self):
        """
        returns netjsonconfig backend instance
        """
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
        """
        shortcut for self.backend_instance.generate()
        """
        return self.backend_instance.generate()

    @property
    def checksum(self):
        """
        returns checksum of configuration
        """
        config = self.generate().getvalue()
        return hashlib.md5(config).hexdigest()

    def json(self, dict=False, **kwargs):
        """
        returns JSON representation of object
        """
        config = self.backend_instance.config
        if dict:
            return config
        return json.dumps(config, **kwargs)
