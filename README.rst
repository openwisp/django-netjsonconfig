django-netjsonconfig
====================

.. image:: https://travis-ci.org/openwisp/django-netjsonconfig.svg
   :target: https://travis-ci.org/openwisp/django-netjsonconfig

.. image:: https://coveralls.io/repos/openwisp/django-netjsonconfig/badge.svg
  :target: https://coveralls.io/r/openwisp/django-netjsonconfig

.. image:: https://requires.io/github/openwisp/django-netjsonconfig/requirements.svg?branch=master
   :target: https://requires.io/github/openwisp/django-netjsonconfig/requirements/?branch=master
   :alt: Requirements Status

.. image:: https://badge.fury.io/py/django-netjsonconfig.svg
   :target: http://badge.fury.io/py/django-netjsonconfig

------------

Configuration manager for embedded devices, implemented as a reusable django-app.

Based on the `NetJSON`_ format and the `netjsonconfig`_ library.

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/adhoc-interface.png
   :alt: adhoc interface

------------

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/preview.png
   :alt: preview

------------

.. contents:: **Table of Contents**:
   :backlinks: none
   :depth: 3

------------

Current features
----------------

* **configuration management** for embedded devices supporting different firmwares:
    - `OpenWRT <http://openwrt.org>`_
    - `OpenWISP Firmware <https://github.com/openwisp/OpenWISP-Firmware>`_
    - support for additional firmware can be added by `specifying custom backends <#netjsonconfig-backends>`_
* **configuration editor** based on `JSON-Schema editor <https://github.com/jdorn/json-editor>`_
* **advanced edit mode**: edit `NetJSON`_ *DeviceConfiguration* objects for maximum flexibility
* **configuration templates**: reduce repetition to the minimum
* **configuration context**: reference ansible-like variables in the configuration
* **template tags**: tag templates to automate different types of auto-configurations (eg: mesh, WDS, 4G)
* **simple HTTP resources**: allow devices to automatically download configuration updates
* **VPN management**: easily create VPN servers and clients

Project goals
-------------

* automate configuration management for embedded devices
* allow to minimize repetition by using templates
* provide base logic that can be extended by third-party apps (see
  `Extending django-netjsonconfig <#extending-django-netjsonconfig>`_)
* provide ways to support more firmwares by adding custom backends
* keep the core as simple as possible

Deploy it in production
-----------------------

An automated installer is available at `ansible-openwisp2 <https://github.com/openwisp/ansible-openwisp2>`_.

Dependencies
------------

* Python 2.7 or Python >= 3.5
* OpenSSL

Install stable version from pypi
--------------------------------

Install from pypi:

.. code-block:: shell

    pip install django-netjsonconfig

Install development version
---------------------------

Install tarball:

.. code-block:: shell

    pip install https://github.com/openwisp/django-netjsonconfig/tarball/master

Alternatively you can install via pip using git:

.. code-block:: shell

    pip install -e git+git://github.com/openwisp/django-netjsonconfig#egg=django-netjsonconfig

If you want to contribute, install your cloned fork:

.. code-block:: shell

    git clone git@github.com:<your_fork>/django-netjsonconfig.git
    cd django-netjsonconfig
    python setup.py develop

Setup (integrate in an existing django project)
-----------------------------------------------

Add ``django_netjsonconfig``, ``django.contrib.admin``, ``sortedm2m`` and ``reversion`` to
``INSTALLED_APPS`` in the following order:

.. code-block:: python

    INSTALLED_APPS = [
        # other apps
        'openwisp_utils.admin_theme',
        'django_netjsonconfig',
        # ensure the django admin comes after django-netjsonconfig
        'django.contrib.admin',
        'sortedm2m',
        'reversion'  # optional, can be removed if not needed
        # ...
    ]

Add the controller URLs to your main ``urls.py``:

.. code-block:: python

    urlpatterns = [
        # ... other urls in your project ...

        # controller URLs
        # used by devices to download/update their configuration
        # keep the namespace argument unchanged
        url(r'^', include('django_netjsonconfig.controller.urls', namespace='controller')),
        # common URLs
        # shared among django-netjsonconfig components
        # keep the namespace argument unchanged
        url(r'^', include('django_netjsonconfig.urls', namespace='netjsonconfig')),
    ]

Then run:

.. code-block:: shell

    ./manage.py migrate

Installing for development
--------------------------

Install sqlite:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev openssl libssl-dev

Install your forked repo:

.. code-block:: shell

    git clone git://github.com/<your_fork>/django-netjsonconfig
    cd django-netjsonconfig/
    python setup.py develop

