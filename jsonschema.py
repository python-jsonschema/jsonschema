from __future__ import division, with_statement

import operator
import re
import sys
import types


# 2.5 support
try:
    next
except NameError:
    _none = object()
    def next(iterator, default=_none):
        try:
            return iterator.next()
        except StopIteration:
            if default is not _none:
                return default
            raise

_PYTYPES = {
        u"array" : list, u"boolean" : bool, u"integer" : int,
        u"null" : types.NoneType, u"number" : (int, float),
        u"object" : dict, u"string" : basestring,
}

_PYTYPES[u"any"] = tuple(_PYTYPES.values())


class SchemaError(Exception):
    pass


class ValidationError(Exception):
    pass


class Validator(object):

    # required and dependencies are handled in validate_properties
    # exclusive Minium and Maximum are handled in validate_minimum
    SKIPPED = set([
        u"dependencies", u"required", u"exclusiveMinimum", u"exclusiveMaximum"
    ])

    def _error(self, msg):
        raise ValidationError(msg)

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

            validator = getattr(self, u"validate_%s" % (k,), None)

            if validator is None:
                raise SchemaError(
                    u"'%s' is not a known schema property" % (k,)
                )

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

            elif isinstance(type, basestring):
                type = _PYTYPES.get(type)

                if type is None:
                    raise SchemaError(u"'%s' is not a known type" % (type,))

                # isinstance(a_bool, int) will make us even sadder here, so
                # let's be even dirtier than we would otherwise be.

                elif (
                    isinstance(instance, type) and
                    (not isinstance(instance, bool) or
                     type is bool or types == [u"any"])
                ):
                        return
        else:
            self._error(u"'%s' is not of type %s" % (instance, types))

    def validate_properties(self, properties, instance, schema):
        for property, subschema in properties.iteritems():
            if property in instance:
                dependencies = _(subschema.get(u"dependencies", []))
                if isinstance(dependencies, dict):
                    self.validate(instance, dependencies)
                else:
                    missing = (d for d in dependencies if d not in instance)
                    first = next(missing, None)
                    if first is not None:
                        self._error(
                            u"'%s' is a dependency of '%s'" % (first, property)
                        )

                self.validate(instance[property], subschema)
            elif subschema.get(u"required", False):
                self._error(u"'%s' is a required property" % (property,))

    def validate_patternProperties(self, patternProperties, instance, schema):
        for pattern, subschema in patternProperties.iteritems():
            for k, v in instance.iteritems():
                if re.match(pattern, k):
                    self.validate(v, subschema)

    def validate_additionalProperties(self, aP, instance, schema):
        # no viewkeys in <2.7, and pypy seems to fail on vk - vk anyhow, so...
        extras = set(instance) - set(schema.get(u"properties", {}))

        if isinstance(aP, dict):
            for extra in extras:
                self.validate(instance[extra], aP)
        elif not aP and extras:
            self._error(u"Additional properties are not allowed")

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
            self._error(u"Additional items are not allowed")

    def validate_minimum(self, minimum, instance, schema):
        if schema.get(u"exclusiveMinimum", False):
            failed = instance <= minimum
            cmp = u"less than or equal to"
        else:
            failed = instance < minimum
            cmp = u"less than"

        if failed:
            self._error(
                u"%s is %s the minimum of %s" % (instance, cmp, minimum)
            )

    def validate_maximum(self, maximum, instance, schema):
        if schema.get(u"exclusiveMaximum", False):
            failed = instance >= maximum
            cmp = u"greater than or equal to"
        else:
            failed = instance > maximum
            cmp = u"greater than"

        if failed:
            self._error(
                u"%s is %s the maximum of %s" % (instance, cmp, maximum)
            )

    def validate_minItems(self, mI, instance, schema):
        if len(instance) < mI:
            self._error(u"'%s' is too short" % (instance,))

    def validate_maxItems(self, mI, instance, schema):
        if len(instance) > mI:
            self._error(u"'%s' is too long" % (instance,))

    def validate_pattern(self, pattern, instance, schema):
        if not re.match(pattern, instance):
            self._error(u"'%s' does not match '%s'" % (instance, pattern))

    def validate_minLength(self, mL, instance, schema):
        if len(instance) < mL:
            self._error(u"'%s' is too short" % (instance,))

    def validate_maxLength(self, mL, instance, schema):
        if len(instance) > mL:
            self._error(u"'%s' is too long" % (instance,))

    def validate_enum(self, enums, instance, schema):
        if instance not in enums:
            self._error(u"'%s' is not one of %s" % (instance, enums))

    def validate_divisibleBy(self, dB, instance, schema):
        if isinstance(dB, float):
            failed = dB - instance % dB > .0000000001
        else:
            failed = instance % dB

        if failed:
            self._error(u"%s is not divisible by %s" % (instance, dB))


def _(thing):
    if isinstance(thing, basestring):
        return [thing]
    return thing


_default_validator = Validator()
validate = _default_validator.validate
