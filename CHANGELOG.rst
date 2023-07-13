v4.18.3
=======

* Properly preserve ``applicable_validators`` in extended validators.
  Specifically, validators extending early drafts where siblings of ``$ref`` were ignored will properly ignore siblings in the extended validator.

v4.18.2
=======

* Fix an additional regression with the deprecated ``jsonschema.RefResolver`` and pointer resolution.

v4.18.1
=======

* Fix a regression with ``jsonschema.RefResolver`` based resolution when used in combination with a custom validation dialect (via ``jsonschema.validators.create``).

v4.18.0
=======

This release majorly rehauls the way in which JSON Schema reference resolution is configured.
It does so in a way that *should* be backwards compatible, preserving old behavior whilst emitting deprecation warnings.

* ``jsonschema.RefResolver`` is now deprecated in favor of the new `referencing library <https://github.com/python-jsonschema/referencing/>`_.
  ``referencing`` will begin in beta, but already is more compliant than the existing ``$ref`` support.
  This change is a culmination of a meaningful chunk of work to make ``$ref`` resolution more flexible and more correct.
  Backwards compatibility *should* be preserved for existing code which uses ``RefResolver``, though doing so is again now deprecated, and all such use cases should be doable using the new APIs.
  Please file issues on the ``referencing`` tracker if there is functionality missing from it, or here on the ``jsonschema`` issue tracker if you have issues with existing code not functioning the same, or with figuring out how to change it to use ``referencing``.
  In particular, this referencing change includes a change concerning *automatic* retrieval of remote references (retrieving ``http://foo/bar`` automatically within a schema).
  This behavior has always been a potential security risk and counter to the recommendations of the JSON Schema specifications; it has survived this long essentially only for backwards compatibility reasons, and now explicitly produces warnings.
  The ``referencing`` library itself will *not* automatically retrieve references if you interact directly with it, so the deprecated behavior is only triggered if you fully rely on the default ``$ref`` resolution behavior and also include remote references in your schema, which will still be retrieved during the deprecation period (after which they will become an error).
* Support for Python 3.7 has been dropped, as it is nearing end-of-life.
  This should not be a "visible" change in the sense that ``requires-python`` has been updated, so users using 3.7 should still receive ``v4.17.3`` when installing the library.
* On draft 2019-09, ``unevaluatedItems`` now properly does *not* consider items to be evaluated by an ``additionalItems`` schema if ``items`` is missing from the schema, as the specification says in this case that ``additionalItems`` must be completely ignored.
* Fix the ``date`` format checker on Python 3.11 (when format assertion behavior is enabled), where it was too liberal (#1076).
* Speed up validation of ``unevaluatedProperties`` (#1075).

Deprecations
------------

* ``jsonschema.RefResolver`` -- see above for details on the replacement
* ``jsonschema.RefResolutionError`` -- see above for details on the replacement
* relying on automatic resolution of remote references -- see above for details on the replacement
* importing ``jsonschema.ErrorTree`` -- instead import it via ``jsonschema.exceptions.ErrorTree``
* importing ``jsonschema.FormatError`` -- instead import it via ``jsonschema.exceptions.FormatError``

v4.17.3
=======

* Fix instantiating validators with cached refs to boolean schemas
  rather than objects (#1018).

v4.17.2
=======

* Empty strings are not valid relative JSON Pointers (aren't valid under the
  RJP format).
* Durations without (trailing) units are not valid durations (aren't
  valid under the duration format). This involves changing the dependency
  used for validating durations (from ``isoduration`` to ``isodate``).

v4.17.1
=======

* The error message when using ``unevaluatedProperties`` with a non-trivial
  schema value (i.e. something other than ``false``) has been improved (#996).

v4.17.0
=======

* The ``check_schema`` method on ``jsonschema.protocols.Validator`` instances
  now *enables* format validation by default when run. This can catch some
  additional invalid schemas (e.g. containing invalid regular expressions)
  where the issue is indeed uncovered by validating against the metaschema
  with format validation enabled as an assertion.
* The ``jsonschema`` CLI (along with ``jsonschema.cli`` the module) are now
  deprecated. Use ``check-jsonschema`` instead, which can be installed via
  ``pip install check-jsonschema`` and found
  `here <https://github.com/python-jsonschema/check-jsonschema>`_.

v4.16.1
=======

* Make ``ErrorTree`` have a more grammatically correct ``repr``.

v4.16.0
=======

* Improve the base URI behavior when resolving a ``$ref`` to a resolution URI
  which is different from the resolved schema's declared ``$id``.
* Accessing ``jsonschema.draftN_format_checker`` is deprecated. Instead, if you
  want access to the format checker itself, it is exposed as
  ``jsonschema.validators.DraftNValidator.FORMAT_CHECKER`` on any
  ``jsonschema.protocols.Validator``.

v4.15.0
=======

* A specific API Reference page is now present in the documentation.
* ``$ref`` on earlier drafts (specifically draft 7 and 6) has been "fixed" to
  follow the specified behavior when present alongside a sibling ``$id``.
  Specifically the ID is now properly ignored, and references are resolved
  against whatever resolution scope was previously relevant.

v4.14.0
=======

* ``FormatChecker.cls_checks`` is deprecated. Use ``FormatChecker.checks`` on
  an instance of ``FormatChecker`` instead.
* ``unevaluatedItems`` has been fixed for draft 2019. It's nonetheless
  discouraged to use draft 2019 for any schemas, new or old.
* Fix a number of minor annotation issues in ``protocols.Validator``

v4.13.0
=======

* Add support for creating validator classes whose metaschema uses a different
  dialect than its schemas. In other words, they may use draft2020-12 to define
  which schemas are valid, but the schemas themselves use draft7 (or a custom
  dialect, etc.) to define which *instances* are valid. Doing this is likely
  not something most users, even metaschema authors, may need, but occasionally
  will be useful for advanced use cases.

v4.12.1
=======

* Fix some stray comments in the README.

v4.12.0
=======

* Warn at runtime when subclassing validator classes. Doing so was not
  intended to be public API, though it seems some downstream libraries
  do so. A future version will make this an error, as it is brittle and
  better served by composing validator objects instead. Feel free to reach
  out if there are any cases where changing existing code seems difficult
  and I can try to provide guidance.

v4.11.0
=======

* Make the rendered README in PyPI simpler and fancier. Thanks Hynek (#983)!

v4.10.3
=======

* ``jsonschema.validators.validator_for`` now properly uses the explicitly
  provided default validator even if the ``$schema`` URI is not found.

v4.10.2
=======

* Fix a second place where subclasses may have added attrs attributes (#982).

v4.10.1
=======

* Fix Validator.evolve (and APIs like ``iter_errors`` which call it) for cases
  where the validator class has been subclassed. Doing so wasn't intended to be
  public API, but given it didn't warn or raise an error it's of course
  understandable. The next release however will make it warn (and a future one
  will make it error). If you need help migrating usage of inheriting from a
  validator class feel free to open a discussion and I'll try to give some
  guidance (#982).

v4.10.0
=======

* Add support for referencing schemas with ``$ref`` across different versions
  of the specification than the referrer's

v4.9.1
======

* Update some documentation examples to use newer validator releases in their
  sample code.

v4.9.0
======

* Fix relative ``$ref`` resolution when the base URI is a URN or other scheme
  (#544).
* ``pkgutil.resolve_name`` is now used to retrieve validators
  provided on the command line. This function is only available on
  3.9+, so 3.7 and 3.8 (which are still supported) now rely on the
  `pkgutil_resolve_name <https://pypi.org/project/pkgutil_resolve_name/>`_
  backport package. Note however that the CLI itself is due
  to be deprecated shortly in favor of `check-jsonschema
  <https://github.com/python-jsonschema/check-jsonschema>`_.

v4.8.0
======

* ``best_match`` no longer traverses into ``anyOf`` and ``oneOf`` when all of
  the errors within them seem equally applicable. This should lead to clearer
  error messages in some cases where no branches were matched.

v4.7.2
======

* Also have ``best_match`` handle cases where the ``type`` validator is an
  array.

v4.7.1
======

* Minor tweak of the PyPI hyperlink names

v4.7.0
======

* Enhance ``best_match`` to prefer errors from branches of the schema which
  match the instance's type (#728)

v4.6.2
======

* Fix a number of minor typos in docstrings, mostly private ones (#969)

v4.6.1
======

* Gut the (incomplete) implementation of ``recursiveRef`` on draft 2019. It
  needs completing, but for now can lead to recursion errors (e.g. #847).

v4.6.0
======

* Fix ``unevaluatedProperties`` and ``unevaluatedItems`` for types they should
  ignore (#949)
* ``jsonschema`` now uses `hatch <https://hatch.pypa.io/>`_ for its build
  process. This should be completely transparent to end-users (and only matters
  to contributors).

v4.5.1
======

* Revert changes to ``$dynamicRef`` which caused a performance regression
  in v4.5.0

v4.5.0
======

* Validator classes for each version now maintain references to the correct
  corresponding format checker (#905)
* Development has moved to a `GitHub organization
  <https://github.com/python-jsonschema/>`_.
  No functional behavior changes are expected from the change.

v4.4.0
======

* Add ``mypy`` support (#892)
* Add support for Python 3.11

v4.3.3
======

* Properly report deprecation warnings at the right stack level (#899)

v4.3.2
======

* Additional performance improvements for resolving refs (#896)

v4.3.1
======

* Resolving refs has had performance improvements (#893)

v4.3.0
======

* Fix undesired fallback to brute force container uniqueness check on
  certain input types (#893)
* Implement a PEP544 Protocol for validator classes (#890)

v4.2.1
======

* Pin ``importlib.resources`` from below (#877)

v4.2.0
======

* Use ``importlib.resources`` to load schemas (#873)
* Ensure all elements of arrays are verified for uniqueness by ``uniqueItems``
  (#866)

v4.1.2
======

* Fix ``dependentSchemas`` to properly consider non-object instances to be
  valid (#850)

v4.1.1
======

* Fix ``prefixItems`` not indicating which item was invalid within the instance
  path (#862)

v4.1.0
======

* Add Python 3.10 to the list of supported Python versions

v4.0.1
======

* Fix the declaration of minimum supported Python version (#846)

v4.0.0
======

* Partial support for Draft 2020-12 (as well as 2019-09).
  Thanks to Thomas Schmidt and Harald Nezbeda.
* ``False`` and ``0`` are now properly considered non-equal even
  recursively within a container (#686). As part of this change,
  ``uniqueItems`` validation may be *slower* in some cases. Please feel
  free to report any significant performance regressions, though in
  some cases they may be difficult to address given the specification
  requirement.
* The CLI has been improved, and in particular now supports a ``--output``
  option (with ``plain`` (default) or ``pretty`` arguments) to control the
  output format. Future work may add additional machine-parsable output
  formats.
* Code surrounding ``DEFAULT_TYPES`` and the legacy mechanism for
  specifying types to validators have been removed, as per the deprecation
  policy. Validators should use the ``TypeChecker`` object to customize
  the set of Python types corresponding to JSON Schema types.
* Validation errors now have a ``json_path`` attribute, describing their
  location in JSON path format
* Support for the IP address and domain name formats has been improved
* Support for Python 2 and 3.6 has been dropped, with ``python_requires``
  properly set.
* ``multipleOf`` could overflow when given sufficiently large numbers. Now,
  when an overflow occurs, ``jsonschema`` will fall back to using fraction
  division (#746).
* ``jsonschema.__version__``, ``jsonschema.validators.validators``,
  ``jsonschema.validators.meta_schemas`` and
  ``jsonschema.RefResolver.in_scope`` have been deprecated, as has
  passing a second-argument schema to ``Validator.iter_errors`` and
  ``Validator.is_valid``.

v3.2.0
======

* Added a ``format_nongpl`` setuptools extra, which installs only ``format``
  dependencies that are non-GPL (#619).

v3.1.1
======

* Temporarily revert the switch to ``js-regex`` until #611 and #612 are
  resolved.

v3.1.0
======

* Regular expressions throughout schemas now respect the ECMA 262 dialect, as
  recommended by the specification (#609).

v3.0.2
======

* Fixed a bug where ``0`` and ``False`` were considered equal by
  ``const`` and ``enum`` (#575).

v3.0.1
======

* Fixed a bug where extending validators did not preserve their notion
  of which validator property contains ``$id`` information.

v3.0.0
======

* Support for Draft 6 and Draft 7
* Draft 7 is now the default
* New ``TypeChecker`` object for more complex type definitions (and overrides)
* Falling back to isodate for the date-time format checker is no longer
  attempted, in accordance with the specification

v2.6.0
======

* Support for Python 2.6 has been dropped.
* Improve a few error messages for ``uniqueItems`` (#224) and
  ``additionalProperties`` (#317)
* Fixed an issue with ``ErrorTree``'s handling of multiple errors (#288)

v2.5.0
======

* Improved performance on CPython by adding caching around ref resolution
  (#203)

v2.4.0
======

* Added a CLI (#134)
* Added absolute path and absolute schema path to errors (#120)
* Added ``relevance``
* Meta-schemas are now loaded via ``pkgutil``

v2.3.0
======

* Added ``by_relevance`` and ``best_match`` (#91)
* Fixed ``format`` to allow adding formats for non-strings (#125)
* Fixed the ``uri`` format to reject URI references (#131)

v2.2.0
======

* Compile the host name regex (#127)
* Allow arbitrary objects to be types (#129)

v2.1.0
======

* Support RFC 3339 datetimes in conformance with the spec
* Fixed error paths for additionalItems + items (#122)
* Fixed wording for min / maxProperties (#117)


v2.0.0
======

* Added ``create`` and ``extend`` to ``jsonschema.validators``
* Removed ``ValidatorMixin``
* Fixed array indices ref resolution (#95)
* Fixed unknown scheme defragmenting and handling (#102)


v1.3.0
======

* Better error tracebacks (#83)
* Raise exceptions in ``ErrorTree``\s for keys not in the instance (#92)
* __cause__ (#93)


v1.2.0
======

* More attributes for ValidationError (#86)
* Added ``ValidatorMixin.descend``
* Fixed bad ``RefResolutionError`` message (#82)


v1.1.0
======

* Canonicalize URIs (#70)
* Allow attaching exceptions to ``format`` errors (#77)


v1.0.0
======

* Support for Draft 4
* Support for format
* Longs are ints too!
* Fixed a number of issues with ``$ref`` support (#66)
* Draft4Validator is now the default
* ``ValidationError.path`` is now in sequential order
* Added ``ValidatorMixin``


v0.8.0
======

* Full support for JSON References
* ``validates`` for registering new validators
* Documentation
* Bugfixes

    * uniqueItems not so unique (#34)
    * Improper any (#47)


v0.7
====

* Partial support for (JSON Pointer) ``$ref``
* Deprecations

  * ``Validator`` is replaced by ``Draft3Validator`` with a slightly different
    interface
  * ``validator(meta_validate=False)``


v0.6
====

* Bugfixes

  * Issue #30 - Wrong behavior for the dependencies property validation
  * Fixed a miswritten test


v0.5
====

* Bugfixes

  * Issue #17 - require path for error objects
  * Issue #18 - multiple type validation for non-objects


v0.4
====

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
====

* Default for unknown types and properties is now to *not* error (consistent
  with the schema).
* Python 3 support
* Removed dependency on SecureTypes now that the hash bug has been resolved.
* "Numerous bug fixes" -- most notably, a divisibleBy error for floats and a
  bunch of missing typechecks for irrelevant properties.
