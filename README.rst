==========
jsonschema
==========

|PyPI| |Pythons| |CI| |ReadTheDocs|

.. |PyPI| image:: https://img.shields.io/pypi/v/jsonschema.svg
   :alt: PyPI version
   :target: https://pypi.org/project/jsonschema/

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/jsonschema.svg
   :alt: Supported Python versions
   :target: https://pypi.org/project/jsonschema/

.. |CI| image:: https://github.com/Julian/jsonschema/workflows/CI/badge.svg
  :alt: Build status
  :target: https://github.com/Julian/jsonschema/actions?query=workflow%3ACI

.. |ReadTheDocs| image:: https://readthedocs.org/projects/python-jsonschema/badge/?version=stable&style=flat
   :alt: ReadTheDocs status
   :target: https://python-jsonschema.readthedocs.io/en/stable/


``jsonschema`` is an implementation of `JSON Schema
<https://json-schema.org>`_ for Python.

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

* `Programmatic querying <https://python-jsonschema.readthedocs.io/en/latest/errors/>`_
  of which properties or items failed validation.


Installation
------------

``jsonschema`` is available on `PyPI <https://pypi.org/project/jsonschema/>`_. You can install using `pip <https://pip.pypa.io/en/stable/>`_:

.. code-block:: bash

    $ pip install jsonschema


Release Notes
-------------

v3.1 brings support for ECMA 262 dialect regular expressions
throughout schemas, as recommended by the specification. Big
thanks to @Zac-HD for authoring support in a new `js-regex
<https://pypi.org/project/js-regex/>`_ library.


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

``jsonschema``'s benchmarks make use of `pyperf
<https://pyperf.readthedocs.io>`_. Running them can be done via::

      $ tox -e perf


Community
---------

The JSON Schema specification has `a Slack
<https://json-schema.slack.com>`_, with an `invite link on its home page
<https://json-schema.org/>`_. Many folks knowledgeable on authoring
schemas can be found there.

Otherwise, asking questions on Stack Overflow is another means of
getting help if you're stuck.

Contributing
------------

I'm Julian Berman.

``jsonschema`` is on `GitHub <https://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.

If you feel overwhelmingly grateful, you can also woo me with beer money
via Google Pay with the email in my GitHub profile.

And for companies who appreciate ``jsonschema`` and its continued support
and growth, ``jsonschema`` is also now supportable via `TideLift
<https://tidelift.com/subscription/pkg/pypi-jsonschema?utm_source=pypi-j
sonschema&utm_medium=referral&utm_campaign=readme>`_.
