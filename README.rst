==========
jsonschema
==========

``jsonschema`` is an implementation of `JSON Schema <http://json-schema.org>`_
for Python (supporting 2.6+ including Python 3).

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
    >>> validate({"name" : "Eggs", "price" : 34.99}, schema)

    >>> validate(
    ...     {"name" : "Eggs", "price" : "Invalid"}, schema
    ... )                                   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: 'Invalid' is not of type 'number'


Features
--------

* Full support for
  `Draft 3 <https://python-jsonschema.readthedocs.org/en/latest/validate.html#jsonschema.Draft3Validator>`_
  **and** `Draft 4 <https://python-jsonschema.readthedocs.org/en/latest/validate.html#jsonschema.Draft4Validator>`_
  of the schema.

* `Lazy validation <https://python-jsonschema.readthedocs.org/en/latest/validate.html#jsonschema.IValidator.iter_errors>`_
  that can iteratively report *all* validation errors.

* Small and extensible

* `Programmatic querying <https://python-jsonschema.readthedocs.org/en/latest/errors.html#module-jsonschema>`_
  of which properties or items failed validation.


Release Notes
-------------

``v1.0.0`` is a new major release of ``jsonschema``.

It includes two major new features: `support for the newly released draft 4 <https://python-jsonschema.readthedocs.org/en/latest/validate.html#jsonschema.Draft4Validator>`_
of the specification (thanks to Chase Sterling) and
`optional support for format
<https://python-jsonschema.readthedocs.org/en/latest/validate.html#validating-formats>`_
(thanks to Norman Hooper).

It also contains two major backwards incompatible changes: draft 4 is now the
default for schemas without ``$schema`` specified, and ``ValidationError``\s
now have ``path`` in sequential order.

It also fixes a minor issue with ``long``\s not being recognized as
``integer``\s and a number of issues with the support for ``$ref``.

Also, ``ValidatorMixin`` can be used to construct concrete validators for users
who wish to create their own from scratch.

As always, see `the documentation <http://python-jsonschema.readthedocs.org>`_
for details.

``v1.1.0`` fixes a bug whereby URIs were not canonicalized when stored and
looked up (#70) and also allows for registering exceptions that can be accessed
from ``ValidationError``\s when validating ``format`` properties (#77).


Running the Test Suite
----------------------

``jsonschema`` uses the wonderful `Tox <http://tox.readthedocs.org>`_ for its
test suite. (It really is wonderful, if for some reason you haven't heard of
it, you really should use it for your projects).

Assuming you have ``tox`` installed (perhaps via ``pip install tox`` or your
package manager), just run ``tox`` in the directory of your source checkout to
run ``jsonschema``'s test suite on all of the versions of Python ``jsonschema``
supports. Note that you'll need to have all of those versions installed in
order to run the tests on each of them, otherwise ``tox`` will skip (and fail)
the tests on that version.


Contributing
------------

I'm Julian Berman.

``jsonschema`` is on `GitHub <http://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.
