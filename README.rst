==========
jsonschema
==========

``jsonschema`` is an implementation of JSON Schema (currently in `Draft 3
<http://tools.ietf.org/html/draft-zyp-json-schema-03>`_) for Python.

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

    >>> validate({"name" : "Eggs", "price" : "Invalid"}, schema)
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
    ...     print "Validation failed with errors:"
    ...     for error in sorted(e.errors):
    ...         print "    * " + error
    Validation failed with errors:
        * 4 is not one of [1, 2, 3]
        * [2, 3, 4] is too long

* Small and extensible

Note: the API is still considered *unstable*, though no major changes are
expected.


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


A Quick Word on uniqueItems
---------------------------

Validating schemas with the ``uniqueItems`` property can leave you open to
algorithmic complexity attacks. This may change in the future. For now,
``jsonschema`` will warn you if you use ``uniqueItems`` without using the
`Securetypes <http://github.com/ludios/Securetypes>`_ module, but will proceed
anyhow if it couldn't be imported.

You can also keep tabs on `http://bugs.python.org/issue13703`_.


Contributing and Contact Info
-----------------------------

I'm Julian Berman.

``jsonschema`` is on `Github <http://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.
