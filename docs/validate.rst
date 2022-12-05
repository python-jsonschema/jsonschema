=================
Schema Validation
=================


.. currentmodule:: jsonschema

.. tip::

   Most of the documentation for this package assumes you're familiar with the fundamentals of writing JSON schemas themselves, and focuses on how this library helps you validate with them in Python.

   If you aren't already comfortable with writing schemas and need an introduction which teaches about JSON Schema the specification, you may find `Understanding JSON Schema <ujs:basics>` to be a good read!


The Basics
----------

The simplest way to validate an instance under a given schema is to use the
`validate <jsonschema.validators.validate>` function.

.. autofunction:: validate
    :noindex:

.. _validator-protocol:

The Validator Protocol
----------------------

`jsonschema` defines a `protocol <typing.Protocol>` that all validator classes adhere to.

.. hint::

    If you are unfamiliar with protocols, either as a general notion or as specifically implemented by `typing.Protocol`, you can think of them as a set of attributes and methods that all objects satisfying the protocol have.

    Here, in the context of `jsonschema`, the `Validator.iter_errors` method can be called on `jsonschema.validators.Draft202012Validator`, or `jsonschema.validators.Draft7Validator`, or indeed any validator class, as all of them have it, along with all of the other methods described below.

.. autoclass:: jsonschema.protocols.Validator
    :noindex:
    :members:

All of the `versioned validators <versioned-validators>` that are included with `jsonschema` adhere to the protocol, and any `extensions of these validators <jsonschema.validators.extend>` will as well.
For more information on `creating <jsonschema.validators.create>` or `extending <jsonschema.validators.extend>` validators see `creating-validators`.

Type Checking
-------------

To handle JSON Schema's :kw:`type` keyword, a `Validator` uses
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
    :noindex:

.. autoexception:: jsonschema.exceptions.UndefinedTypeCheck
    :noindex:

    Raised when trying to remove a type check that is not known to this
    TypeChecker, or when calling `jsonschema.TypeChecker.is_type`
    directly.

.. _validating-types:

Validating With Additional Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Occasionally it can be useful to provide additional or alternate types when
validating JSON Schema's :kw:`type` keyword.

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
existing `jsonschema.TypeChecker` or create a new one. You may then create a new
`Validator` via `jsonschema.validators.extend`.

.. testcode::

    from jsonschema import validators

    class MyInteger:
        pass

    def is_my_int(checker, instance):
        return (
            Draft202012Validator.TYPE_CHECKER.is_type(instance, "number") or
            isinstance(instance, MyInteger)
        )

    type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
        "number", is_my_int,
    )

    CustomValidator = validators.extend(
        Draft202012Validator,
        type_checker=type_checker,
    )
    validator = CustomValidator(schema={"type" : "number"})


.. autoexception:: jsonschema.exceptions.UnknownType
    :noindex:

.. _versioned-validators:

Versioned Validators
--------------------

`jsonschema` ships with validator classes for various versions of the JSON Schema specification.
For details on the methods and attributes that each validator class provides see the `Validator` protocol, which each included validator class implements.

Each of the below cover a specific release of the JSON Schema specification.

.. autoclass:: Draft202012Validator
    :noindex:

.. autoclass:: Draft201909Validator
    :noindex:

.. autoclass:: Draft7Validator
    :noindex:

.. autoclass:: Draft6Validator
    :noindex:

.. autoclass:: Draft4Validator
    :noindex:

.. autoclass:: Draft3Validator
    :noindex:


For example, if you wanted to validate a schema you created against the
Draft 2020-12 meta-schema, you could use:

.. testcode::

    from jsonschema import Draft202012Validator

    schema = {
        "$schema": Draft202012Validator.META_SCHEMA["$id"],

        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
        },
        "required": ["email"]
    }
    Draft202012Validator.check_schema(schema)


.. _validating formats:

Validating Formats
------------------

JSON Schema defines the :kw:`format` keyword which can be used to check if primitive types (``string``\s, ``number``\s, ``boolean``\s) conform to well-defined formats.
By default, as per the specification, no validation is enforced.
Optionally however, validation can be enabled by hooking a `format-checking object <jsonschema.FormatChecker>` into a `Validator`.

.. doctest::

    >>> validate("127.0.0.1", {"format" : "ipv4"})
    >>> validate(
    ...     instance="-12",
    ...     schema={"format" : "ipv4"},
    ...     format_checker=Draft202012Validator.FORMAT_CHECKER,
    ... )
    Traceback (most recent call last):
        ...
    ValidationError: "-12" is not a "ipv4"


Some formats require additional dependencies to be installed.

The easiest way to ensure you have what is needed is to install ``jsonschema`` using the ``format`` or ``format-nongpl`` extras.

For example:

.. code:: sh

    $ pip install jsonschema[format]

Or if you want to avoid GPL dependencies, a second extra is available:

.. code:: sh

    $ pip install jsonschema[format-nongpl]

At the moment, it supports all the available checkers except for ``iri`` and ``iri-reference``.

.. warning::

    It is your own responsibility ultimately to ensure you are license-compliant, so you should be double checking your own dependencies if you rely on this extra.

The more specific list of formats along with any additional dependencies they have is shown below.

.. warning::

    If a dependency is not installed when using a checker that requires it, validation will succeed without throwing an error, as also specified by the specification.

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
.. _uri-template: https://pypi.org/pypi/uri-template/
.. _webcolors: https://pypi.org/pypi/webcolors/

The supported mechanism for ensuring these dependencies are present is again as shown above, not by directly installing the packages.

.. autoclass:: FormatChecker
    :members:
    :noindex:
    :exclude-members: cls_checks

    .. attribute:: checkers

        A mapping of currently known formats to tuple of functions that validate them and errors that should be caught.
        New checkers can be added and removed either per-instance or globally for all checkers using the `FormatChecker.checks` decorator.

    .. classmethod:: cls_checks(format, raises=())

        Register a decorated function as *globally* validating a new format.

        Any instance created after this function is called will pick up the supplied checker.

        :argument str format: the format that the decorated function will check
        :argument Exception raises: the exception(s) raised
            by the decorated function when an invalid instance is
            found. The exception object will be accessible as the
            `jsonschema.exceptions.ValidationError.cause` attribute
            of the resulting validation error.

        .. deprecated:: v4.14.0

            Use `FormatChecker.checks` on an instance instead.

.. autoexception:: FormatError
    :noindex:
    :members:


Format-Specific Notes
~~~~~~~~~~~~~~~~~~~~~

regex
^^^^^

The JSON Schema specification `recommends (but does not require) <https://json-schema.org/draft/2020-12/json-schema-core.html#name-regular-expressions>`_ that implementations use ECMA 262 regular expressions.

Given that there is no current library in Python capable of supporting the ECMA 262 dialect, the ``regex`` format will instead validate *Python* regular expressions, which are the ones used by this implementation for other keywords like :kw:`pattern` or :kw:`patternProperties`.

email
^^^^^

Since in most cases "validating" an email address is an attempt instead to confirm that mail sent to it will deliver to a recipient, and that that recipient is the correct one the email is intended for, and since many valid email addresses are in many places incorrectly rejected, and many invalid email addresses are in many places incorrectly accepted, the ``email`` format keyword only provides a sanity check, not full :RFC:`5322` validation.

The same applies to the ``idn-email`` format.

If you indeed want a particular well-specified set of emails to be considered valid, you can use `FormatChecker.checks` to provide your specific definition.
