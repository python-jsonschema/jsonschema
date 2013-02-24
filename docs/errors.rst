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

        The failed validator.

    .. attribute:: path

        A deque containing the path to the offending element (or an empty deque
        if the error happened globally).


In case an invalid schema itself is encountered, a :exc:`SchemaError` is
raised.

.. autoexception:: SchemaError

    The provided schema is malformed.

    The same attributes are present as for :exc:`ValidationError`\s.

ErrorTrees
----------

If you want to programmatically be able to query which properties or validators
failed when validating a given instance, you probably will want to do so using
:class:`ErrorTree` objects.

.. autoclass:: ErrorTree
    :members:

Consider the following example:

.. code-block:: python

    >>> from jsonschema import ErrorTree, Draft3Validator
    >>> schema = {
    ...     "type" : "array",
    ...     "items" : {"type" : "number", "enum" : [1, 2, 3]},
    ...     "minItems" : 3,
    ... }
    >>> instance = ["spam", 2]

For clarity's sake, the given instance has three errors under this schema:

.. code-block:: python

    >>> v = Draft3Validator(schema)
    >>> for error in sorted(v.iter_errors(["spam", 2]), key=str):
    ...     print error
    'spam' is not of type 'number'
    'spam' is not one of [1, 2, 3]
    ['spam', 2] is too short

Let's construct an :class:`ErrorTree` so that we can query the errors a bit
more easily than by just iterating over the error objects.

.. code-block:: python

    >>> tree = ErrorTree(v.iter_errors(instance))

As you can see, :class:`ErrorTree` takes an iterable of
:class:`ValidationError`\s when constructing a tree so you can directly pass it
the return value of a validator's ``iter_errors`` method.

:class:`ErrorTree`\s support a number of useful operations. The first one we
might want to perform is to check whether a given element in our instance
failed validation. We do so using the ``in`` operator:

.. code-block:: python

    >>> 0 in tree
    True

    >>> 1 in tree
    False

The interpretation here is that the 0th index into the instance (``"spam"``)
did have an error (in fact it had 2), while the 1th index (``2``) did not (i.e.
it was valid).

If we want to see which errors a child had, we index into the tree and look at
the ``errors`` attribute.

.. code-block:: python

    >>> sorted(tree[0].errors)
    ['enum', 'type']

Here we see that the ``enum`` and ``type`` validators failed for index 0. In
fact ``errors`` is a dict, whose values are the :class:`ValidationError`\s, so
we can get at those directly if we want them.

.. code-block:: python

    >>> print(tree[0].errors["type"].message)
    'spam' is not of type 'number'

Of course this means that if we want to know if a given validator failed for a
given index, we check for its presence in ``errors``:

.. code-block:: python

    >>> "enum" in tree[0].errors
    True

    >>> "minimum" in tree[0].errors
    False

Finally, if you were paying close enough attention, you'll notice that we
haven't seen our ``minItems`` error appear anywhere yet. This is because
``minItems`` is an error that applies globally to the instance itself. So it
appears in the root node of the tree.

.. code-block:: python

    >>> "minItems" in tree.errors
    True

That's all you need to know to use error trees.

To summarize, each tree contains child trees that can be accessed by indexing
the tree to get the corresponding child tree for a given index into the
instance. Each tree and child has a ``errors`` attribute, a dict, that maps the
failed validator to the corresponding validation error.
