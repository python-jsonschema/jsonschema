==========
jsonschema
==========

``jsonschema`` is an implementation of JSON Schema (currently in `Draft 3
<http://tools.ietf.org/html/draft-zyp-json-schema-03>`_) for Python (supporting
2.6+ including Python 3).

::

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

    * ``$ref``, and ``extends`` that use ``$ref``\s

* Lazy validation that can iteratively report *all* validation errors.

::

    >>> from jsonschema import Validator
    >>> schema = {
    ...     "type" : "array",
    ...     "items" : {"enum" : [1, 2, 3]},
    ...     "maxItems" : 2,
    ... }
    >>> v = Validator()
    >>> for error in sorted(v.iter_errors([2, 3, 4], schema), key=str):
    ...     print(error)
    4 is not one of [1, 2, 3]
    [2, 3, 4] is too long

* Small and extensible

* Programmatic querying of which properties or items failed validation.

::

    >>> from jsonschema import ErrorTree, Validator
    >>> schema = {
    ...     "type" : "array",
    ...     "items" : {"type" : "number", "enum" : [1, 2, 3]},
    ...     "minItems" : 3,
    ... }
    >>> instance = ["spam", 2]
    >>> v = Validator()
    >>> tree = ErrorTree(v.iter_errors(instance, schema))

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
preparations for Draft 4 underway. The ``Validator`` class and ``validate``
function take a ``version`` argument that you can use to specify what version
of the Schema you are validating under.

As of right now, Draft 3 (``jsonschema.DRAFT_3``) is the only supported
version, and the default when validating. Whether it will remain the default
version in the future when it is superceeded is undecided, so if you want to be
safe, *explicitly* declare which version to use when validating.


Release Notes
-------------

v0.5 is mostly just a bugfix release to fix a lingering bug for error objects'
``reqired`` properties (Issue #17) and for multiple types' validation for
non-objects (Issue #18).

All of the deprecated parameters from v0.4 have also been removed in this
release.

Contributing
------------

I'm Julian Berman.

``jsonschema`` is on `GitHub <http://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.