Install test requirements:

.. code-block:: shell

    pip install -r requirements-test.txt

Create database:

.. code-block:: shell

    cd tests/
    ./manage.py migrate
    ./manage.py createsuperuser

Launch development server:

.. code-block:: shell

    ./manage.py runserver

You can access the admin interface at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    ./runtests.py

Settings
--------

``NETJSONCONFIG_BACKENDS``
~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+-----------------------------------------------+
| **type**:    | ``tuple``                                     |
+--------------+-----------------------------------------------+
| **default**: | .. code-block:: python                        |
|              |                                               |
|              |   (                                           |
|              |     ('netjsonconfig.OpenWrt', 'OpenWRT'),     |
|              |     ('netjsonconfig.OpenWisp', 'OpenWISP'),   |
|              |   )                                           |
+--------------+-----------------------------------------------+

Available configuration backends. For more information, see `netjsonconfig backends
<http://netjsonconfig.openwisp.org/en/latest/general/basics.html#backend>`_.

``NETJSONCONFIG_VPN_BACKENDS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+----------------------------------------------------------------+
| **type**:    | ``tuple``                                                      |
+--------------+----------------------------------------------------------------+
| **default**: | .. code-block:: python                                         |
|              |                                                                |
|              |   (                                                            |
|              |     ('django_netjsonconfig.vpn_backends.OpenVpn', 'OpenVPN'),  |
|              |   )                                                            |
+--------------+----------------------------------------------------------------+

Available VPN backends for VPN Server objects. For more information, see `OpenVPN netjsonconfig backend
<http://netjsonconfig.openwisp.org/en/latest/backends/openvpn.html>`_.

A VPN backend must follow some basic rules in order to be compatible with *django-netjsonconfig*:

* it MUST allow at minimum and at maximum one VPN instance
* the main *NetJSON* property MUST match the lowercase version of the class name,
  eg: when using the ``OpenVpn`` backend, the system will look into
  ``config['openvpn']``
* it SHOULD focus on the server capabilities of the VPN software being used

``NETJSONCONFIG_DEFAULT_BACKEND``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+----------------------------------+
| **type**:    | ``str``                          |
+--------------+----------------------------------+
| **default**: | ``NETJSONCONFIG_BACKENDS[0][0]`` |
+--------------+----------------------------------+

The preferred backend that will be used as initial value when adding new ``Config`` or
``Template`` objects in the admin.

This setting defaults to the raw value of the first item in the ``NETJSONCONFIG_BACKENDS`` setting,
which is ``netjsonconfig.OpenWrt``.

Setting it to ``None`` will force the user to choose explicitly.

``NETJSONCONFIG_DEFAULT_VPN_BACKEND``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+--------------------------------------+
| **type**:    | ``str``                              |
+--------------+--------------------------------------+
| **default**: | ``NETJSONCONFIG_VPN_BACKENDS[0][0]`` |
+--------------+--------------------------------------+

The preferred backend that will be used as initial value when adding new ``Vpn`` objects in the admin.

This setting defaults to the raw value of the first item in the ``NETJSONCONFIG_VPN_BACKENDS`` setting,
which is ``django_netjsonconfig.vpn_backends.OpenVpn``.

Setting it to ``None`` will force the user to choose explicitly.

``NETJSONCONFIG_REGISTRATION_ENABLED``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+-------------+
| **type**:    | ``bool``    |
+--------------+-------------+
| **default**: | ``True``    |
+--------------+-------------+

Whether devices can automatically register through the controller or not.

This feature is enabled by default.

Autoregistration must be supported on the devices in order to work, see `openwisp-config automatic
registration <https://github.com/openwisp/openwisp-config#automatic-registration>`_ for more information.

``NETJSONCONFIG_CONSISTENT_REGISTRATION``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+-------------+
| **type**:    | ``bool``    |
+--------------+-------------+
| **default**: | ``True``    |
+--------------+-------------+

Whether devices that are already registered are recognized when reflashed or reset, hence keeping
the existing configuration without creating a new one.

This feature is enabled by default.

Autoregistration must be enabled also on the devices in order to work, see `openwisp-config
consistent key generation <https://github.com/openwisp/openwisp-config#consistent-key-generation>`_
for more information.

``NETJSONCONFIG_SHARED_SECRET``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``str``          |
+--------------+------------------+
| **default**: | ``""``           |
+--------------+------------------+

A secret key which must be used by devices to perform `automatic registration
<https://github.com/openwisp/openwisp-config#automatic-registration>`_.

