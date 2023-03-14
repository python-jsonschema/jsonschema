==========================
Frequently Asked Questions
==========================

My schema specifies format validation. Why do invalid instances seem valid?
---------------------------------------------------------------------------

The :kw:`format` keyword can be a bit of a stumbling block for new
users working with JSON Schema.

In a schema such as:

.. code-block:: json

    {"type": "string", "format": "date"}

JSON Schema specifications have historically differentiated between the
:kw:`format` keyword and other keywords. In particular, the
:kw:`format` keyword was specified to be *informational* as much
as it may be used for validation.

In other words, for many use cases, schema authors may wish to use
values for the :kw:`format` keyword but have no expectation
they be validated alongside other required assertions in a schema.

Of course this does not represent all or even most use cases -- many
schema authors *do* wish to assert that instances conform fully, even to
the specific format mentioned.

In drafts prior to ``draft2019-09``, the decision on whether to
automatically enable :kw:`format` validation was left up to
validation implementations such as this one.

This library made the choice to leave it off by default, for two reasons:

    * for forward compatibility and implementation complexity reasons
      -- if :kw:`format` validation were on by default, and a
      future draft of JSON Schema introduced a hard-to-implement format,
      either the implementation of that format would block releases of
      this library until it were implemented, or the behavior surrounding
      :kw:`format` would need to be even more complex than simply
      defaulting to be on. It therefore was safer to start with it off,
      and defend against the expectation that a given format would always
      automatically work.

    * given that a common use of JSON Schema is for portability across
      languages (and therefore implementations of JSON Schema), so that
      users be aware of this point itself regarding :kw:`format`
      validation, and therefore remember to check any *other*
      implementations they were using to ensure they too were explicitly
      enabled for :kw:`format` validation.

As of ``draft2019-09`` however, the opt-out by default behavior
mentioned here is now *required* for all validators.

Difficult as this may sound for new users, at this point it at least
means they should expect the same behavior that has always been
implemented here, across any other implementation they encounter.

.. seealso::

    `Draft 2019-09's release notes on format <https://json-schema.org/draft/2019-09/release-notes.html#format-vocabulary>`_

        for upstream details on the behavior of format and how it has changed
        in ``draft2019-09``

    `validating formats`

        for details on how to enable format validation

    `jsonschema.FormatChecker`

        the object which implements format validation


Can jsonschema be used to validate YAML, TOML, etc.?
----------------------------------------------------

Like most JSON Schema implementations, `jsonschema` doesn't actually deal directly with JSON at all (other than in relation to the :kw:`$ref` keyword, elaborated on below).

In other words as far as this library is concerned, schemas and instances are simply runtime Python objects.
The JSON object ``{}`` is simply the Python `dict` ``{}``, and a JSON Schema like ``{"type": "object", {"properties": {}}}`` is really an assertion about particular Python objects and their keys.

.. note::

   The :kw:`$ref` keyword is a single notable exception.

   Specifically, in the case where `jsonschema` is asked to resolve a remote reference, it has no choice but to assume that the remote reference is serialized as JSON, and to deserialize it using the `json` module.

   One cannot today therefore reference some remote piece of YAML and have it deserialized into Python objects by this library without doing some additional work.
   See `Resolving References to Schemas Written in YAML <referencing:Resolving References to Schemas Written in YAML>` for details.

In practice what this means for JSON-like formats like YAML and TOML is that indeed one can generally schematize and then validate them exactly as if they were JSON by simply first deserializing them using libraries like ``PyYAML`` or the like, and passing the resulting Python objects into functions within this library.

Beware however that there are cases where the behavior of the JSON Schema specification itself is only well-defined within the data model of JSON itself, and therefore only for Python objects that could have "in theory" come from JSON.
As an example, JSON supports only string-valued keys, whereas YAML supports additional types.
The JSON Schema specification does not deal with how to apply the :kw:`patternProperties` keyword to non-string properties.
The behavior of this library is therefore similarly not defined when presented with Python objects of this form, which could never have come from JSON.
In such cases one is recommended to first pre-process the data such that the resulting behavior is well-defined.
In the previous example, if the desired behavior is to transparently coerce numeric properties to strings, as Javascript might, then do the conversion explicitly before passing data to this library.


Why doesn't my schema's default property set the default on my instance?
------------------------------------------------------------------------

The basic answer is that the specification does not require that
:kw:`default` actually do anything.

For an inkling as to *why* it doesn't actually do anything, consider
that none of the other keywords modify the instance either. More
importantly, having :kw:`default` modify the instance can produce
quite peculiar things. It's perfectly valid (and perhaps even useful)
to have a default that is not valid under the schema it lives in! So an
instance modified by the default would pass validation the first time,
but fail the second!

Still, filling in defaults is a thing that is useful. `jsonschema`
allows you to `define your own validator classes and callables
<creating>`, so you can easily create an `jsonschema.protocols.Validator`
that does do default setting. Here's some code to get you started. (In
this code, we add the default properties to each object *before* the
properties are validated, so the default values themselves will need to
be valid under the schema.)

    .. testcode::

        from jsonschema import Draft202012Validator, validators


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


        DefaultValidatingValidator = extend_with_default(Draft202012Validator)


        # Example usage:
        obj = {}
        schema = {'properties': {'foo': {'default': 'bar'}}}
        # Note jsonschema.validate(obj, schema, cls=DefaultValidatingValidator)
        # will not work because the metaschema contains `default` keywords.
        DefaultValidatingValidator(schema).validate(obj)
        assert obj == {'foo': 'bar'}


See the above-linked document for more info on how this works,
but basically, it just extends the :kw:`properties` keyword on a
`jsonschema.validators.Draft202012Validator` to then go ahead and update
all the defaults.

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

    .. testcode::

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
        DefaultValidatingValidator(schema).validate(obj)
        assert obj == {'outer-object': {'inner-object': 'INNER-DEFAULT'}}

    ...but if you don't provide a default value for your object, then
    it won't be instantiated at all, much less populated with default
    properties.

    .. testcode::

        del schema["properties"]["outer-object"]["default"]
        obj2 = {}
        DefaultValidatingValidator(schema).validate(obj2)
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

    * the exact wording and contents of error messages; typical reasons
      to rely on this seem to involve downstream tests in packages using
      `jsonschema`. These use cases are encouraged to use the extensive
      introspection provided in `jsonschema.exceptions.ValidationError`\s
      instead to make meaningful assertions about what failed rather than
      relying on *how* what failed is explained to a human.

    * the order in which validation errors are returned or raised

    * the contents of the ``jsonschema.tests`` package

    * the contents of the ``jsonschema.benchmarks`` package

    * the specific non-zero error codes presented by the command line
      interface

    * the exact representation of errors presented by the command line
      interface, other than that errors represented by the plain outputter
      will be reported one per line

    * anything marked private

With the exception of the last two of those, flippant changes are
avoided, but changes can and will be made if there is improvement to be
had. Feel free to open an issue ticket if there is a specific issue or
question worth raising.
