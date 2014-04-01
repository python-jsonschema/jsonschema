==========================
Frequently Asked Questions
==========================


Why doesn't my schema that has a default property actually set the default on my instance?
------------------------------------------------------------------------------------------

The basic answer is that the specification does not require that
:validator:`default` actually do anything.

For an inkling as to *why* it doesn't actually do anything, consider that none
of the other validators modify the instance either. More importantly, having
:validator:`default` modify the instance can produce quite peculiar things.
It's perfectly valid (and perhaps even useful) to have a default that is not
valid under the schema it lives in! So an instance modified by the default
would pass validation the first time, but fail the second!

Still, filling in defaults is a thing that is useful. :mod:`jsonschema` allows
you to :doc:`define your own validators <creating>`, so you can easily create a
:class:`IValidator` that does do default setting. Here's some code to get you
started:

    .. code-block:: python

        from jsonschema import Draft4Validator, validators


        def extend_with_default(validator_class):
            validate_properties = validator_class.VALIDATORS["properties"]

            def set_defaults(validator, properties, instance, schema):
                for error in validate_properties(
                    validator, properties, instance, schema,
                ):
                    yield error

                for property, subschema in properties.iteritems():
                    if "default" in subschema:
                        instance.setdefault(property, subschema["default"])

            return validators.extend(
                validator_class, {"properties" : set_defaults},
            )


        DefaultValidatingDraft4Validator = extend_with_default(Draft4Validator)


        # Example usage:
        obj = {}
        schema = {'properties': {'foo': {'default': 'bar'}}}
        # Note jsonschem.validate(obj, schema, cls=DefaultValidatingDraft4Validator)
        # will not work because the metaschema contains `default` directives.
        DefaultValidatingDraft4Validator(schema).validate(obj)
        assert obj == {'foo': 'bar'}


See the above-linked document for more info on how this works, but basically,
it just extends the :validator:`properties` validator on a
:class:`Draft4Validator` to then go ahead and update all the defaults.

If you're interested in a more interesting solution to a larger class of these
types of transformations, keep an eye on `Seep
<https://github.com/Julian/Seep>`_, which is an experimental data
transformation and extraction library written on top of :mod:`jsonschema`.


How do jsonschema version numbers work?
---------------------------------------

``jsonschema`` tries to follow the `Semantic Versioning <http://semver.org/>`_
specification.

This means broadly that no backwards-incompatible changes should be made in
minor releases (and certainly not in dot releases).

The full picture requires defining what constitutes a backwards-incompatible
change.

The following are simple examples of things considered public API, and
therefore should *not* be changed without bumping a major version number:

    * module names and contents, when not marked private by Python convention
      (a single leading underscore)

    * function and object signature (parameter order and name)

The following are *not* considered public API and may change without notice:

    * the exact wording and contents of error messages; typical
      reasons to do this seem to involve unit tests. API users are
      encouraged to use the extensive introspection provided in
      :class:`~jsonschema.exceptions.ValidationError`\s instead to make
      meaningful assertions about what failed.

    * the order in which validation errors are returned or raised

    * anything marked private

With the exception of the last of those, flippant changes are avoided, but
changes can and will be made if there is improvement to be had. Feel free to
open an issue ticket if there is a specific issue or question worth raising.
