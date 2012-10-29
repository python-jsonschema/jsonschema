==========
jsonschema
==========

``jsonschema`` is an implementation of JSON Schema (currently in `Draft 3
<http://tools.ietf.org/html/draft-zyp-json-schema-03>`_) for Python (supporting
2.6+ including Python 3).

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
    >>> validate({"name" : "Eggs", "price" : 34.99}, schema)

    >>> validate(
    ...     {"name" : "Eggs", "price" : "Invalid"}, schema
    ... )                                   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: 'Invalid' is not of type 'number'


Features
--------

* Support for Draft 3 of the Schema with the exception of

    * Non-JSON Pointer ``$ref``, and ``extends`` that use them

* Lazy validation that can iteratively report *all* validation errors.

.. code:: python

    >>> from jsonschema import Draft3Validator
    >>> schema = {
    ...     "type" : "array",
    ...     "items" : {"enum" : [1, 2, 3]},
    ...     "maxItems" : 2,
    ... }
    >>> v = Draft3Validator(schema)
    >>> for error in sorted(v.iter_errors([2, 3, 4]), key=str):
    ...     print(error)
    4 is not one of [1, 2, 3]
    [2, 3, 4] is too long

* Small and extensible

* Programmatic querying of which properties or items failed validation.

.. code:: python

    >>> from jsonschema import ErrorTree, Draft3Validator
    >>> schema = {
    ...     "type" : "array",
    ...     "items" : {"type" : "number", "enum" : [1, 2, 3]},
    ...     "minItems" : 3,
    ... }
    >>> instance = ["spam", 2]
    >>> v = Draft3Validator(schema)
    >>> tree = ErrorTree(v.iter_errors(instance))

    >>> sorted(tree.errors)
    ['minItems']

    >>> 0 in tree
    True

    >>> 1 in tree
    False

    >>> sorted(tree[0].errors)
    ['enum', 'type']

    >>> print(tree[0].errors["type"].message)
    'spam' is not of type 'number'


Schema Versioning
-----------------

JSON Schema is, at the time of this writing, seemingly at Draft 3, with
preparations for Draft 4 underway. As of right now, Draft 3 is the only
supported version, and the default when validating. Preparations for
implementing some Draft 4 support are in progress.


Release Notes
-------------

``v0.7`` introduces a number of changes.

The most important one is that the ``Validator`` class is now **deprecated**.

In its place is the ``Draft3Validator`` class (soon to be accompanied by others
for other supported versions). This class accepts a schema when *initializing*,
so that the new interface is::

    validator = Draft3Validator(my_schema)
    validator.validate(some_instance)

Also, *no* meta-validation is done. If you want to check if a schema is valid,
use the ``check_schema`` ``classmethod`` (i.e. use
``Draft3Validator.check_schema(a_maybe_valid_schema)``).

The ``validate`` function of course still exists and continues to work as it
did before::

    from jsonschema import validate
    validate(my_instance, my_schema)

There's just one exception: the ``meta_validate`` argument is deprecated,
and meta-validation will now always be done. If you don't want to have it done,
construct a validator directly as above.

One last thing that is present is partial support for ``$ref``, at least for
JSON Pointer refs. Full support should be coming soon.

As always, if you find any bugs, please file a ticket.


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
