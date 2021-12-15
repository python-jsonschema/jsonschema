=================
Schema Validation
=================


.. currentmodule:: jsonschema


The Basics
----------

The simplest way to validate an instance under a given schema is to use the
:func:`validate` function.

.. autofunction:: validate

.. [#] For information on creating JSON schemas to validate
    your data, there is a good introduction to JSON Schema
    fundamentals underway at `Understanding JSON Schema
    <https://json-schema.org/understanding-json-schema/>`_

.. _validator-protocol:

The Validator Protocol
-----------------------

`jsonschema` defines a protocol that all validator
classes should adhere to.

.. autoclass:: jsonschema.protocols.Validator
    :members:

All of the `versioned validators <versioned-validators>` that are included with
`jsonschema` adhere to the protocol, and implementers of validator classes
that extend or complement the ones included should adhere to it as well. For
more information see `creating-validators`.

Type Checking
-------------

To handle JSON Schema's :validator:`type` property, a `Validator` uses
an associated `TypeChecker`. The type checker provides an immutable
mapping between names of types and functions that can test if an instance is
of that type. The defaults are suitable for most users - each of the
`versioned validators <versioned-validators>` that are included with
`jsonschema` have a `TypeChecker` that can correctly handle their respective
versions.

.. seealso:: `validating-types`

    For an example of providing a custom type check.

.. autoclass:: TypeChecker
    :members:

.. autoexception:: jsonschema.exceptions.UndefinedTypeCheck

    Raised when trying to remove a type check that is not known to this
    TypeChecker, or when calling `jsonschema.TypeChecker.is_type`
    directly.

.. _validating-types:

Validating With Additional Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Occasionally it can be useful to provide additional or alternate types when
validating the JSON Schema's :validator:`type` property.

`jsonschema` tries to strike a balance between performance in the common
case and generality. For instance, JSON Schema defines a ``number`` type, which
can be validated with a schema such as ``{"type" : "number"}``. By default,
this will accept instances of Python `numbers.Number`. This includes in
particular `int`\s and `float`\s, along with
`decimal.Decimal` objects, `complex` numbers etc. For
``integer`` and ``object``, however, rather than checking for
`numbers.Integral` and `collections.abc.Mapping`,
`jsonschema` simply checks for `int` and `dict`, since the
more general instance checks can introduce significant slowdown, especially
given how common validating these types are.

If you *do* want the generality, or just want to add a few specific additional
types as being acceptable for a validator object, then you should update an
existing `TypeChecker` or create a new one. You may then create a new
`Validator` via `jsonschema.validators.extend`.

.. code-block:: python

    class MyInteger(object):
        pass

    def is_my_int(checker, instance):
        return (
            Draft3Validator.TYPE_CHECKER.is_type(instance, "number") or
            isinstance(instance, MyInteger)
        )

    type_checker = Draft3Validator.TYPE_CHECKER.redefine("number", is_my_int)

    CustomValidator = extend(Draft3Validator, type_checker=type_checker)
    validator = CustomValidator(schema={"type" : "number"})


.. autoexception:: jsonschema.exceptions.UnknownType

.. _versioned-validators:

Versioned Validators
--------------------

`jsonschema` ships with validator classes for various versions of
the JSON Schema specification. For details on the methods and attributes
that each validator class provides see the `Validator` protocol,
which each included validator class implements.

.. autoclass:: Draft202012Validator

.. autoclass:: Draft201909Validator

.. autoclass:: Draft7Validator

.. autoclass:: Draft6Validator

.. autoclass:: Draft4Validator

.. autoclass:: Draft3Validator


For example, if you wanted to validate a schema you created against the
Draft 7 meta-schema, you could use:

.. code-block:: python

    from jsonschema import Draft7Validator

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",

        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
        },
        "required": ["email"]
    }
    Draft7Validator.check_schema(schema)


.. _validating formats:

Validating Formats
------------------

JSON Schema defines the :validator:`format` property which can be used to check
if primitive types (``string``\s, ``number``\s, ``boolean``\s) conform to
well-defined formats. By default, no validation is enforced, but optionally,
validation can be enabled by hooking in a format-checking object into an
`Validator`.

