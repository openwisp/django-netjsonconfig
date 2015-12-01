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

Django implementation of `NetJSON <http://netjson.org>`__ NetworkGraph.

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

TODO.

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

You can access the visualizer at http://127.0.0.1:8000/
and the admin interface at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    ./runtests.py

Contributing
------------

1. Announce your intentions in the `issue tracker <https://github.com/openwisp/django-netjsonconfig/issues>`__
2. Fork this repo and install it
3. Follow `PEP8, Style Guide for Python Code`_
4. Write code
5. Write tests for your code
6. Ensure all tests pass
7. Ensure test coverage is not under 90%
8. Document your changes
9. Send pull request

.. _PEP8, Style Guide for Python Code: http://www.python.org/dev/peps/pep-0008/
.. _ninux-dev mailing list: http://ml.ninux.org/mailman/listinfo/ninux-dev
