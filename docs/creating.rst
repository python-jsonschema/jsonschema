.. currentmodule:: jsonschema.validators

.. _creating-validators:

=======================================
Creating or Extending Validator Classes
=======================================

.. autofunction:: create

    Create a new validator class.

    Arguments:

        meta_schema (collections.Mapping):

            the meta schema for the new validator class

        validators (collections.Mapping):

            a mapping from names to callables, where each callable will
            validate the schema property with the given name.

            Each callable should take 4 arguments:

                1. a validator instance,
                2. the value of the property being validated within the
                   instance
                3. the instance
                4. the schema

        version (str):

            an identifier for the version that this validator class will
            validate. If provided, the returned validator class will have its
            ``__name__`` set to include the version, and also will have
            `jsonschema.validators.validates` automatically called for the
            given version.

        type_checker (jsonschema.TypeChecker):

            a type checker, used when applying the :validator:`type` validator.

            If unprovided, an empty `jsonschema.TypeChecker` will created with
            no known default types.

        default_types (collections.Mapping):

            .. deprecated:: 2.7.0

                Please use the type_checker argument instead.

            If set, it provides mappings of JSON types to Python types that
            will be converted to functions and redefined in this object's
            `jsonschema.TypeChecker`.

    Returns:

        a new `jsonschema.IValidator` class


.. autofunction:: extend

    Create a new validator class by extending an existing one.

    Arguments:

        validator (jsonschema.IValidator):

            an existing validator class

        validators (collections.Mapping):

            a mapping of new validator callables to extend with, whose
            structure is as in `create`.

            .. note::

                Any validator callables with the same name as an existing one
                will (silently) replace the old validator callable entirely,
                effectively overriding any validation done in the "parent"
                validator class.

                If you wish to instead extend the behavior of a parent's
                validator callable, delegate and call it directly in the new
                validator function by retrieving it using
                ``OldValidator.VALIDATORS["validator_name"]``.

        version (str):

            a version for the new validator class

        type_checker (jsonschema.TypeChecker):

            a type checker, used when applying the :validator:`type` validator.

            If unprovided, the type checker of the extended
            `jsonschema.IValidator` will be carried along.`

    Returns:

        a new `jsonschema.IValidator` class extending the one provided

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

    Arguments:

        schema (dict):

            the schema to look at

        default:

            the default to return if the appropriate validator class cannot be
            determined.

            If unprovided, the default is to return
            `jsonschema.Draft4Validator`.


.. autofunction:: validates


Creating Validation Errors
--------------------------

Any validating function that validates against a subschema should call
``descend``, rather than ``iter_errors``. If it recurses into the
instance, or schema, it should pass one or both of the ``path`` or
``schema_path`` arguments to ``descend`` in order to properly maintain
where in the instance or schema respectively the error occurred.
