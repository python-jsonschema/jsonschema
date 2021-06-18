from fractions import Fraction
import re

from jsonschema._utils import (
    ensure_list,
    equal,
    extras_msg,
    find_additional_properties,
    find_evaluated_item_indexes_by_schema,
    types_msg,
    unbool,
    uniq,
)
from jsonschema.exceptions import FormatError, ValidationError


def patternProperties(validator, patternProperties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for pattern, subschema in patternProperties.items():
        for k, v in instance.items():
            if re.search(pattern, k):
                for error in validator.descend(
                    v, subschema, path=k, schema_path=pattern,
                ):
                    yield error


def propertyNames(validator, propertyNames, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for property in instance:
        for error in validator.descend(
            instance=property,
            schema=propertyNames,
        ):
            yield error


def additionalProperties(validator, aP, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    extras = set(find_additional_properties(instance, schema))

    if validator.is_type(aP, "object"):
        for extra in extras:
            for error in validator.descend(instance[extra], aP, path=extra):
                yield error
    elif not aP and extras:
        if "patternProperties" in schema:
            patterns = sorted(schema["patternProperties"])
            if len(extras) == 1:
                verb = "does"
            else:
                verb = "do"
            error = "%s %s not match any of the regexes: %s" % (
                ", ".join(map(repr, sorted(extras))),
                verb,
                ", ".join(map(repr, patterns)),
            )
            yield ValidationError(error)
        else:
            error = "Additional properties are not allowed (%s %s unexpected)"
            yield ValidationError(error % extras_msg(extras))


def items(validator, items, instance, schema):
    if not validator.is_type(instance, "array"):
        return

    if validator.is_type(items, "boolean") and 'prefixItems' in schema:
        if not items:
            if len(instance) > len(schema['prefixItems']):
                yield ValidationError("%r has more items than defined in prefixItems" % instance)
            else:
                for error in validator.descend(instance, {'prefixItems': schema['prefixItems']}, path='items__prefixItems'):
                    yield error
    else:
        if 'prefixItems' in schema:
            for error in validator.descend(instance, {'prefixItems': schema['prefixItems']}, path='items__prefixItems'):
                yield error

            # Remove evaluated prefixItems indexes
            del instance[0:len(schema['prefixItems'])]

        for index, item in enumerate(instance):
            for error in validator.descend(item, items, path=index):
                yield error


def additionalItems(validator, aI, instance, schema):
    if (
        not validator.is_type(instance, "array") or
        validator.is_type(schema.get("items", {}), "object")
    ):
        return

    len_items = len(schema.get("items", []))
    if validator.is_type(aI, "object"):
        for index, item in enumerate(instance[len_items:], start=len_items):
            for error in validator.descend(item, aI, path=index):
                yield error
    elif not aI and len(instance) > len(schema.get("items", [])):
        error = "Additional items are not allowed (%s %s unexpected)"
        yield ValidationError(
            error %
            extras_msg(instance[len(schema.get("items", [])):])
        )


def const(validator, const, instance, schema):
    if not equal(instance, const):
        yield ValidationError("%r was expected" % (const,))


def contains(validator, contains, instance, schema):
    if not validator.is_type(instance, "array"):
        return

    min_contains = max_contains = None

    if 'minContains' in schema:
        min_contains = schema['minContains']
        if not validator.is_type(min_contains, "integer"):
            yield ValidationError(
                "minContains of %r in not valid under the given schema" % (min_contains,)
            )
            return

    if 'maxContains' in schema:
        max_contains = schema['maxContains']
        if not validator.is_type(max_contains, "integer"):
            yield ValidationError(
                "maxContains of %r is not valid under the given schema" % (instance,)
            )
            return

    # minContains set to 0 will ignore contains
    if min_contains == 0:
        return

    matches = len(list(filter(lambda x: x, [validator.is_valid(element, contains) for element in instance])))

    # default contains behavior
    if not matches:
        yield ValidationError(
            "None of %r are valid under the given schema" % (instance,)
        )
        return

    if min_contains and max_contains is None:
        if matches < min_contains:
            yield ValidationError(
                "Invalid number or matches of %r under the given schema, expected min %d, got %d" % (
                    instance, min_contains, matches
                )
            )
        return

    if min_contains is None and max_contains:
        if matches > max_contains:
            yield ValidationError(
                "Invalid number or matches of %r under the given schema, expected max %d, got %d" % (
                    instance, max_contains, matches
                )
            )
        return

    if min_contains and max_contains:
        if matches < min_contains or matches > max_contains:
            yield ValidationError(
                "Invalid number or matches of %r under the given schema, expected min %d and max %d, got %d" % (
                    instance, min_contains, max_contains, matches
                )
            )
        return


def exclusiveMinimum(validator, minimum, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if instance <= minimum:
        yield ValidationError(
            "%r is less than or equal to the minimum of %r" % (
                instance, minimum,
            ),
        )


def exclusiveMaximum(validator, maximum, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if instance >= maximum:
        yield ValidationError(
            "%r is greater than or equal to the maximum of %r" % (
                instance, maximum,
            ),
        )


def minimum(validator, minimum, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if instance < minimum:
        yield ValidationError(
            "%r is less than the minimum of %r" % (instance, minimum)
        )


def maximum(validator, maximum, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if instance > maximum:
        yield ValidationError(
            "%r is greater than the maximum of %r" % (instance, maximum)
        )


def multipleOf(validator, dB, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if isinstance(dB, float):
        quotient = instance / dB
        try:
            failed = int(quotient) != quotient
        except OverflowError:
            # When `instance` is large and `dB` is less than one,
            # quotient can overflow to infinity; and then casting to int
            # raises an error.
            #
            # In this case we fall back to Fraction logic, which is
            # exact and cannot overflow.  The performance is also
            # acceptable: we try the fast all-float option first, and
            # we know that fraction(dB) can have at most a few hundred
            # digits in each part.  The worst-case slowdown is therefore
            # for already-slow enormous integers or Decimals.
            failed = (Fraction(instance) / Fraction(dB)).denominator != 1
    else:
        failed = instance % dB

    if failed:
        yield ValidationError("%r is not a multiple of %r" % (instance, dB))


def minItems(validator, mI, instance, schema):
    if validator.is_type(instance, "array") and len(instance) < mI:
        yield ValidationError("%r is too short" % (instance,))


def maxItems(validator, mI, instance, schema):
    if validator.is_type(instance, "array") and len(instance) > mI:
        yield ValidationError("%r is too long" % (instance,))


def uniqueItems(validator, uI, instance, schema):
    if (
        uI and
        validator.is_type(instance, "array") and
        not uniq(instance)
    ):
        yield ValidationError("%r has non-unique elements" % (instance,))


def pattern(validator, patrn, instance, schema):
    if (
        validator.is_type(instance, "string") and
        not re.search(patrn, instance)
    ):
        yield ValidationError("%r does not match %r" % (instance, patrn))


def format(validator, format, instance, schema):
    if validator.format_checker is not None:
        try:
            validator.format_checker.check(instance, format)
        except FormatError as error:
            yield ValidationError(error.message, cause=error.cause)


def minLength(validator, mL, instance, schema):
    if validator.is_type(instance, "string") and len(instance) < mL:
        yield ValidationError("%r is too short" % (instance,))


def maxLength(validator, mL, instance, schema):
    if validator.is_type(instance, "string") and len(instance) > mL:
        yield ValidationError("%r is too long" % (instance,))


def dependencies(validator, dependencies, instance, schema):
    """
    The dependencies keyword has been deprecated since draft 2019-09 and has been split into dependentRequired
    and dependentSchemas.
    """
    if not validator.is_type(instance, "object"):
        return

    for property, dependency in dependencies.items():
        if property not in instance:
            continue

        if validator.is_type(dependency, "array"):
            for each in dependency:
                if each not in instance:
                    message = "%r is a dependency of %r"
                    yield ValidationError(message % (each, property))
        else:
            for error in validator.descend(
                instance, dependency, schema_path=property,
            ):
                yield error


def dependentRequired(validator, dependentRequired, instance, schema):
    """
    Split from dependencies
    """
    if not validator.is_type(instance, "object"):
        return

    for property, dependency in dependentRequired.items():
        if property not in instance:
            continue

        for each in dependency:
            if each not in instance:
                message = "%r is a dependency of %r"
                yield ValidationError(message % (each, property))


def dependentSchemas(validator, dependentSchemas, instance, schema):
    """
    Split from dependencies
    """
    if not validator.is_type(instance, "object"):
        return

    for property, dependency in dependentSchemas.items():
        if property not in instance:
            continue

        for error in validator.descend(
                instance, dependency, schema_path=property,
        ):
            yield error


def enum(validator, enums, instance, schema):
    if instance == 0 or instance == 1:
        unbooled = unbool(instance)
        if all(unbooled != unbool(each) for each in enums):
            yield ValidationError("%r is not one of %r" % (instance, enums))
    elif instance not in enums:
        yield ValidationError("%r is not one of %r" % (instance, enums))


def ref(validator, ref, instance, schema):
    resolve = getattr(validator.resolver, "resolve", None)
    if resolve is None:
        with validator.resolver.resolving(ref) as resolved:
            for error in validator.descend(instance, resolved):
                yield error
    else:
        scope, resolved = validator.resolver.resolve(ref)
        validator.resolver.push_scope(scope)

        try:
            for error in validator.descend(instance, resolved):
                yield error
        finally:
            validator.resolver.pop_scope()


def type(validator, types, instance, schema):
    types = ensure_list(types)

    if not any(validator.is_type(instance, type) for type in types):
        yield ValidationError(types_msg(instance, types))


def properties(validator, properties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for property, subschema in properties.items():
        if property in instance:
            for error in validator.descend(
                instance[property],
                subschema,
                path=property,
                schema_path=property,
            ):
                yield error


def required(validator, required, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            yield ValidationError("%r is a required property" % property)


def minProperties(validator, mP, instance, schema):
    if validator.is_type(instance, "object") and len(instance) < mP:
        yield ValidationError(
            "%r does not have enough properties" % (instance,)
        )


def maxProperties(validator, mP, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    if validator.is_type(instance, "object") and len(instance) > mP:
        yield ValidationError("%r has too many properties" % (instance,))


def allOf(validator, allOf, instance, schema):
    for index, subschema in enumerate(allOf):
        for error in validator.descend(instance, subschema, schema_path=index):
            yield error


def anyOf(validator, anyOf, instance, schema):
    all_errors = []
    for index, subschema in enumerate(anyOf):
        errs = list(validator.descend(instance, subschema, schema_path=index))
        if not errs:
            break
        all_errors.extend(errs)
    else:
        yield ValidationError(
            "%r is not valid under any of the given schemas" % (instance,),
            context=all_errors,
        )


def oneOf(validator, oneOf, instance, schema):
    subschemas = enumerate(oneOf)
    all_errors = []
    for index, subschema in subschemas:
        errs = list(validator.descend(instance, subschema, schema_path=index))
        if not errs:
            first_valid = subschema
            break
        all_errors.extend(errs)
    else:
        yield ValidationError(
            "%r is not valid under any of the given schemas" % (instance,),
            context=all_errors,
        )

    more_valid = [s for i, s in subschemas if validator.is_valid(instance, s)]
    if more_valid:
        more_valid.append(first_valid)
        reprs = ", ".join(repr(schema) for schema in more_valid)
        yield ValidationError(
            "%r is valid under each of %s" % (instance, reprs)
        )


def not_(validator, not_schema, instance, schema):
    if validator.is_valid(instance, not_schema):
        yield ValidationError(
            "%r is not allowed for %r" % (not_schema, instance)
        )


def if_(validator, if_schema, instance, schema):
    if validator.is_valid(instance, if_schema):
        if u"then" in schema:
            then = schema[u"then"]
            for error in validator.descend(instance, then, schema_path="then"):
                yield error
    elif u"else" in schema:
        else_ = schema[u"else"]
        for error in validator.descend(instance, else_, schema_path="else"):
            yield error


def unevaluatedItems(validator, unevaluatedItems, instance, schema):
    if not validator.is_type(instance, "array"):
        return

    if validator.is_type(unevaluatedItems, "boolean"):
        if unevaluatedItems:
            return

    evaluated_item_indexes = find_evaluated_item_indexes_by_schema(validator, instance, schema)
    for k, v in enumerate(instance):
        if k not in evaluated_item_indexes:
            for error in validator.descend(v, unevaluatedItems, schema_path="unevaluatedItems"):
                yield error


def prefixItems(validator, prefixItems, instance, schema):
    if not validator.is_type(instance, "array"):
        return

    for k, v in enumerate(instance):
        if k < len(prefixItems):
            for error in validator.descend(v, prefixItems[k], schema_path="prefixItems"):
                yield error
