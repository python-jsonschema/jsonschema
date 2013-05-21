v1.4.0
------

* Added ``create`` and ``extend`` to ``jsonschema.validators``
* Fixed array indices ref resolution (#95)
* Fixed unknown scheme defragmenting and handling (#102)


v1.3.0
------

* Better error tracebacks (#83)
* Raise exceptions in ``ErrorTree``\s for keys not in the instance (#92)
* __cause__ (#93)


v1.2.0
------

* More attributes for ValidationError (#86)
* Added ``ValidatorMixin.descend``
* Fixed bad ``RefResolutionError`` message (#82)


v1.1.0
------

* Canonicalize URIs (#70)
* Allow attaching exceptions to ``format`` errors (#77)


v1.0.0
------

* Support for Draft 4
* Support for format
* Longs are ints too!
* Fixed a number of issues with ``$ref`` support (#66)
* Draft4Validator is now the default
* ``ValidationError.path`` is now in sequential order
* Added ``ValidatorMixin``


v0.8.0
------

* Full support for JSON References
* ``validates`` for registering new validators
* Documentation
* Bugfixes

    * uniqueItems not so unique (#34)
    * Improper any (#47)


v0.7
----

* Partial support for (JSON Pointer) ``$ref``
* Deprecations

  * ``Validator`` is replaced by ``Draft3Validator`` with a slightly different
    interface
  * ``validator(meta_validate=False)``


v0.6
----

* Bugfixes

  * Issue #30 - Wrong behavior for the dependencies property validation
  * Fix a miswritten test


v0.5
----

* Bugfixes

  * Issue #17 - require path for error objects
  * Issue #18 - multiple type validation for non-objects


v0.4
----

* Preliminary support for programmatic access to error details (Issue #5).
  There are certainly some corner cases that don't do the right thing yet, but
  this works mostly.

    In order to make this happen (and also to clean things up a bit), a number
    of deprecations are necessary:

        * ``stop_on_error`` is deprecated in ``Validator.__init__``. Use 
          ``Validator.iter_errors()`` instead.
        * ``number_types`` and ``string_types`` are deprecated there as well.
          Use ``types={"number" : ..., "string" : ...}`` instead.
        * ``meta_validate`` is also deprecated, and instead is now accepted as
          an argument to ``validate``, ``iter_errors`` and ``is_valid``.

* A bugfix or two


v0.3
----

* Default for unknown types and properties is now to *not* error (consistent
  with the schema).
* Python 3 support
* Removed dependency on SecureTypes now that the hash bug has been resolved.
* "Numerous bug fixes" -- most notably, a divisibleBy error for floats and a
  bunch of missing typechecks for irrelevant properties.
