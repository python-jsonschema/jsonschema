.. _creating-validators:

================================
Creating or Extending Validators
================================

.. currentmodule:: jsonschema.validators

.. autofunction:: create

    Create a new validator.

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
