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

``v1.3.0`` adds better, more verbose tracebacks for validation errors that give
some actual possibility of seeing what went wrong, particularly for the new 
``anyOf``, ``oneOf`` and ``allOf`` validators in draft 4.

The other notable change is that ``ErrorTree``\s now raise exceptions for keys
that aren't in the instance, to prevent typos.

``__cause__`` is also implemented on Py3 for format errors, if that floats your
boat.


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


Community
---------

There's a `mailing list <https://groups.google.com/forum/#!forum/jsonschema>`_ for this implementation on Google Groups.

Please join, and feel free to send questions there.

Contributing
------------

I'm Julian Berman.

``jsonschema`` is on `GitHub <http://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.
