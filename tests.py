from __future__ import with_statement
from decimal import Decimal
from functools import wraps
import warnings

import sys

if (sys.version_info[0], sys.version_info[1]) < (2, 7):  # pragma: no cover
    import unittest2 as unittest
else:
    import unittest

from jsonschema import SchemaError, ValidationError, validate


class ParametrizedTestCase(type):
    """
    A (deliberately naive & specialized) parametrized test.

    """

    def __new__(cls, name, bases, attrs):
        attr = {}

        for k, v in attrs.iteritems():
            parameters = getattr(v, "_parameters", None)

            if parameters is not None:
                for parameter in parameters:
                    parametrized_name, args = parameter[0], parameter[1:]
                    fn = partial(v, *args)

                    names = ["test", k]
                    if parametrized_name:
                        names.append(parametrized_name)

                    fn.__name__ = "_".join(names)
                    attr[fn.__name__] = fn
            else:
                attr[k] = v

        return super(ParametrizedTestCase, cls).__new__(cls, name, bases, attr)


def parametrized(*runs):
    def parametrized_test(fn):
        fn._parameters = runs
        return fn
    return parametrized_test


def partial(fn, *args, **kwargs):
    """
    ``functools.partial`` for methods (suitable for binding).

    """

    @wraps(fn)
    def _partial(self):
        return fn(self, *args, **kwargs)
    return _partial


def validation_test(schema=(), initkwargs=(), **kwschema):
    schema = dict(schema, **kwschema)
    initkwargs = dict(initkwargs)

    def _validation_test(self, expected, instance):
        if expected == "valid":
            validate(instance, schema, **initkwargs)
        elif expected == "invalid":
            with self.assertRaises(ValidationError):
                validate(instance, schema, **initkwargs)
        else:  # pragma: no cover
            raise ValueError("You spelled something wrong.")

    return _validation_test


