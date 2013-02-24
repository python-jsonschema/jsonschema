.. _creating-validators:

================================
Creating or Extending Validators
================================

.. currentmodule:: jsonschema

.. autoclass:: ValidatorMixin

.. autofunction:: validates


Creating Validation Errors
--------------------------

Any validating function that recurses into an instance (e.g. ``properties`` or
``items``) must call ``appendleft`` on the :exc:`ValidationError.path`
attribute of the error in order to properly maintain where in the instance the
error occurred.
