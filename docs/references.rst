=========================
Resolving JSON References
=========================

How to use the RefResolver
--------------------------

This section is intended for those who are having problems with using $ref to
load other schemas from within a given schema.

Loading schemas from within the filesystem requires setting a base uri for
the RefResolver. Otherwise, finding another schema relative to a first schema
will not work.

.. code-block:: python

        import os
        from jsonschema import Draft4Validator, RefResolver

        def get_draft4_validator(schema_absolute_path):
          """
          Return a draft4 validator with the base_uri
          set to the schema path so that file refs are resolved
          """
          with open(schema_absolute_path) as schema_file:
            schema = json.load(schema_file)
          resolver = RefResolver("file://" + schema_absolute_path, schema)
          return Draft4Validator(schema, resolver=resolver)





.. currentmodule:: jsonschema

.. autoclass:: RefResolver
    :members:

.. autoexception:: RefResolutionError

    A JSON reference failed to resolve.
