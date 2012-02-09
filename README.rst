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
    * ``format``, though the schema does not mandate it anyhow. Note however
      that by default, ``jsonschema`` is strict about unknown properties, so
      using ``format`` without passing ``unknown_property="skip"`` to a
      validator will raise a ``SchemaError`` until it is properly supported.

* Validation that reports *all* errors, rather than short-circuiting on the
  first validation error (off by default)::

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

* Small, extensibile, strict! and has as clean of an API as is feasible

Note: the API is still considered *unstable*, though no major changes are
expected.


Schema Versioning
-----------------

JSON Schema is, at the time of this writing, seemingly at draft 03, with
preparations for draft 04 underway. The current plan is likely to have
the validators in this module take a ``version`` argument, which will allow
support for future versions. Whether draft 03 will remain the default version
used or not is undecided, so to be safe, *explicitly* declare which version of
the schema you will be validating with.


A Quick Word on uniqueItems
---------------------------

Validating schemas with the ``uniqueItems`` property can leave you open to
algorithmic complexity attacks. This may change in the future. For now,
``jsonschema`` will warn you if you use ``uniqueitems`` without using the
`Securetypes <http://github.com/ludios/Securetypes>`_ module, but will proceed
anyhow if it couldn't be imported.


TODO
----

* Optimize ``extends`` to prevent doing double work
* Implement some time of prioritizing, to allow quick validation checks to run
  first


Contributing and Contact Info
-----------------------------

I'm Julian Berman :).

You can generally find me on Freenode (nick: ``tos9``) in various channels,
including ``#python``.

Get in touch here or there if you've got something to contribute, it'd be most
welcome!
