==========
jsonschema
==========


.. module:: jsonschema


``jsonschema`` is an implementation of `JSON Schema <http://json-schema.org>`_
for Python (supporting 2.6+ including Python 3).

.. code-block:: python

    >>> from jsonschema import validate

    >>> # A sample schema, like what we'd get from json.load()
    >>> schema = {
    ...     "type" : "object",
    ...     "properties" : {
    ...         "price" : {"type" : "number"},
    ...         "name" : {"type" : "string"},
    ...     },
    ... }

    >>> # If no exception is raised by validate(), the instance is valid.
    >>> validate({"name" : "Eggs", "price" : 34.99}, schema)

    >>> validate(
    ...     {"name" : "Eggs", "price" : "Invalid"}, schema
    ... )                                   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: 'Invalid' is not of type 'number'


You can find further information (installation instructions, mailing list)
as well as the source code and issue tracker on our
`GitHub page <https://github.com/Julian/jsonschema/>`__.

Contents:

.. toctree::
    :maxdepth: 2

    validate
    errors
    references
    creating
    faq


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
