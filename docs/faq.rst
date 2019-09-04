==========================
Frequently Asked Questions
==========================


Why doesn't my schema's default property set the default on my instance?
------------------------------------------------------------------------

The basic answer is that the specification does not require that
:validator:`default` actually do anything.

For an inkling as to *why* it doesn't actually do anything, consider
that none of the other validators modify the instance either. More
importantly, having :validator:`default` modify the instance can produce
quite peculiar things. It's perfectly valid (and perhaps even useful)
to have a default that is not valid under the schema it lives in! So an
instance modified by the default would pass validation the first time,
but fail the second!

Still, filling in defaults is a thing that is useful. `jsonschema`
allows you to `define your own validator classes and callables
<creating>`, so you can easily create an `jsonschema.IValidator` that
does do default setting. Here's some code to get you started. (In
this code, we add the default properties to each object *before* the
properties are validated, so the default values themselves will need to
be valid under the schema.)

    .. code-block:: python

        from jsonschema import Draft7Validator, validators


        def extend_with_default(validator_class):
            validate_properties = validator_class.VALIDATORS["properties"]

            def set_defaults(validator, properties, instance, schema):
                for property, subschema in properties.items():
                    if "default" in subschema:
                        instance.setdefault(property, subschema["default"])

                for error in validate_properties(
                    validator, properties, instance, schema,
                ):
                    yield error

            return validators.extend(
                validator_class, {"properties" : set_defaults},
            )


        DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)


        # Example usage:
        obj = {}
        schema = {'properties': {'foo': {'default': 'bar'}}}
        # Note jsonschem.validate(obj, schema, cls=DefaultValidatingDraft7Validator)
        # will not work because the metaschema contains `default` directives.
        DefaultValidatingDraft7Validator(schema).validate(obj)
        assert obj == {'foo': 'bar'}


See the above-linked document for more info on how this works, but
basically, it just extends the :validator:`properties` validator on
a `jsonschema.Draft7Validator` to then go ahead and update all the
defaults.

.. note::

    If you're interested in a more interesting solution to a larger
    class of these types of transformations, keep an eye on `Seep
    <https://github.com/Julian/Seep>`_, which is an experimental
    data transformation and extraction library written on top of
    `jsonschema`.


.. hint::

    The above code can provide default values for an entire object and
    all of its properties, but only if your schema provides a default
    value for the object itself, like so:

    .. code-block:: python

        schema = {
            "type": "object",
            "properties": {
                "outer-object": {
                    "type": "object",
                    "properties" : {
                        "inner-object": {
                            "type": "string",
                            "default": "INNER-DEFAULT"
                        }
                    },
                    "default": {} # <-- MUST PROVIDE DEFAULT OBJECT
                }
            }
        }

        obj = {}
        DefaultValidatingDraft7Validator(schema).validate(obj)
        assert obj == {'outer-object': {'inner-object': 'INNER-DEFAULT'}}

    ...but if you don't provide a default value for your object, then
    it won't be instantiated at all, much less populated with default
    properties.

    .. code-block:: python

        del schema["properties"]["outer-object"]["default"]
        obj2 = {}
        DefaultValidatingDraft7Validator(schema).validate(obj2)
        assert obj2 == {} # whoops


How do jsonschema version numbers work?
---------------------------------------

``jsonschema`` tries to follow the `Semantic Versioning
<https://semver.org/>`_ specification.

This means broadly that no backwards-incompatible changes should be made
in minor releases (and certainly not in dot releases).

The full picture requires defining what constitutes a
backwards-incompatible change.

The following are simple examples of things considered public API,
and therefore should *not* be changed without bumping a major version
number:

    * module names and contents, when not marked private by Python
      convention (a single leading underscore)

    * function and object signature (parameter order and name)

The following are *not* considered public API and may change without
notice:

    * the exact wording and contents of error messages; typical
      reasons to do this seem to involve unit tests. API users are
      encouraged to use the extensive introspection provided in
      `jsonschema.exceptions.ValidationError`\s instead to make meaningful
      assertions about what failed.

    * the order in which validation errors are returned or raised

    * the contents of the ``jsonschema.tests`` package

    * the contents of the ``jsonschema.benchmarks`` package

    * the ``jsonschema.compat`` module, which is for internal
      compatibility use

    * anything marked private

With the exception of the last two of those, flippant changes are
avoided, but changes can and will be made if there is improvement to be
had. Feel free to open an issue ticket if there is a specific issue or
question worth raising.
