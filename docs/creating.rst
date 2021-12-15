.. currentmodule:: jsonschema.validators

.. _creating-validators:

=======================================
Creating or Extending Validator Classes
=======================================

.. autofunction:: create

.. autofunction:: extend

.. autofunction:: validator_for

.. autofunction:: validates


Creating Validation Errors
--------------------------

Any validating function that validates against a subschema should call
``descend``, rather than ``iter_errors``. If it recurses into the
instance, or schema, it should pass one or both of the ``path`` or
``schema_path`` arguments to ``descend`` in order to properly maintain
where in the instance or schema respectively the error occurred.

The Validator Protocol
----------------------

``jsonschema`` defines a `protocol <typing.Protocol>`,
`jsonschema.protocols.Validator` which can be used in type annotations to
describe the type of a validator object.

For full details, see `validator-protocol`.
