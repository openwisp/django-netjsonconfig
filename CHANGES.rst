Changelog
=========

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