This key MUST be explicitly set in production (if ``settings.DEBUG is False``), otherwise
an ``ImproperlyConfigured`` exception will be raised on startup.

``NETJSONCONFIG_CONTEXT``
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``dict``         |
+--------------+------------------+
| **default**: | ``{}``           |
+--------------+------------------+

Additional context that is passed to the default context of each ``Config`` object.

Each ``Config`` object gets the following attributes passed as configuration variables:

* ``id``
* ``key``
* ``name``
* ``mac_address``

``NETJSONCONFIG_CONTEXT`` can be used to define system-wide configuration variables.

For more information, see `netjsonconfig context: configuration variables
<http://netjsonconfig.openwisp.org/en/latest/general/basics.html#context-configuration-variables>`_.

``NETJSONCONFIG_DEFAULT_AUTO_CERT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+---------------------------+
| **type**:    | ``bool``                  |
+--------------+---------------------------+
| **default**: | ``True``                  |
+--------------+---------------------------+

The default value of the ``auto_cert`` field for new ``Template`` objects.

The ``auto_cert`` field is valid only for templates which have ``type``
set to ``VPN`` and indicates whether a new x509 certificate should be created
automatically for each configuration using that template.

The automatically created certificates will also be removed when they are not
needed anymore (eg: when the VPN template is removed from a configuration object).

``NETJSONCONFIG_CERT_PATH``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+---------------------------+
| **type**:    | ``str``                   |
+--------------+---------------------------+
| **default**: | ``/etc/x509``             |
+--------------+---------------------------+

The filesystem path where x509 certificate will be installed when
downloaded on routers when ``auto_cert`` is being used (enabled by default).

``NETJSONCONFIG_COMMON_NAME_FORMAT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------------------+
| **type**:    | ``str``                      |
+--------------+------------------------------+
| **default**: | ``{mac_address}-{name}``     |
+--------------+------------------------------+

Defines the format of the ``common_name`` attribute of VPN client certificates that are automatically
created when using VPN templates which have ``auto_cert`` set to ``True``.

``NETJSONCONFIG_MANAGEMENT_IP_DEVICE_LIST``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------------------+
| **type**:    | ``bool``                     |
+--------------+------------------------------+
| **default**: | ``True``                     |
+--------------+------------------------------+

In the device list page, the column ``IP`` will show the ``management_ip`` if
available, defaulting to ``last_ip`` otherwise.

If this setting is set to ``False`` the ``management_ip`` won't be shown
in the device list page even if present, it will be shown only in the device
detail page.

You may set this to ``False`` if for some reason the majority of your user
doesn't care about the management ip address.

``NETJSONCONFIG_BACKEND_DEVICE_LIST``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------------------+
| **type**:    | ``bool``                     |
+--------------+------------------------------+
| **default**: | ``True``                     |
+--------------+------------------------------+

In the device list page, the column ``backend`` and the backend filter are
shown by default.

If this setting is set to ``False`` these items will be removed from the UI.

You may set this to ``False`` if you are using only one configuration backend
and having this UI element doesn't add any value to your users.

``NETJSONCONFIG_HARDWARE_ID_ENABLED``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+-------------+
| **type**:    | ``bool``    |
+--------------+-------------+
| **default**: | ``False``   |
+--------------+-------------+

The field ``hardware_id`` can be used to store a unique hardware id, for example a serial number.

If this setting is set to ``True`` then this field will be shown first in the device list page
and in the add/edit device page.

This feature is disabled by default.

``NETJSONCONFIG_HARDWARE_ID_OPTIONS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+--------------------------------------------------------+
| **type**:    | ``dict``                                               |
+--------------+--------------------------------------------------------+
| **default**: | .. code-block:: python                                 |
|              |                                                        |
|              |    {                                                   |
|              |        'blank': not NETJSONCONFIG_HARDWARE_ID_ENABLED, |
|              |        'null': True,                                   |
|              |        'max_length': 32,                               |
|              |        'unique': True,                                 |
|              |        'verbose_name': _('Serial number'),             |
|              |        'help_text': _('Serial number of this device')  |
|              |    }                                                   |
+--------------+--------------------------------------------------------+

Options for the model field ``hardware_id``.

* ``blank``: wether the field is allowed to be blank
* ``null``: wether an empty value will be stored as ``NULL`` in the database
* ``max_length``: maximum length of the field
* ``unique``: wether the value of the field must be unique
* ``verbose_name``: text for the human readable label of the field
* ``help_text``: help text to be displayed with the field

