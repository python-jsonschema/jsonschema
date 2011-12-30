from __future__ import unicode_literals

import numbers
import re
import types


_PYTYPES = {
        "array" : list, "boolean" : bool, "integer" : int,
        "null" : types.NoneType, "number" : numbers.Number,
        "object" : dict, "string" : unicode
}

_PYTYPES["any"] = tuple(_PYTYPES.values())


class SchemaError(Exception):
    pass


class ValidationError(Exception):
    pass


class Validator(object):

    # required and dependencies are handled in validate_properties
    # exclusive Minium and Maximum are handled in validate_minimum
    SKIPPED = {
        "dependencies", "required", "exclusiveMinimum", "exclusiveMaximum"
    }

    def is_valid(self, instance, schema):
        try:
            self.validate(instance, schema)
            return True
        except ValidationError:
            return False

    def validate(self, instance, schema):
        for k, v in schema.iteritems():
            if k in self.SKIPPED:
                continue

            validator = getattr(self, "validate_%s" % k, None)

            if validator is None:
                raise SchemaError("'%s' is not a known schema property" % k)

            validator(v, instance, schema)

    def validate_type(self, types, instance, schema):
        types = _(types)

        for type in types:
            if (
                isinstance(type, dict) and
                isinstance(instance, dict) and
                self.is_valid(instance, type)
            ):
                return

            elif isinstance(type, unicode):
                type = _PYTYPES.get(type)

                if type is None:
                    raise SchemaError("'%s' is not a known type" % type)

                # isinstance(a_bool, int) will make us even sadder here, so
                # let's be even dirtier than we would otherwise be.

                elif (
                    isinstance(instance, type) and
                    (not isinstance(instance, bool) or
                     type is bool or types == ["any"])
                ):
                        return
        else:
            raise ValidationError("'%s' is not of type %s" % (instance, types))

    def validate_properties(self, properties, instance, schema):
        for property, subschema in properties.iteritems():
            if property in instance:
                dependencies = _(subschema.get("dependencies", []))
                if isinstance(dependencies, dict):
                    self.validate(instance, dependencies)
                else:
                    missing = (d for d in dependencies if d not in instance)
                    first = next(missing, None)
                    if first is not None:
                        raise ValidationError(
                            "'%s' is a dependency of '%s'" % (first, property)
                        )

                self.validate(instance[property], subschema)
            elif subschema.get("required", False):
                raise ValidationError("'%s' is a required property" % property)

    def validate_patternProperties(self, patternProperties, instance, schema):
        for pattern, subschema in patternProperties.iteritems():
            for k, v in instance.iteritems():
                if re.match(pattern, k):
                    self.validate(v, subschema)

    def validate_additionalProperties(self, aP, instance, schema):
        extras = instance.viewkeys() - schema.get("properties", {}).viewkeys()

        if isinstance(aP, dict):
            for extra in extras:
                self.validate(instance[extra], aP)
        elif not aP and extras:
            raise ValidationError("Additional properties are not allowed")

    def validate_items(self, items, instance, schema):
        if isinstance(items, dict):
            for item in instance:
                self.validate(item, items)
        else:
            for item, subschema in zip(instance, items):
                self.validate(item, subschema)

    def validate_additionalItems(self, aI, instance, schema):
        if isinstance(aI, dict):
            for item in instance[len(schema):]:
                self.validate(item, aI)
        elif not aI and len(instance) > len(schema):
            raise ValidationError("Additional items are not allowed")

    def validate_minimum(self, minimum, instance, schema):
        if schema.get("exclusiveMinimum", False):
            failed = instance <= minimum
            cmp = "less than or equal to"
        else:
            failed = instance < minimum
            cmp = "less than"

        if failed:
            raise ValidationError(
                "%s is %s the minimum (%s)" % (instance, cmp, minimum)
            )

    def validate_maximum(self, maximum, instance, schema):
        if schema.get("exclusiveMaximum", False):
            failed = instance >= maximum
            cmp = "greater than or equal to"
        else:
            failed = instance > maximum
            cmp = "greater than"

        if failed:
            raise ValidationError(
                "%s is %s the maximum (%s)" % (instance, cmp, maximum)
            )

    def validate_minItems(self, mI, instance, schema):
        if len(instance) < mI:
            raise ValidationError("'%s' is too short" % (instance,))

    def validate_maxItems(self, mI, instance, schema):
        if len(instance) > mI:
            raise ValidationError("'%s' is too long" % (instance,))

    def validate_minLength(self, mL, instance, schema):
        if len(instance) < mL:
            raise ValidationError("'%s' is too short" % (instance,))

    def validate_maxLength(self, mL, instance, schema):
        if len(instance) > mL:
            raise ValidationError("'%s' is too long" % (instance,))


def _(thing):
    if isinstance(thing, unicode):
        return [thing]
    return thing


_default_validator = Validator()
validate = _default_validator.validate
