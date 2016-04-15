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

.. image:: https://img.shields.io/pypi/dm/django-netjsonconfig.svg
   :target: https://pypi.python.org/pypi/django-netjsonconfig

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
* **simple HTTP resources**: allow devices to automatically download configuration updates

Project goals
-------------

* automate configuration management for embedded devices
* allow to minimize repetition by using templates
* make it easy to integrate in larger django projects to improve reusability
* make it easy to extend its models by providing abstract models
* provide ways to support more firmwares by adding custom backends
* keep the core as simple as possible
* provide ways to extend the default behaviour
* encourage new features to be published as extensions

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

Add ``django_netjsonconfig``, ``sortedm2m`` and ``reversion`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        # other apps
        'django_netjsonconfig',
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

Deploy it in production
-----------------------

If you need to deploy *django-netjsonconfig* by itself (that is without including it in a larger project),
you may want to check out the `ansible-openwisp2 <https://github.com/nemesisdesign/ansible-openwisp2>`_ role.

Installing for development
--------------------------

Install sqlite:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev

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

+--------------+-------------+
| **type**:    | ``list``    |
+--------------+-------------+
| **default**: | ``[]``      |
+--------------+-------------+

Additional custom `netjsonconfig backends <http://netjsonconfig.openwisp.org/en/latest/general/basics.html#backend>`_.

``NETJSONCONFIG_REGISTRATION_ENABLED``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+-------------+
| **type**:    | ``bool``    |
+--------------+-------------+
| **default**: | ``True``    |
+--------------+-------------+

Whether devices can automatically register through the controller or not.

This feature is enabled by default.

``NETJSONCONFIG_SHARED_SECRET``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``str``          |
+--------------+------------------+
| **default**: | ``""``           |
+--------------+------------------+

A secret key which must be used by devices to perform automatic registration.

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

``NETJSONCONFIG_CONTEXT`` can be used to define system-wide configuration variables.

For more information, see `netjsonconfig context: configuration variables
<http://netjsonconfig.openwisp.org/en/latest/general/basics.html#context-configuration-variables>`_.

``NETJSONCONFIG_DEFAULT_BACKEND``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+---------------------------+
| **type**:    | ``str``                   |
+--------------+---------------------------+
| **default**: | ``netjsonconfig.OpenWrt`` |
+--------------+---------------------------+

The preferred backend that will be used as initial value when adding new ``Config`` or
``Template`` objects in the admin.

Set it to ``None`` in order to force the user to choose explicitly.

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
