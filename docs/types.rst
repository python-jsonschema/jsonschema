.. currentmodule:: jsonschema

=============
Type Checking
=============

Each :class:`IValidator` has an associated :class:`TypeChecker`. The
TypeChecker provides an immutable mapping between names of types and
functions that can test if an instance is of that type. The defaults are
suitable for most users - each of the predefined Validators (Draft3, Draft4)
has a :class:`TypeChecker` that can correctly handle that draft.

See :ref:`validating-types` for an example of providing a custom type check.

.. autoclass:: TypeChecker
    :members:

.. autoexception:: jsonschema.exceptions.UndefinedTypeCheck

    Raised when trying to remove a type check that is not known to this
    TypeChecker. Internally this is also raised when calling
    :meth:`TypeChecker.is_type`, but is caught and re-raised as a
    :class:`jsonschema.exceptions.UnknownType` exception.
