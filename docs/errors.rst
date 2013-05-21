==========================
Handling Validation Errors
==========================

.. currentmodule:: jsonschema

When an invalid instance is encountered, a :exc:`ValidationError` will be
raised or returned, depending on which method or function is used.

.. autoexception:: ValidationError

    The instance didn't properly validate under the provided schema.

    .. attribute:: message

        A human readable message explaining the error.

    .. attribute:: validator

        The failed `validator
        <http://json-schema.org/latest/json-schema-validation.html#anchor12>`_.

    .. attribute:: validator_value

        The value for the failed validator in the schema.

    .. attribute:: schema

        The full schema that this error came from. This is potentially a
        subschema from within the schema that was passed into the validator, or
        even an entirely different schema if a :validator:`$ref` was followed.

    .. attribute:: schema_path

        A :class:`collections.deque` containing the path to the failed
        validator within the schema.

    .. attribute:: path

        A :class:`collections.deque` containing the path to the offending
        element within the instance. The deque can be empty if the error
        happened at the root of the instance.

    .. attribute:: instance

        The instance that was being validated. This will differ from the
        instance originally passed into validate if the validator was in the
        process of validating a (possibly nested) element within the top-level
        instance. The path within the top-level instance (i.e.
        :attr:`ValidationError.path`) could be used to find this object, but it
        is provided for convenience.

    .. attribute:: context

        If the error was caused by errors in subschemas, the list of errors
        from the subschemas will be available on this property. The
        :attr:`.schema_path` and :attr:`.path` of these errors will be relative
        to the parent error.

    .. attribute:: cause

        If the error was caused by a *non*-validation error, the exception
        object will be here. Currently this is only used for the exception
        raised by a failed format checker in :meth:`FormatChecker.check`.


In case an invalid schema itself is encountered, a :exc:`SchemaError` is
raised.

.. autoexception:: SchemaError

    The provided schema is malformed.

    The same attributes are present as for :exc:`ValidationError`\s.


These attributes can be clarified with a short example:

.. testcode::

    schema = {
        "items": {
            "anyOf": [
                {"type": "string", "maxLength": 2},
                {"type": "integer", "minimum": 5}
            ]
        }
    }
    instance = [{}, 3, "foo"]
    v = Draft4Validator(schema)
    errors = sorted(v.iter_errors(instance), key=lambda e: e.path)

The error messages in this situation are not very helpful on their own.

.. testcode::

    for error in errors:
        print(error.message)

outputs:

.. testoutput::

    {} is not valid under any of the given schemas
    3 is not valid under any of the given schemas
    'foo' is not valid under any of the given schemas

If we look at :attr:`~ValidationError.path` on each of the errors, we can find
out which elements in the instance correspond to each of the errors. In
this example, :attr:`~ValidationError.path` will have only one element, which
will be the index in our list.

.. testcode::

    for error in errors:
        print(list(error.path))

.. testoutput::

    [0]
    [1]
    [2]

Since our schema contained nested subschemas, it can be helpful to look at
the specific part of the instance and subschema that caused each of the errors.
This can be seen with the :attr:`~ValidationError.instance` and
:attr:`~ValidationError.schema` attributes.

With validators like :validator:`anyOf`, the :attr:`~ValidationError.context`
attribute can be used to see the sub-errors which caused the failure. Since
these errors actually came from two separate subschemas, it can be helpful to
look at the :attr:`~ValidationError.schema_path` attribute as well to see where
exactly in the schema each of these errors come from. In the case of sub-errors
from the :attr:`~ValidationError.context` attribute, this path will be relative
to the :attr:`~ValidationError.schema_path` of the parent error.

.. testcode::

    for error in errors:
        for suberror in sorted(error.context, key=lambda e: e.schema_path):
            print(list(suberror.schema_path), suberror.message, sep=", ")

.. testoutput::

    [0, 'type'], {} is not of type 'string'
    [1, 'type'], {} is not of type 'integer'
    [0, 'type'], 3 is not of type 'string'
    [1, 'minimum'], 3.0 is less than the minimum of 5
    [0, 'maxLength'], 'foo' is too long
    [1, 'type'], 'foo' is not of type 'integer'

The string representation of an error combines some of these attributes for
easier debugging.

.. testcode::

    print(errors[1])

.. testoutput::

    3 is not valid under any of the given schemas

    Failed validating 'anyOf' in schema['items']:
        {'anyOf': [{'maxLength': 2, 'type': 'string'},
                   {'minimum': 5, 'type': 'integer'}]}

    On instance[1]:
        3

ErrorTrees
----------

If you want to programmatically be able to query which properties or validators
failed when validating a given instance, you probably will want to do so using
:class:`ErrorTree` objects.

.. autoclass:: ErrorTree
    :members:
    :special-members:
    :exclude-members: __dict__,__weakref__

    .. attribute:: errors

        The mapping of validator names to the error objects (usually
        :class:`ValidationError`\s) at this level of the tree.

Consider the following example:

.. testcode::

    schema = {
        "type" : "array",
        "items" : {"type" : "number", "enum" : [1, 2, 3]},
        "minItems" : 3,
    }
    instance = ["spam", 2]

For clarity's sake, the given instance has three errors under this schema:

.. testcode::

    v = Draft3Validator(schema)
    for error in sorted(v.iter_errors(["spam", 2]), key=str):
        print(error.message)

.. testoutput::

    'spam' is not of type 'number'
    'spam' is not one of [1, 2, 3]
    ['spam', 2] is too short

Let's construct an :class:`ErrorTree` so that we can query the errors a bit
more easily than by just iterating over the error objects.

.. testcode::

    tree = ErrorTree(v.iter_errors(instance))

As you can see, :class:`ErrorTree` takes an iterable of
:class:`ValidationError`\s when constructing a tree so you can directly pass it
the return value of a validator's :attr:`~IValidator.iter_errors` method.

:class:`ErrorTree`\s support a number of useful operations. The first one we
might want to perform is to check whether a given element in our instance
failed validation. We do so using the :keyword:`in` operator:

.. doctest::

    >>> 0 in tree
    True

    >>> 1 in tree
    False

The interpretation here is that the 0th index into the instance (``"spam"``)
did have an error (in fact it had 2), while the 1th index (``2``) did not (i.e.
it was valid).

If we want to see which errors a child had, we index into the tree and look at
the :attr:`~ErrorTree.errors` attribute.

.. doctest::

    >>> sorted(tree[0].errors)
    ['enum', 'type']

Here we see that the :validator:`enum` and :validator:`type` validators failed
for index ``0``. In fact :attr:`~ErrorTree.errors` is a dict, whose values are
the :class:`ValidationError`\s, so we can get at those directly if we want
them.

.. doctest::

    >>> print(tree[0].errors["type"].message)
    'spam' is not of type 'number'

Of course this means that if we want to know if a given validator failed for a
given index, we check for its presence in :attr:`~ErrorTree.errors`:

.. doctest::

    >>> "enum" in tree[0].errors
    True

    >>> "minimum" in tree[0].errors
    False

Finally, if you were paying close enough attention, you'll notice that we
haven't seen our :validator:`minItems` error appear anywhere yet. This is
because :validator:`minItems` is an error that applies globally to the instance
itself. So it appears in the root node of the tree.

.. doctest::

    >>> "minItems" in tree.errors
    True

That's all you need to know to use error trees.

To summarize, each tree contains child trees that can be accessed by indexing
the tree to get the corresponding child tree for a given index into the
instance. Each tree and child has a :attr:`~ErrorTree.errors` attribute, a
dict, that maps the failed validator to the corresponding validation error.
