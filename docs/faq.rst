==========================
Frequently Asked Questions
==========================

**Why doesn't my schema that has a default property actually set
the default on my instance?**

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


See the above-linked document for more info on how this works, but basically,
it just extends the :validator:`properties` validator on a
:class:`Draft4Validator` to then go ahed and update all the defaults.

If you're interested in a more interesting solution to a larger class of these
types of transformations, keep an eye on `Seep
<https://github.com/Julian/Seep>`_, which is an experimental data
transformation and extraction library written on top of :mod:`jsonschema`.
