.. _creating-validators:

================================
Creating or Extending Validators
================================

.. currentmodule:: jsonschema.validators

.. autofunction:: create

    Create a new validator.

    :argument dict meta_schema: the meta schema for the new validator

    :argument dict validators: a mapping from validator names to functions that
        validate the given name. Each function should take 4 arguments: a
        validator instance, the value of the current validator property in the
        instance being validated, the instance, and the schema. 

    :argument str version: an identifier for the version that this validator
        will validate. If provided, the returned validator class will have its
        ``__name__`` set to include the version, and also will have
        :func:`validates` automatically called for the given version.

    :argument dict default_types: a default mapping to use for instances of the
        validator when mapping between JSON types to Python types. The default
        for this argument is probably fine. Instances of the returned validator
        can still have their types customized on a per-instance basis.

    :returns: an :class:`jsonschema.IValidator`


.. autofunction:: extend

    Create a new validator that extends an existing validator.

    :argument jsonschema.IValidator validator: an existing validator

    :argument dict validators: a set of new validators to add to the new
        validator. Any validators with the same name as an existing one will
        (silently) replace the old validator entirely.

    :argument str version: a version for the new validator

    :returns: an :class:`jsonschema.IValidator`


.. autofunction:: validates


Creating Validation Errors
--------------------------

Any validating function that validates against a subschema should call
:meth:`ValidatorMixin.descend`, rather than :meth:`ValidatorMixin.iter_errors`.
If it recurses into the instance, or schema, it should pass one or both of the
``path`` or ``schema_path`` arguments to :meth:`ValidatorMixin.descend` in
order to properly maintain where in the instance or schema respsectively the
error occurred.