Extending django-netjsonconfig
------------------------------

*django-netjsonconfig* provides a set of models, admin classes and generic views which can be imported,
extended and reused by third party apps.

To extend *django-netjsonconfig*, **you MUST NOT** add it to ``settings.INSTALLED_APPS``,
but you must create your own app (which goes into ``settings.INSTALLED_APPS``), import the
base classes from django-netjsonconfig and add your customizations.

In order to help django find the static files and templates of *django-netjsonconfig*,
you need to perform the steps described below.

1. Add ``EXTENDED_APPS``
~~~~~~~~~~~~~~~~~~~~~~~~

Add the following to your ``settings.py``:

.. code-block:: python

    EXTENDED_APPS = ('django_netjsonconfig', 'django_x509',)

2. Add ``openwisp_utils.staticfiles.DependencyFinder``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``openwisp_utils.staticfiles.DependencyFinder`` to
``STATICFILES_FINDERS`` in your ``settings.py``:

.. code-block:: python

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'openwisp_utils.staticfiles.DependencyFinder',
    ]

3. Add ``openwisp_utils.loaders.DependencyLoader``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``openwisp_utils.loaders.DependencyLoader`` to ``TEMPLATES`` in your ``settings.py``:

.. code-block:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'OPTIONS': {
                'loaders': [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                    'openwisp_utils.loaders.DependencyLoader',
                ],
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }
    ]

Extending models
~~~~~~~~~~~~~~~~

This example provides an example of how to extend the base models of
*django-netjsonconfig* by adding a relation to another django model named `Organization`.

.. code-block:: python

    # models.py of your custom ``config`` app
    from django.db import models
    from sortedm2m.fields import SortedManyToManyField
    from taggit.managers import TaggableManager

    from django_netjsonconfig.base.config import AbstractConfig, TemplatesVpnMixin
    from django_netjsonconfig.base.tag import AbstractTaggedTemplate, AbstractTemplateTag
    from django_netjsonconfig.base.template import AbstractTemplate
    from django_netjsonconfig.base.vpn import AbstractVpn, AbstractVpnClient

    # the model ``organizations.Organization`` is omitted for brevity
    # if you are curious to see a real implementation, check out django-organizations
    # https://github.com/bennylope/django-organizations

    class OrganizationMixin(models.Model):
        organization = models.ForeignKey('organizations.Organization')

        class Meta:
            abstract = True


    class Config(OrganizationMixin, TemplatesVpnMixin, AbstractConfig):
        templates = SortedManyToManyField('config.Template',
                                          related_name='config_relations',
                                          blank=True)
        vpn = models.ManyToManyField('config.Vpn',
                                     through='config.VpnClient',
                                     related_name='vpn_relations',
                                     blank=True)

        def clean(self):
            # your own validation logic here...
            pass

        class Meta(AbstractConfig.Meta):
            abstract = False


    class TemplateTag(AbstractTemplateTag):
        class Meta(AbstractTemplateTag.Meta):
            abstract = False


    class TaggedTemplate(AbstractTaggedTemplate):
        tag = models.ForeignKey('config.TemplateTag',
                                related_name='%(app_label)s_%(class)s_items',
                                on_delete=models.CASCADE)

        class Meta(AbstractTaggedTemplate.Meta):
            abstract = False


    class Template(OrganizationMixin, AbstractTemplate):
        tags = TaggableManager(through='config.TaggedTemplate', blank=True)
        vpn = models.ForeignKey('config.Vpn', blank=True, null=True)

        def clean(self):
            # your own validation logic here...
            pass

        class Meta(AbstractTemplate.Meta):
            abstract = False


    class Vpn(OrganizationMixin, AbstractVpn):
        class Meta(AbstractVpn.Meta):
            abstract = False


    class VpnClient(AbstractVpnClient):
        config = models.ForeignKey('config.Config', on_delete=models.CASCADE)
        vpn = models.ForeignKey('config.Vpn', on_delete=models.CASCADE)
        cert = models.OneToOneField('django_x509.Cert',
                                    on_delete=models.CASCADE,
                                    blank=True,
                                    null=True)

        class Meta(AbstractVpnClient.Meta):
            abstract = False

Extending the admin
~~~~~~~~~~~~~~~~~~~

Following the previous ``Organization`` example, you can avoid duplicating the admin
code by importing the base admin classes and registering your models with.