class TestValidate(unittest.TestCase):

    __metaclass__ = ParametrizedTestCase

    integer = parametrized(
        ("integer", "valid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", u"foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=u"integer"))

    number = parametrized(
        ("integer", "valid", 1),
        ("number", "valid", 1.1),
        ("string", "invalid", u"foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=u"number"))

    string = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("unicode", "valid", u"foo"),
        ("str", "valid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=u"string"))

    object = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", u"foo"),
        ("object", "valid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=u"object"))

    array = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", u"foo"),
        ("object", "invalid", {}),
        ("array", "valid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=u"array"))

    boolean = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", u"foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("true", "valid", True),
        ("false", "valid", False),
        ("null", "invalid", None),
    )(validation_test(type=u"boolean"))

    null = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", u"foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "valid", None),
    )(validation_test(type=u"null"))

    any = parametrized(
        ("integer", "valid", 1),
        ("number", "valid", 1.1),
        ("string", "valid", u"foo"),
        ("object", "valid", {}),
        ("array", "valid", []),
        ("boolean", "valid", True),
        ("null", "valid", None),
    )(validation_test(type=u"any"))

    multiple_types = parametrized(
        ("integer", "valid", 1),
        ("string", "valid", u"foo"),
        ("number", "invalid", 1.1),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=[u"integer", u"string"]))

    multiple_types_schema = parametrized(
        ("match", "valid", [1, 2]),
        ("other_match", "valid", {u"foo" : u"bar"}),
        ("number", "invalid", 1.1),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=[u"array", {u"type" : u"object"}]))

    multiple_types_subschema = parametrized(
        ("integer", "valid", 1),
        ("object_right_type", "valid", {u"foo" : None}),
        ("object_wrong_type", "invalid", {u"foo" : 1}),
        ("object_another_wrong_type", "invalid", {u"foo" : 1.1}),
    )(validation_test(
        type=[u"integer", {"properties" : {u"foo" : {u"type" : u"null"}}}]
    ))

    properties = parametrized(
        ("", "valid", {u"foo" : 1, u"bar" : u"baz"}),
        ("extra_property", "valid",
         {u"foo" : 1, u"bar" : u"baz", u"quux" : 42}),
        ("invalid_type", "invalid", {u"foo" : 1, u"bar" : []}),
    )(validation_test(
        {
            "properties" : {
                u"foo" : {u"type" : u"number"},
                u"bar" : {u"type" : u"string"},
            }
        }
    ))

    patternProperties = parametrized(
        ("single_match", "valid", {u"foo" : 1}),
        ("multiple_match", "valid", {u"foo" : 1, u"fah" : 2, u"bar" : u"baz"}),
        ("single_mismatch", "invalid", {u"foo" : u"bar"}),
        ("multiple_mismatch", "invalid", {u"foo" : 1, u"fah" : u"bar"}),
    )(validation_test(patternProperties={u"f.*" : {u"type" : u"integer"}}))

    multiple_patternProperties = parametrized(
        ("match", "valid", {u"a" : 21}),
        ("other_match", "valid", {u"aaaa" : 18}),
        ("multiple_match", "valid", {u"a" : 21, u"aaaa" : 18}),
        ("mismatch", "invalid", {u"aaa" : u"bar"}),
        ("other_mismatch", "invalid", {u"aaaa" : 31}),
        ("multiple_mismatch", "invalid", {u"aaa" : u"foo", u"aaaa" : 32}),
    )(validation_test(patternProperties={
        u"a*" : {u"type" : u"integer"},
        u"aaa*" : {u"maximum" : 20},
        }
    ))

    def test_additionalProperties_allowed_by_default(self):
        schema = {
            "properties" : {
                u"foo" : {u"type" : u"number"},
                u"bar" : {u"type" : u"string"},
            }
        }
        validate({u"foo" : 1, u"bar" : u"baz", u"quux" : False}, schema)

    @parametrized(
        ("", False),
        ("schema", {u"type" : u"boolean"}),
    )
    def additionalProperties(self, aP):
        schema = {
            "properties" : {
                u"foo" : {u"type" : u"number"},
                u"bar" : {u"type" : u"string"},
            },

            "additionalProperties" : aP,
        }

        with self.assertRaises(ValidationError):
            validate({u"foo" : 1, u"bar" : u"baz", u"quux" : u"boom"}, schema)

    items = parametrized(
        ("", "valid", [1, 2, 3]),
        ("wrong_type", "invalid", [1, u"x"]),
    )(validation_test(items={u"type" : u"integer"}))

    items_tuple_typing = parametrized(
        ("", "valid", [1, u"foo"]),
        ("wrong_type", "invalid", [u"foo", 1])
    )(validation_test(items=[{u"type" : u"integer"}, {u"type" : u"string"}]))

    def test_additionalItems_allowed_by_default(self):
        validate(
            [1, u"foo", False],
            {"items" : [{u"type" : u"integer"}, {u"type" : u"string"}]}
        )

    additionalItems = parametrized(
        ("no_additional", "valid", [1, u"foo"]),
        ("additional", "invalid", [1, u"foo", False]),
    )(validation_test({
        "items" : [{u"type" : u"integer"}, {u"type" : u"string"}],
        "additionalItems" : False,
    }))

    additionalItems_schema = parametrized(
        ("match", "valid", [1, u"foo", 3]),
        ("mismatch", "invalid", [1, u"foo", u"bar"]),
    )(validation_test({
        "items" : [{u"type" : u"integer"}, {u"type" : u"string"}],
        "additionalItems" : {u"type" : u"integer"},
    }))

    @parametrized(
        ("false_by_default", "valid", {}, {}),
        ("false_explicit", "valid", {u"required" : False}, {}),
        ("one", "valid", {u"required" : True}, {}),
        ("other", "invalid", {}, {u"required" : True}),
        ("both", "invalid", {u"required" : True}, {u"required" : True}),
    )
    def required(self, expect, foo, bar):
        schema = {
            u"properties" : {
                u"foo" : {u"type" : u"number"},
                u"bar" : {u"type" : u"string"},
            }
        }

        schema[u"properties"][u"foo"].update(foo)
        schema[u"properties"][u"bar"].update(bar)

        test = validation_test(schema)
        test(self, expect, {u"foo" : 1})

    dependencies = parametrized(
        ("neither", "valid", {}),
        ("nondependant", "valid", {u"foo" : 1}),
        ("with_dependency", "valid", {u"foo" : 1, u"bar" : 2}),
        ("missing_dependency", "invalid", {u"bar" : 2}),
    )(validation_test(properties={u"bar" : {u"dependencies" : u"foo"}}))

    multiple_dependencies = parametrized(
        ("neither", "valid", {}),
        ("nondependants", "valid", {u"foo" : 1, u"bar" : 2}),
        ("with_dependencies", "valid", {u"foo" : 1, u"bar" : 2, u"quux" : 3}),
        ("missing_dependency", "invalid", {u"foo" : 1, u"quux" : 2}),
        ("missing_other_dependency", "invalid", {u"bar" : 1, u"quux" : 2}),
        ("missing_both_dependencies", "invalid", {u"quux" : 1}),
    )(validation_test(
        properties={u"quux" : {u"dependencies" : [u"foo", u"bar"]}}
    ))

    multiple_dependencies_subschema = parametrized(
        ("", "valid", {u"foo" : 1, u"bar" : 2}),
        ("wrong_type", "invalid", {u"foo" : u"quux", u"bar" : 2}),
        ("wrong_type_other", "invalid", {u"foo" : 2, u"bar" : u"quux"}),
        ("wrong_type_both", "invalid", {u"foo" : u"quux", u"bar" : u"quux"}),
    )(validation_test(properties={
        u"bar" : {
            u"dependencies" : {
                "properties" : {
                    u"foo" : {u"type" : u"integer"},
                    u"bar" : {u"type" : u"integer"},
        }}}}))

    @parametrized(
        ("", "valid", {}, 2.6),
        ("fail", "invalid", {}, .6),
        ("exclusiveMinimum", "valid", {u"exclusiveMinimum" : True}, 1.2),
        ("exclusiveMinimum_fail", "invalid",
         {u"exclusiveMinimum" : True}, 1.1),
    )
    def minimum(self, expect, eM, instance):
        eM["minimum"] = 1.1
        test = validation_test(eM)
        test(self, expect, instance)

    @parametrized(
        ("", "valid", {}, 2.6),
        ("fail", "invalid", {}, 3.5),
        ("exclusiveMaximum", "valid", {u"exclusiveMaximum" : True}, 2.2),
        ("exclusiveMaximum_fail", "invalid",
         {u"exclusiveMaximum" : True}, 3.0),
    )
    def maximum(self, expect, eM, instance):
        eM["maximum"] = 3.0
        test = validation_test(eM)
        test(self, expect, instance)

    minItems = parametrized(
        ("exact", "valid", [1]),
        ("longer", "valid", [1, 2]),
        ("too_short", "invalid", []),
        ("ignores_strings", "valid", "a"),
    )(validation_test(minItems=1))

    maxItems = parametrized(
        ("exact", "valid", [1, 2]),
        ("shorter", "valid", [1]),
        ("empty", "valid", []),
        ("too_long", "invalid", [1, 2, 3]),
        ("ignores_strings", "valid", "aaaa"),
    )(validation_test(maxItems=2))

    pattern = parametrized(
        ("match", "valid", u"aaa"),
        ("mismatch", "invalid", u"ab"),
        ("ignores_other_stuff", "valid", True),
    )(validation_test(pattern=u"^a*$"))

    minLength = parametrized(
        ("", "valid", u"foo"),
        ("too_short", "invalid", u"f"),
        ("ignores_arrays", "valid", [1]),
    )(validation_test(minLength=2))

    maxLength = parametrized(
        ("", "valid", u"f"),
        ("too_long", "invalid", u"foo"),
        ("ignores_arrays", "valid", [1, 2, 3]),
    )(validation_test(maxLength=2))

    @parametrized(
        ("integer", "valid", 1, [1, 2, 3]),
        ("integer_fail", "invalid", 6, [1, 2, 3]),
        ("string", "valid", u"foo", [u"foo", u"bar"]),
        ("string_fail", "invalid", u"quux", [u"foo", u"bar"]),
        ("bool", "valid", True, [True]),
        ("bool_fail", "invalid", False, [True]),
        ("object", "valid", {u"foo" : u"bar"}, [{u"foo" : u"bar"}]),
        ("object_fail", "invalid", {u"foo" : u"bar"}, [{u"foo" : u"quux"}]),
    )
    def enum(self, expect, instance, enum):
        test = validation_test(enum=enum)
        test(self, expect, instance)

    @parametrized(
        ("int_by_int", "valid", 10, 2),
        ("int_by_int_fail", "invalid", 7, 2),
        ("number_by_number", "valid", 3.3, 1.1),
        ("number_by_number_fail", "invalid", 3.5, 1.1),
        ("number_by_number_small", "valid", .0075, .0001),
        ("number_by_number_small_fail", "invalid", .00751, .0001),
    )
    def divisibleBy(self, expect, instance, dB):
        test = validation_test(divisibleBy=dB)
        test(self, expect, instance)

    disallow = parametrized(
        ("", "valid", u"foo"),
        ("disallowed", "invalid", 1),
    )(validation_test(disallow=u"integer"))

    multiple_disallow = parametrized(
        ("", "valid", u"foo"),
        ("mismatch", "invalid", 1),
        ("other_mismatch", "invalid", True),
    )(validation_test(disallow=[u"integer", u"boolean"]))

    multiple_disallow_subschema = parametrized(
        ("match", "valid", 1),
        ("other_match", "valid", {u"foo" : 1}),
        ("mismatch", "invalid", u"foo"),
        ("other_mismatch", "invalid", {u"foo" : u"bar"}),
    )(validation_test(
        disallow=[u"string", {"properties" : {u"foo" : {u"type" : u"string"}}}]
    ))

    def test_stop_on_error(self):
        instance = [1, 2]

        schema = {
            u"disallow" : u"array",
            u"enum" : [[u"a", u"b", u"c"], [u"d", u"e", u"f"]],
            u"minItems" : 3
        }

        with self.assertRaises(ValidationError) as e:
            validate(instance, schema, stop_on_error=False)

        self.assertEqual(sorted(e.exception.errors), sorted([
            u"u'array' is disallowed for [1, 2]",
            u"[1, 2] is too short",
            u"[1, 2] is not one of [[u'a', u'b', u'c'], [u'd', u'e', u'f']]",
        ]))

    def test_unknown_type_error(self):
        with self.assertRaises(SchemaError):
            validate(1, {u"type" : u"foo"})

    @unittest.skipIf(
        sys.version_info[:2] == (2, 5),
        "Python 2.5 lacks catch_warnings, and I am lazy."
    )
    def test_unknown_type_warn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate(1, {u"type" : u"foo"}, unknown_type="warn")
        self.assertEqual(len(w), 1)

    def test_unknown_type_skip(self):
        validate(1, {u"type" : u"foo"}, unknown_type="skip")

    def test_unknown_property_error(self):
        with self.assertRaises(SchemaError):
            validate(1, {u"foo" : u"bar"})

    @unittest.skipIf(
        sys.version_info[:2] == (2, 5),
        "Python 2.5 lacks catch_warnings, and I am lazy."
    )
    def test_unknown_property_warn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate(1, {u"foo" : u"bar"}, unknown_property="warn")
        self.assertEqual(len(w), 1)

    def test_unknown_property_skip(self):
        validate(
            1,
            {u"foo" : u"foo", u"type" : u"integer"},
            unknown_property="skip"
        )

    decimal = parametrized(
        ("integer", "valid", 1),
        ("number", "valid", 1.1),
        ("decimal", "valid", Decimal(1) / Decimal(8)),
        ("string", "invalid", u"foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(
        initkwargs={"number_types" : (int, float, Decimal)},
        type=u"number")
    )

    # Test that only the types that are json-loaded validate (e.g. bytestrings)
