Changelog
=========

Version 0.4.2 [2016-12-29]
--------------------------

- `#22 <https://github.com/openwisp/django-netjsonconfig/issues/22>`_: Fixed evaluation of multiple vars

Version 0.4.1 [2016-09-22]
--------------------------

- [vpn] Use "not equal" operator instead of "is not" in CA validation
- [openvpn] Corrected wrong "client" mode value to "p2p"
- [vpn] Updated custom OpenVpn schema (netjsonconfig 0.5.1)
- [general] require at least netjsonconfig 0.5.1

Version 0.4.0 [2016-09-20]
--------------------------

- [general] upgraded minimum django version to 1.10
- [general] upgraded minimum netjsonconfig version to 0.5.0
- [general] added VPN Server management (depends on django-x509)
- [general] added ``auto_cert`` feature for automatic management of VPN client certificates
- [template] added ``type`` attribute to ``Template`` model, which can be ``generic`` or ``vpn``
- [config] added required unique ``mac_address`` field to ``Config`` model
- [settings] added ``NETJSONCONFIG_VPN_BACKENDS`` setting
- [settings] added ``NETJSONCONFIG_DEFAULT_VPN_BACKEND`` setting
- [settings] added ``NETJSONCONFIG_DEFAULT_AUTO_CERT`` setting
- [settings] added ``NETJSONCONFIG_CERT_PATH`` setting
- [settings] added ``NETJSONCONFIG_COMMON_NAME_FORMAT`` setting
- [settings] backends are now completely overridable
- [admin] configuration editor is now initialized empty
- [admin] configuration editor buttons order swapped: advanced mode is now on the right side
  while "object properties" has been renamed to "configuration menu" and moved to the left side
- [admin] log failed previews for debugging purposes

Version 0.3.3 [2016-08-24]
--------------------------

- `#24 <https://github.com/openwisp/django-netjsonconfig/issues/24>`_: updated outdated dependencies
- `9cd6348 <https://github.com/openwisp/django-netjsonconfig/commit/9cd6348>`_: added a more human readable app verbose name
- `93ddb9f <https://github.com/openwisp/django-netjsonconfig/commit/93ddb9f>`_: removed incorrect ``verbose_name_plural`` from ``AppConfig``
- `4fd23a1 <https://github.com/openwisp/django-netjsonconfig/commit/4fd23a1>`_: updated requirements to be less strict

Version 0.3.2 [2016-06-21]
--------------------------

- `ddb6a13 <https://github.com/openwisp/django-netjsonconfig/commit/ddb6a13>`_: [config] replace ':' with '-' in hostname when generating configuration
- `6f22de8 <https://github.com/openwisp/django-netjsonconfig/commit/6f22de8>`_: added consistent registration feature

Version 0.3.1 [2016-04-19]
--------------------------

- `b4ca30a <https://github.com/openwisp/django-netjsonconfig/commit/b4ca30a>`_: [pypi] added openwisp tag to pypi release
- `d7c3aea <https://github.com/openwisp/django-netjsonconfig/commit/d7c3aea>`_: [pypi] eliminated accidentally included test database from pypi release

Version 0.3.0 [2016-04-15]
--------------------------

- `0948999 <https://github.com/openwisp/django-netjsonconfig/commit/0948999>`_: [admin] ensured ``default_templates`` variable is included only in ``Config`` admin
- `#13 <https://github.com/openwisp/django-netjsonconfig/issues/13>`_: [admin] added json-schema editor UI in ``Config`` admin
- `6044ac3 <https://github.com/openwisp/django-netjsonconfig/commit/6044ac3>`_: [admin] improved look of disabled inputs & selects
- `4b4c6a1 <https://github.com/openwisp/django-netjsonconfig/commit/4b4c6a1>`_: fixed requirements.txt (had to be ``<`` instead of ``<=``)
- `#22 <https://github.com/openwisp/django-netjsonconfig/issues/22>`_: updated django-sortedm2m dependency
- `751e24e <https://github.com/openwisp/django-netjsonconfig/commit/751e24e>`_: [admin] preview: wait when keyboard shortcut is used
- `739c9bc <https://github.com/openwisp/django-netjsonconfig/commit/739c9bc>`_: updated minimum netjsonconfig version to 0.4.2 in requirements.txt

Version 0.2.5 [2016-03-08]
--------------------------

- `04c8c78 <https://github.com/openwisp/django-netjsonconfig/commit/04c8c78>`_:
  [controller] log ``last_ip`` during registration
- `80806d7 <https://github.com/openwisp/django-netjsonconfig/commit/80806d7>`_:
  [controller] log forbidden requests with ``warning`` level
- `dba328c <https://github.com/openwisp/django-netjsonconfig/commit/dba328c>`_:
  [controller] refactored ``utils.forbid_unallowed`` in order to log request details

Version 0.2.4 [2016-02-22]
--------------------------

