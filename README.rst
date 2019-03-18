==========
jsonschema
==========

|PyPI| |Pythons| |Travis| |AppVeyor| |ReadTheDocs|

.. |PyPI| image:: https://img.shields.io/pypi/v/jsonschema.svg
   :alt: PyPI version
   :target: https://pypi.org/project/jsonschema/

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/jsonschema.svg
   :alt: Supported Python versions
   :target: https://pypi.org/project/jsonschema/

.. |Travis| image:: https://travis-ci.org/Julian/jsonschema.svg?branch=master
   :alt: Travis build status
   :target: https://travis-ci.org/Julian/jsonschema

.. |AppVeyor| image:: https://ci.appveyor.com/api/projects/status/adtt0aiaihy6muyn?svg=true
   :alt: AppVeyor build status
   :target: https://ci.appveyor.com/project/Julian/jsonschema
   
.. |ReadTheDocs| image:: https://readthedocs.org/projects/python-jsonschema/badge/?version=latest&style=flat
   :alt: ReadTheDocs status
   :target: https://python-jsonschema.readthedocs.io/en/stable/


``jsonschema`` is an implementation of `JSON Schema <https://json-schema.org>`_
for Python (supporting 2.7+ including Python 3).

.. code-block:: python

    >>> from jsonschema import validate

    >>> # A sample schema, like what we'd get from json.load()
    >>> schema = {
    ...     "type" : "object",
    ...     "properties" : {
    ...         "price" : {"type" : "number"},
    ...         "name" : {"type" : "string"},
    ...     },
    ... }

    >>> # If no exception is raised by validate(), the instance is valid.
    >>> validate(instance={"name" : "Eggs", "price" : 34.99}, schema=schema)

    >>> validate(
    ...     instance={"name" : "Eggs", "price" : "Invalid"}, schema=schema,
    ... )                                   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: 'Invalid' is not of type 'number'

It can also be used from console:

.. code-block:: bash

    $ jsonschema -i sample.json sample.schema

Features
--------

* Full support for
  `Draft 7 <https://python-jsonschema.readthedocs.io/en/latest/validate/#jsonschema.Draft7Validator>`_,
  `Draft 6 <https://python-jsonschema.readthedocs.io/en/latest/validate/#jsonschema.Draft6Validator>`_,
  `Draft 4 <https://python-jsonschema.readthedocs.io/en/latest/validate/#jsonschema.Draft4Validator>`_
  and
  `Draft 3 <https://python-jsonschema.readthedocs.io/en/latest/validate/#jsonschema.Draft3Validator>`_

* `Lazy validation <https://python-jsonschema.readthedocs.io/en/latest/validate/#jsonschema.IValidator.iter_errors>`_
  that can iteratively report *all* validation errors.

* `Programmatic querying <https://python-jsonschema.readthedocs.io/en/latest/errors/#module-jsonschema>`_
  of which properties or items failed validation.


Installation
------------

``jsonschema`` is available on `PyPI <https://pypi.org/project/jsonschema/>`_. You can install using `pip <https://pip.pypa.io/en/stable/>`_:

.. code-block:: bash

    $ pip install jsonschema


Release Notes
-------------

Version 3.0 brings support for Draft 7 (and 6). The interface for redefining
types has also been majorly overhauled to support easier redefinition of the
types a Validator will accept or allow.

jsonschema is also now tested under Windows via AppVeyor.

Thanks to all who contributed pull requests along the way.


Running the Test Suite
----------------------

If you have ``tox`` installed (perhaps via ``pip install tox`` or your
package manager), running ``tox`` in the directory of your source
checkout will run ``jsonschema``'s test suite on all of the versions
of Python ``jsonschema`` supports. If you don't have all of the
versions that ``jsonschema`` is tested under, you'll likely want to run
using ``tox``'s ``--skip-missing-interpreters`` option.

Of course you're also free to just run the tests on a single version with your
favorite test runner. The tests live in the ``jsonschema.tests`` package.


Benchmarks
----------

``jsonschema``'s benchmarks make use of `perf <https://perf.readthedocs.io>`_.

Running them can be done via ``tox -e perf``, or by invoking the ``perf``
commands externally (after ensuring that both it and ``jsonschema`` itself are
installed)::

    $ python -m perf jsonschema/benchmarks/test_suite.py --hist --output results.json

To compare to a previous run, use::

    $ python -m perf compare_to --table reference.json results.json

See the ``perf`` documentation for more details.


Community
---------

There's a `mailing list <https://groups.google.com/forum/#!forum/jsonschema>`_
for this implementation on Google Groups.

Please join, and feel free to send questions there.


Contributing
------------

I'm Julian Berman.

``jsonschema`` is on `GitHub <https://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.

If you feel overwhelmingly grateful, you can woo me with beer money via
Google Pay with the email in my GitHub profile.
