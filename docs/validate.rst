=================
Schema Validation
=================


.. currentmodule:: jsonschema


The Basics
----------

The simplest way to validate an instance under a given schema is to use the
:func:`validate` function.

.. autofunction:: validate


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
                     the ``type`` property. Should map strings (type names) to
                     class objects that will be checked via ``isinstance``. See
                     :ref:`validating-types` for details.
    :type types: dict or iterable of 2-tuples
    :argument resolver: an object with a ``resolve()`` method that will be used
                        to resolve ``$ref`` properties (JSON references). If
                        unprovided, a :class:`RefResolver` is created and used.
    :argument format_checker: an object with a ``conform()`` method that will
                              be called to check and see if instances conform
                              to each ``format`` property present in the
                              schema. If unprovided, no validation will be done
                              for ``format``. :class:`FormatChecker` is a
                              concrete implementation of an object of this form
                              that can be used for common formats.

    .. attribute:: DEFAULT_TYPES

        The default mapping of JSON types to Python types used when validating
        ``type`` properties in JSON schemas.

    .. attribute:: META_SCHEMA

        An object representing the validator's meta schema (the schema that
        describes valid schemas in the given version).

    .. attribute:: schema

        The schema that was passed in when initializing the validator.


    .. classmethod:: check_schema(schema)

        Validate the given schema against the validator's :attr:`META_SCHEMA`.

        :raises: :exc:`SchemaError` if the schema is invalid

    .. method:: is_type(instance, type)

        Check if the instance is of the given (JSON Schema) type.

        :type type: str
        :rtype: bool

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
            ...     print(error)
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
validating the JSON Schema's ``type`` property. Validators allow this by taking
a ``types`` argument on construction that specifies additional types, or which
can be used to specify a different set of Python types to map to a given JSON
type.

For instance, JSON defines a ``number`` type, which can be validated with a
schema such as ``{"type" : "number"}``. By default, this will validate
correctly for Python :class:`int`\s and :class:`float`\s. If you wanted to
additionally validate :class:`decimal.Decimal` objects, you'd use

.. code-block:: python

    Draft3Validator(
        schema={"type" : "number"},
        types={"number" : (int, float, decimal.Decimal)},
    )

The list of default Python types for each JSON type is available on each
validator in the :attr:`IValidator.DEFAULT_TYPES` attribute. Note that you
need to specify all types to match if you override one of the existing JSON
types, so you may want to access the set of default types to add it to the
ones being appended.


.. _versioned-validators:

Versioned Validators
--------------------

:mod:`jsonschema` ships with validators for various versions of the JSON Schema
specification. For details on the methods and attributes that each validator
provides see the :class:`IValidator` interface, which each validator
implements.

.. autoclass:: Draft3Validator


Validating Formats
------------------

JSON Schema defines the ``format`` property which can be used to check if
primitive types (``str``\s, ``number``\s, ``bool``\s) conform to well-defined
formats. By default, no validation is enforced, but optionally, validation can
be enabled by hooking in a format-checking object into an :class:`IValidator`.

.. autoclass:: FormatChecker
    :members:

.. autofunction:: is_date_time
