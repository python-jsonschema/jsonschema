==========
jsonschema
==========

|PyPI| |Pythons| |CI| |ReadTheDocs| |Precommit| |Zenodo|

.. |PyPI| image:: https://img.shields.io/pypi/v/jsonschema.svg
   :alt: PyPI version
   :target: https://pypi.org/project/jsonschema/

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/jsonschema.svg
   :alt: Supported Python versions
   :target: https://pypi.org/project/jsonschema/

.. |CI| image:: https://github.com/python-jsonschema/jsonschema/workflows/CI/badge.svg
  :alt: Build status
  :target: https://github.com/python-jsonschema/jsonschema/actions?query=workflow%3ACI

.. |ReadTheDocs| image:: https://readthedocs.org/projects/python-jsonschema/badge/?version=stable&style=flat
   :alt: ReadTheDocs status
   :target: https://python-jsonschema.readthedocs.io/en/stable/

.. |Precommit| image:: https://results.pre-commit.ci/badge/github/python-jsonschema/jsonschema/main.svg
   :alt: pre-commit.ci status
   :target: https://results.pre-commit.ci/latest/github/python-jsonschema/jsonschema/main

.. |Zenodo| image:: https://zenodo.org/badge/3072629.svg
   :alt: Zenodo DOI
   :target: https://zenodo.org/badge/latestdoi/3072629


``jsonschema`` is an implementation of the `JSON Schema <https://json-schema.org>`_ specification for Python.

.. code:: python

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

It can also be used from the command line by installing `check-jsonschema <https://github.com/python-jsonschema/check-jsonschema>`_.

Features
--------

* Full support for `Draft 2020-12 <https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/#jsonschema.validators.Draft202012Validator>`_, `Draft 2019-09 <https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/#jsonschema.validators.Draft201909Validator>`_, `Draft 7 <https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/#jsonschema.validators.Draft7Validator>`_, `Draft 6 <https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/#jsonschema.validators.Draft6Validator>`_, `Draft 4 <https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/#jsonschema.validators.Draft4Validator>`_ and `Draft 3 <https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/#jsonschema.validators.Draft3Validator>`_

* `Lazy validation <https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/protocols/#jsonschema.protocols.Validator.iter_errors>`_ that can iteratively report *all* validation errors.

* `Programmatic querying <https://python-jsonschema.readthedocs.io/en/latest/errors/>`_ of which properties or items failed validation.


Installation
------------

``jsonschema`` is available on `PyPI <https://pypi.org/project/jsonschema/>`_. You can install using `pip <https://pip.pypa.io/en/stable/>`_:

.. code:: bash

    $ pip install jsonschema


Extras
======

Two extras are available when installing the package, both currently related to ``format`` validation:

    * ``format``
    * ``format-nongpl``

They can be used when installing in order to include additional dependencies, e.g.:

.. code:: bash

    $ pip install jsonschema'[format]'

Be aware that the mere presence of these dependencies – or even the specification of ``format`` checks in a schema – do *not* activate format checks (as per the specification).
Please read the `format validation documentation <https://python-jsonschema.readthedocs.io/en/latest/validate/#validating-formats>`_ for further details.

.. start cut from PyPI

Running the Test Suite
----------------------

If you have ``nox`` installed (perhaps via ``pipx install nox`` or your package manager), running ``nox`` in the directory of your source checkout will run ``jsonschema``'s test suite on all of the versions of Python ``jsonschema`` supports.
If you don't have all of the versions that ``jsonschema`` is tested under, you'll likely want to run using ``nox``'s ``--no-error-on-missing-interpreters`` option.

Of course you're also free to just run the tests on a single version with your favorite test runner.
The tests live in the ``jsonschema.tests`` package.


Benchmarks
----------

``jsonschema``'s benchmarks make use of `pyperf <https://pyperf.readthedocs.io>`_.
Running them can be done via::

      $ nox -s perf


Community
---------

The JSON Schema specification has `a Slack <https://json-schema.slack.com>`_, with an `invite link on its home page <https://json-schema.org/>`_.
Many folks knowledgeable on authoring schemas can be found there.

Otherwise, opening a `GitHub discussion <https://github.com/python-jsonschema/jsonschema/discussions>`_ or asking questions on Stack Overflow are other means of getting help if you're stuck.

.. end cut from PyPI


About
-----

I'm Julian Berman.

``jsonschema`` is on `GitHub <https://github.com/python-jsonschema/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute, it'd be most welcome!

You can also generally find me on Libera (nick: ``Julian``) in various channels, including ``#python``.

If you feel overwhelmingly grateful, you can also `sponsor me <https://github.com/sponsors/Julian/>`_.

And for companies who appreciate ``jsonschema`` and its continued support and growth, ``jsonschema`` is also now supportable via `TideLift <https://tidelift.com/subscription/pkg/pypi-jsonschema?utm_source=pypi-jsonschema&utm_medium=referral&utm_campaign=readme>`_.
