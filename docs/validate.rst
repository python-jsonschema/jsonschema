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

.. class:: IValidator(schema, types=(), resolver=None)

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

    .. method:: iter_errors(instance)

        Lazily yield each of the validation errors in the given instance.

        :rtype: an iterable of :exc:`ValidationError`\s

    .. method:: validate(instance)

        Check if the instance is valid under the current :attr:`schema`.

        :raises: :exc:`ValidationError` if the instance is invalid


All of the :ref:`versioned validators <versioned-validators>` that are included
with :mod:`jsonschema` adhere to the interface, and implementors of validators
that extend or complement the ones included should adhere to it as well. For
more information see :ref:`creating-validators`.


.. _versioned-validators:

Versioned Validators
--------------------

.. autoclass:: Draft3Validator
    :members:


.. _validating-types:

Validating With Additional Types
--------------------------------
