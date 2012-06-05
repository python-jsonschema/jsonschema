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

* Validation that reports *all* errors, rather than short-circuiting on the
  first validation error (toggleable, off by default)::

    >>> from jsonschema import ValidationError, validate
    >>> schema = {
    ...     "type" : "array",
    ...     "items" : {"enum" : [1, 2, 3]},
    ...     "maxItems" : 2,
    ... }
    >>> try:
    ...     validate([2, 3, 4], schema, stop_on_error=False)
    ... except ValidationError as e:
    ...     print("Validation failed with errors:")
    ...     for error in sorted(e.errors):
    ...         print("    * " + error)
    Validation failed with errors:
        * 4 is not one of [1, 2, 3]
        * [2, 3, 4] is too long

* Small and extensible


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

* Default for unknown types and properties is now to *not* error (consistent
  with the schema).
* Python 3 support
* Removed dependency on SecureTypes now that the hash bug has been resolved.
* "Numerous bug fixes" -- most notably, a divisibleBy error for floats and a
  bunch of missing typechecks for irrelevant properties.


Contributing
------------

I'm Julian Berman.

``jsonschema`` is on `GitHub <http://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.
