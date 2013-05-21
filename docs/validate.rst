=================
Schema Validation
=================


.. currentmodule:: jsonschema


The Basics
----------

The simplest way to validate an instance under a given schema is to use the
:func:`validate` function.

.. autofunction:: validate

    Validate an instance under the given schema.

        >>> validate([2, 3, 4], {"maxItems" : 2})
        Traceback (most recent call last):
            ...
        ValidationError: [2, 3, 4] is too long

    :func:`validate` will first verify that the provided schema is itself
    valid, since not doing so can lead to less obvious error messages and fail
    in less obvious or consistent ways. If you know you have a valid schema
    already or don't care, you might prefer using the
    :meth:`~IValidator.validate` method directly on a specific validator
    (e.g. :meth:`Draft4Validator.validate`).


    :argument instance: the instance to validate
    :argument schema: the schema to validate with
    :argument cls: an :class:`IValidator` class that will be used to validate
                   the instance.

    If the ``cls`` argument is not provided, two things will happen in
    accordance with the specification. First, if the schema has a
    :validator:`$schema` property containing a known meta-schema [#]_ then the
    proper validator will be used.  The specification recommends that all
    schemas contain :validator:`$schema` properties for this reason. If no
    :validator:`$schema` property is found, the default validator class is
    :class:`Draft4Validator`.

    Any other provided positional and keyword arguments will be passed on when
    instantiating the ``cls``.

    :raises:
        :exc:`ValidationError` if the instance is invalid

        :exc:`SchemaError` if the schema itself is invalid

    .. rubric:: Footnotes
    .. [#] known by a validator registered with :func:`validates`


The Validator Interface
-----------------------

:mod:`jsonschema` defines an (informal) interface that all validators should
adhere to.

.. class:: IValidator(schema, types=(), resolver=None, format_checker=None)

    :argument dict schema: the schema that the validator will validate with. It
                           is assumed to be valid, and providing an invalid
                           schema can lead to undefined behavior. See
                           :meth:`IValidator.check_schema` to validate a schema
                           first.
    :argument types: Override or extend the list of known types when validating
                     the :validator:`type` property. Should map strings (type
                     names) to class objects that will be checked via
                     :func:`isinstance`. See :ref:`validating-types` for
                     details.
    :type types: dict or iterable of 2-tuples
    :argument resolver: an instance of :class:`RefResolver` that will be used
                        to resolve :validator:`$ref` properties (JSON
                        references). If unprovided, one will be created.
    :argument format_checker: an instance of :class:`FormatChecker` whose
                              :meth:`~conforms` method will be called to check
                              and see if instances conform to each
                              :validator:`format` property present in the
                              schema. If unprovided, no validation will be done
                              for :validator:`format`.

    .. attribute:: DEFAULT_TYPES

        The default mapping of JSON types to Python types used when validating
        :validator:`type` properties in JSON schemas.

    .. attribute:: META_SCHEMA

        An object representing the validator's meta schema (the schema that
        describes valid schemas in the given version).

    .. attribute:: VALIDATORS

        A mapping of validators (:class:`str`\s) to functions that validate the
        validator property with that name. For more information see
        :ref:`creating-validators`.

    .. attribute:: schema

        The schema that was passed in when initializing the validator.


    .. classmethod:: check_schema(schema)

        Validate the given schema against the validator's :attr:`META_SCHEMA`.

        :raises: :exc:`SchemaError` if the schema is invalid

    .. method:: is_type(instance, type)

        Check if the instance is of the given (JSON Schema) type.

        :type type: str
        :rtype: bool
        :raises: :exc:`UnknownType` if ``type`` is not a known type.

        The special type ``"any"`` is valid for any given instance.

    .. method:: is_valid(instance)

        Check if the instance is valid under the current :attr:`schema`.

        :rtype: bool

            >>> schema = {"maxItems" : 2}
            >>> Draft3Validator(schema).is_valid([2, 3, 4])
            False

    .. method:: iter_errors(instance)

        Lazily yield each of the validation errors in the given instance.

        :rtype: an iterable of :exc:`ValidationError`\s

            >>> schema = {
            ...     "type" : "array",
            ...     "items" : {"enum" : [1, 2, 3]},
            ...     "maxItems" : 2,
            ... }
            >>> v = Draft3Validator(schema)
            >>> for error in sorted(v.iter_errors([2, 3, 4]), key=str):
            ...     print(error.message)
            4 is not one of [1, 2, 3]
            [2, 3, 4] is too long

    .. method:: validate(instance)

        Check if the instance is valid under the current :attr:`schema`.

        :raises: :exc:`ValidationError` if the instance is invalid

            >>> schema = {"maxItems" : 2}
            >>> Draft3Validator(schema).validate([2, 3, 4])
            Traceback (most recent call last):
                ...
            ValidationError: [2, 3, 4] is too long


All of the :ref:`versioned validators <versioned-validators>` that are included
with :mod:`jsonschema` adhere to the interface, and implementors of validators
that extend or complement the ones included should adhere to it as well. For
more information see :ref:`creating-validators`.


.. _validating-types:

Validating With Additional Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Occasionally it can be useful to provide additional or alternate types when
validating the JSON Schema's :validator:`type` property. Validators allow this
by taking a ``types`` argument on construction that specifies additional types,
or which can be used to specify a different set of Python types to map to a
given JSON type.

:mod:`jsonschema` tries to strike a balance between performance in the common
case and generality. For instance, JSON Schema defines a ``number`` type, which
can be validated with a schema such as ``{"type" : "number"}``. By default,
this will accept instances of Python :class:`numbers.Number`. This includes in
particular :class:`int`\s and :class:`float`\s, along with
:class:`decimal.Decimal` objects, :class:`complex` numbers etc. For
``integer`` and ``object``, however, rather than checking for
:class:`numbers.Integral` and :class:`collections.abc.Mapping`,
:mod:`jsonschema` simply checks for :class:`int` and :class:`dict`, since the
more general instance checks can introduce significant slowdown, especially
given how common validating these types are.

If you *do* want the generality, or just want to add a few specific additional
types as being acceptible for a validator, :class:`IValidator`\s have a
``types`` argument that can be used to provide additional or new types.

.. code-block:: python

    class MyInteger(object):
        ...

    Draft3Validator(
        schema={"type" : "number"},
        types={"number" : (numbers.Number, MyInteger)},
    )

The list of default Python types for each JSON type is available on each
validator in the :attr:`IValidator.DEFAULT_TYPES` attribute. Note that you
need to specify all types to match if you override one of the existing JSON
types, so you may want to access the set of default types when specifying your
additional type.

.. _versioned-validators:

Versioned Validators
--------------------

:mod:`jsonschema` ships with validators for various versions of the JSON Schema
specification. For details on the methods and attributes that each validator
provides see the :class:`IValidator` interface, which each validator
implements.

.. autoclass:: Draft3Validator

.. autoclass:: Draft4Validator


Validating Formats
------------------

JSON Schema defines the :validator:`format` property which can be used to check
if primitive types (``string``\s, ``number``\s, ``boolean``\s) conform to
well-defined formats. By default, no validation is enforced, but optionally,
validation can be enabled by hooking in a format-checking object into an
:class:`IValidator`.

.. doctest::

    >>> validate("localhost", {"format" : "hostname"})
    >>> validate(
    ...     "-12", {"format" : "hostname"}, format_checker=FormatChecker(),
    ... )
    Traceback (most recent call last):
        ...
    ValidationError: "-12" is not a "hostname"

.. autoclass:: FormatChecker
    :members:
    :exclude-members: cls_checks

    .. attribute:: checkers

        A mapping of currently known formats to tuple of functions that
        validate them and errors that should be caught. New checkers can be
        added and removed either per-instance or globally for all checkers
        using the :meth:`FormatChecker.checks` or
        :meth:`FormatChecker.cls_checks` decorators respectively.

    .. method:: cls_checks(format, raises=())

        Register a decorated function as *globally* validating a new format.

        Any instance created after this function is called will pick up the
        supplied checker.

        :argument str format: the format that the decorated function will check
        :argument Exception raises: the exception(s) raised by the decorated
            function when an invalid instance is found. The exception object
            will be accessible as the :attr:`ValidationError.cause` attribute
            of the resulting validation error.



There are a number of default checkers that :class:`FormatChecker`\s know how
to validate. Their names can be viewed by inspecting the
:attr:`FormatChecker.checkers` attribute. Certain checkers will only be
available if an appropriate package is available for use. The available
checkers, along with their requirement (if any,) are listed below.

==========  ====================
Checker     Notes
==========  ====================
hostname
ipv4
ipv6        OS must have :func:`socket.inet_pton` function
email
uri         requires rfc3987_
date-time   requires isodate_
date
time
regex
color       requires webcolors_
==========  ====================


.. _isodate: http://pypi.python.org/pypi/isodate/
.. _rfc3987: http://pypi.python.org/pypi/rfc3987/
.. _webcolors: http://pypi.python.org/pypi/webcolors/