.. doctest::

    >>> validate("127.0.0.1", {"format" : "ipv4"})
    >>> validate(
    ...     instance="-12",
    ...     schema={"format" : "ipv4"},
    ...     format_checker=draft7_format_checker,
    ... )
    Traceback (most recent call last):
        ...
    ValidationError: "-12" is not a "ipv4"

.. autoclass:: FormatChecker
    :members:
    :exclude-members: cls_checks

    .. attribute:: checkers

        A mapping of currently known formats to tuple of functions that
        validate them and errors that should be caught. New checkers can be
        added and removed either per-instance or globally for all checkers
        using the `FormatChecker.checks` or `FormatChecker.cls_checks`
        decorators respectively.

    .. classmethod:: cls_checks(format, raises=())

        Register a decorated function as *globally* validating a new format.

        Any instance created after this function is called will pick up the
        supplied checker.

        :argument str format: the format that the decorated function will check
        :argument Exception raises: the exception(s) raised
            by the decorated function when an invalid instance is
            found. The exception object will be accessible as the
            `jsonschema.exceptions.ValidationError.cause` attribute
            of the resulting validation error.


.. autoexception:: FormatError
    :members:


There are a number of default checkers that `FormatChecker`\s know how
to validate. Their names can be viewed by inspecting the
`FormatChecker.checkers` attribute. Certain checkers will only be
available if an appropriate package is available for use. The easiest way to
ensure you have what is needed is to install ``jsonschema`` using the
``format`` or ``format_nongpl`` setuptools extra -- i.e.

.. code-block:: sh

   $ pip install jsonschema[format]

which will install all of the below dependencies for all formats.

Or if you want to install MIT-license compatible dependencies only:

.. code-block:: sh

   $ pip install jsonschema[format_nongpl]

The non-GPL extra is intended to not install any direct dependencies
that are GPL (but that of course end-users should do their own verification).
At the moment, it supports all the available checkers except for ``iri`` and
``iri-reference``.

The more specific list of available checkers, along with their requirement
(if any,) are listed below.

.. note::

    If the following packages are not installed when using a checker
    that requires it, validation will succeed without throwing an error,
    as specified by the JSON Schema specification.

=========================  ====================
Checker                    Notes
=========================  ====================
``color``                  requires webcolors_
``date``
``date-time``              requires rfc3339-validator_
``duration``               requires isoduration_
``email``
``hostname``               requires fqdn_
``idn-hostname``           requires idna_
``ipv4``
``ipv6``                   OS must have `socket.inet_pton` function
``iri``                    requires rfc3987_
``iri-reference``          requires rfc3987_
``json-pointer``           requires jsonpointer_
``regex``
``relative-json-pointer``  requires jsonpointer_
``time``                   requires rfc3339-validator_
``uri``                    requires rfc3987_ or rfc3986-validator_
``uri-reference``          requires rfc3987_ or rfc3986-validator_
``uri-template``           requires uri-template_
=========================  ====================


.. _fqdn: https://pypi.org/pypi/fqdn/
.. _idna: https://pypi.org/pypi/idna/
.. _isoduration: https://pypi.org/pypi/isoduration/
.. _jsonpointer: https://pypi.org/pypi/jsonpointer/
.. _rfc3339-validator: https://pypi.org/project/rfc3339-validator/
.. _rfc3986-validator: https://pypi.org/project/rfc3986-validator/
.. _rfc3987: https://pypi.org/pypi/rfc3987/
.. _rfc5322: https://tools.ietf.org/html/rfc5322#section-3.4.1
.. _uri-template: https://pypi.org/pypi/uri-template/
.. _webcolors: https://pypi.org/pypi/webcolors/

.. note::

    Since in most cases "validating" an email address is an attempt
    instead to confirm that mail sent to it will deliver to a recipient,
    and that that recipient is the correct one the email is intended
    for, and since many valid email addresses are in many places
    incorrectly rejected, and many invalid email addresses are in many
    places incorrectly accepted, the ``email`` format validator only
    provides a sanity check, not full rfc5322_ validation.

    The same applies to the ``idn-email`` format.
