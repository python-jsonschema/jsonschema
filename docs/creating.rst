.. _creating-validators:

================================
Creating or Extending Validators
================================

.. currentmodule:: jsonschema

.. autoclass:: ValidatorMixin

.. autofunction:: validates


Creating Validation Errors
--------------------------

Any validating function that validates against a subschema should call
:meth:`ValidatorMixin.descend`, rather than :meth:`ValidatorMixin.iter_errors`.
If it recurses into the instance, or schema, it must set the ``path`` or
``schema_path`` in order to properly maintain where in the instance and schema
the error occurred.