.. code-block:: python

    # admin.py of your app
    # these are your custom models, they must be imported before the abstract admin classes
    from .models import Config, Template, Vpn

    from django.contrib import admin
    from django_netjsonconfig.base.admin import (AbstractConfigAdmin,
                                                 AbstractConfigForm,
                                                 AbstractTemplateAdmin,
                                                 AbstractVpnAdmin,
                                                 AbstractVpnForm,
                                                 BaseForm)


    class ConfigForm(AbstractConfigForm):
        class Meta(AbstractConfigForm.Meta):
            model = Config


    class ConfigAdmin(AbstractConfigAdmin):
        form = ConfigForm


    class TemplateForm(BaseForm):
        class Meta(BaseForm.Meta):
            model = Template


    class TemplateAdmin(AbstractTemplateAdmin):
        form = TemplateForm


    class VpnForm(AbstractVpnForm):
        class Meta(AbstractVpnForm.Meta):
            model = Vpn


    class VpnAdmin(AbstractVpnAdmin):
        form = VpnForm


    admin.site.register(Config, ConfigAdmin)
    admin.site.register(Template, TemplateAdmin)
    admin.site.register(Vpn, VpnAdmin)

Extending controller views
~~~~~~~~~~~~~~~~~~~~~~~~~~

If your use case doesn't vary a lot from the base one, you may also want
to try to reuse the controller views:

.. code-block:: python

    # your_config_app.controller.views
    from ..models import Config  # this is your custom model
    from django_netjsonconfig.controller.generics import (
        BaseChecksumView,
        BaseDownloadConfigView,
        BaseRegisterView,
        BaseReportStatusView
    )


    class ChecksumView(BaseChecksumView):
        model = Device


    class DownloadConfigView(BaseDownloadConfigView):
        model = Device


    class ReportStatusView(BaseReportStatusView):
        model = Device


    class RegisterView(BaseRegisterView):
        model = Device


    checksum = ChecksumView.as_view()
    download_config = DownloadConfigView.as_view()
    report_status = ReportStatusView.as_view()
    register = RegisterView.as_view()

Controller URLs
~~~~~~~~~~~~~~~

If you are not making drastic changes to the controller views, you can avoid duplicating the URL
logic by using the ``get_controller_urls`` function. Put this in your controller ``urls.py``:

.. code-block:: python

    # your_config_app.controller.urls
    from django_netjsonconfig.utils import get_controller_urls
    from . import views

    urlpatterns = get_controller_urls(views)

Extending AppConfig
~~~~~~~~~~~~~~~~~~~

You may want to reuse the ``AppConfig`` class of *django-netjsonconfig* too:

.. code-block:: python

    from django_netjsonconfig.apps import DjangoNetjsonconfigApp


    class MyOwnConfig(DjangoNetjsonconfigApp):
        name = 'yourapp.config'
        label = 'config'

        def __setmodels__(self):
            from .models import Config, VpnClient  # these are your custom models
            self.config_model = Config
            self.vpnclient_model = VpnClient

Real world extensions of django-netjsonconfig
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For full working examples of django proejcts which extend *django-netjsonconfig*, see:

- `openwisp/openwisp-controller <https://github.com/openwisp/openwisp-controller>`_
- `innovationgarage/extendnetjson_project <https://github.com/innovationgarage/extendnetjson_project>`_

Screenshots
-----------

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/configuration-ui.png
   :alt: configuration item

------------

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/bridge.png
   :alt: bridge

------------

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/radio.png
   :alt: radio

------------

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/wpa-enterprise.png
  :alt: wpa enterprise

------------

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/preview.png
  :alt: preview

------------

.. image:: https://raw.githubusercontent.com/openwisp/django-netjsonconfig/master/docs/images/adhoc-interface.png
   :alt: adhoc interface

Contributing
------------

1. Announce your intentions in the `OpenWISP Mailing List <https://groups.google.com/d/forum/openwisp>`_
2. Fork this repo and install it
3. Follow `PEP8, Style Guide for Python Code`_
4. Write code
5. Write tests for your code
6. Ensure all tests pass
7. Ensure test coverage does not decrease
8. Document your changes
9. Send pull request

.. _PEP8, Style Guide for Python Code: http://www.python.org/dev/peps/pep-0008/
.. _NetJSON: http://netjson.org
.. _netjsonconfig: http://netjsonconfig.openwisp.org

Changelog
---------

See `CHANGES <https://github.com/openwisp/django-netjsonconfig/blob/master/CHANGES.rst>`_.

License
-------

See `LICENSE <https://github.com/openwisp/django-netjsonconfig/blob/master/LICENSE>`_.

Support
-------

See `OpenWISP Support Channels <http://openwisp.org/support.html>`_.