- `75f5c38 <https://github.com/openwisp/django-netjsonconfig/commit/75f5c38>`_:
  [admin] swapped order of key and id attribtues in config form
- `#18 <https://github.com/openwisp/django-netjsonconfig/issues/18>`_:
  added support for **"configuration variables"** and ``NETJSONCONFIG_CONTEXT`` setting
- `c66f74f <https://github.com/openwisp/django-netjsonconfig/commit/c66f74f>`_:
  [admin] fixed possible import error case when adding new ``Config``
- `1f7c4e7 <https://github.com/openwisp/django-netjsonconfig/commit/1f7c4e7>`_:
  [admin] fixed wrong template validation error in add ``Config``
- `#19 <https://github.com/openwisp/django-netjsonconfig/issues/19>`_:
  added **"default templates"** feature
- `902a65d <https://github.com/openwisp/django-netjsonconfig/commit/902a65d>`_:
  added ``NETJSONCONFIG_DEFAULT_BACKEND`` setting
- `dc628e1 <https://github.com/openwisp/django-netjsonconfig/commit/dc628e1>`_:
  [admin] ensured unsaved change warnings are issued only in add/change
- updated `netjsonconfig <https://github.com/openwisp/netjsonconfig>`_ minimum version to 0.3.7

Version 0.2.3 [2016-02-12]
--------------------------

- `d7700a9 <https://github.com/openwisp/django-netjsonconfig/commit/d7700a9>`_:
  added (forgotten) migration for commit `e96e26 <https://github.com/openwisp/django-netjsonconfig/commit/e96e26>`_
- `#15 <https://github.com/openwisp/django-netjsonconfig/issues/15>`_:
  [model] ``config`` field cannot be ``None``
- `#17 <https://github.com/openwisp/django-netjsonconfig/issues/17>`_:
  [controller] update ``last_ip`` during checksum

Version 0.2.2 [2016-02-05]
--------------------------

- `e96e262 <https://github.com/openwisp/django-netjsonconfig/commit/e96e262>`_:
  allow ``blank=True`` in ``BaseConfig`` (but not Templates)
- `#10 <https://github.com/openwisp/django-netjsonconfig/issues/10>`_:
  [admin] added configuration preview
- `#12 <https://github.com/openwisp/django-netjsonconfig/issues/12>`_:
  [admin] added unsaved changes warning
- `#11 <https://github.com/openwisp/django-netjsonconfig/issues/11>`_:
  [admin] moved preview in ``submit_row``
- `#14 <https://github.com/openwisp/django-netjsonconfig/issues/14>`_:
  [admin] added "visualize" and "download" links for templates

Version 0.2.1 [2016-01-22]
--------------------------

- `#9 <https://github.com/openwisp/django-netjsonconfig/issues/9>`_ added "visualize" and "download" links for templates
- `#7 <https://github.com/openwisp/django-netjsonconfig/issues/7>`_ added ``report-status`` mechanism
- `4905bbb <https://github.com/openwisp/django-netjsonconfig/commit/4905bbb>`_ [config] auto detect hostname unless overridden
- `#8 <https://github.com/openwisp/django-netjsonconfig/issues/8>`_ added ``last_ip`` field
- `#11 <https://github.com/openwisp/django-netjsonconfig/issues/11>`_ added revision history via django-reversion

Version 0.2.0 [2016-01-14]
--------------------------

- `#2 <https://github.com/openwisp/django-netjsonconfig/issues/2>`_ simplified override of ``Device`` admin ``change_form.html`` template
- `#3 <https://github.com/openwisp/django-netjsonconfig/issues/3>`_ added simple http controller
- `#5 <https://github.com/openwisp/django-netjsonconfig/issues/5>`_ fixed ``ImportError`` during ``Device`` validation
- `#4 <https://github.com/openwisp/django-netjsonconfig/issues/4>`_ renamed ``Device`` to ``Config``
- `#6 <https://github.com/openwisp/django-netjsonconfig/issues/6>`_ added more structure to HTTP responses of controller

Version 0.1.2 [2015-12-21]
--------------------------

- fixed files in pypi build

Version 0.1.1 [2015-12-18]
--------------------------

- `99244a0 <https://github.com/openwisp/django-netjsonconfig/commit/99244a0>`_ added ``key`` field to Device
- `46c1582 <https://github.com/openwisp/django-netjsonconfig/commit/46c1582>`_ added ``key_validator`` to validate ``key`` field
- `3016a2e <https://github.com/openwisp/django-netjsonconfig/commit/3016a2e>`_ admin: improved style of config textarea
- `ec1544a <https://github.com/openwisp/django-netjsonconfig/commit/ec1544a>`_ admin: improved overall usability
- `#1 <https://github.com/openwisp/django-netjsonconfig/issues/1>`_ fixed admin ``clean_templates`` for new devices

Version 0.1 [2015-12-11]
------------------------

* manage devices
* manage templates
* multiple template inheritance with django-sortedm2m
* download configurations
* visualize configuration
