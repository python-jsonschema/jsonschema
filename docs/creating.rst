.. _creating-validators:

=======================================
Creating or Extending Validator Classes
=======================================

.. currentmodule:: jsonschema.validators

.. autofunction:: create

    Create a new validator class.

    :argument dict meta_schema: the meta schema for the new validator class

    :argument dict validators: a mapping from names to callables, where
        each callable will validate the schema property with the given
        name.
        
        Each callable should take 4 arguments:

            1. a validator instance,
            2. the value of the property being validated within the instance
            3. the instance
            4. the schema

    :argument str version: an identifier for the version that this validator
        class will validate. If provided, the returned validator class
        will have its ``__name__`` set to include the version, and also
        will have :func:`validates` automatically called for the given
        version.

    :argument dict default_types: a default mapping to use for instances
        of the validator class when mapping between JSON types to Python
        types. The default for this argument is probably fine. Instances
        can still have their types customized on a per-instance basis.

    :returns: a new :class:`jsonschema.IValidator` class


.. autofunction:: extend

    Create a new validator class by extending an existing one.

    :argument jsonschema.IValidator validator: an existing validator class

    :argument dict validators: a mapping of new validator callables to extend
        with, whose structure is as in :func:`create`\ .

        .. note::

            Any validator callables with the same name as an existing one will
            (silently) replace the old validator callable entirely, effectively
            overriding any validation done in the "parent" validator class.

            If you wish to instead extend the behavior of a parent's
            validator callable, delegate and call it directly in
            the new validator function by retrieving it using
            ``OldValidator.VALIDATORS["validator_name"]``.

    :argument str version: a version for the new validator class

    :returns: a new :class:`jsonschema.IValidator` class

    .. note:: Meta Schemas

        The new validator class will have its parent's meta schema.

        If you wish to change or extend the meta schema in the new
        validator class, modify ``META_SCHEMA`` directly on the returned
        class. Note that no implicit copying is done, so a copy should
        likely be made before modifying it, in order to not affect the
        old validator.


.. autofunction:: validator_for

    Retrieve the validator class appropriate for validating the given schema.

    Uses the :validator:`$schema` property that should be present in the given
    schema to look up the appropriate validator class.

    :argument schema: the schema to look at
    :argument default: the default to return if the appropriate validator class
        cannot be determined. If unprovided, the default is to return
        :class:`Draft4Validator`


.. autofunction:: validates


Creating Validation Errors
--------------------------

Any validating function that validates against a subschema should call
:meth:`ValidatorMixin.descend`, rather than :meth:`ValidatorMixin.iter_errors`.
If it recurses into the instance, or schema, it should pass one or both of the
``path`` or ``schema_path`` arguments to :meth:`ValidatorMixin.descend` in
order to properly maintain where in the instance or schema respectively the
error occurred.
