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

    :argument schema: the schema that the validator will validate with
    :argument types: Override or extend the list of known types when validating
                     the ``type`` property. Should map strings (type names) to
                     class objects that will be checked via ``isinstance``.
    :type types: dict or iterable of 2-tuples
    :argument resolver: an object with a ``resolve()`` method that will be used
                        to resolve ``$ref`` properties (JSON references). If
                        unprovided, a :class:`RefResolver` is created and used.

All of the :ref:`versioned validators <versioned-validators>` that are included
with :mod:`jsonschema` adhere to the interface, and implementors of validators
that extend or complement the ones included should adhere to it as well. For
more information see :ref:`creating-validators`.


.. _versioned-validators:

Versioned Validators
--------------------

.. autoclass:: Draft3Validator
    :members:
