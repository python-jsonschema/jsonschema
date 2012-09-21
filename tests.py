from __future__ import unicode_literals
from decimal import Decimal
from functools import wraps
import sys
import warnings

if sys.version_info[:2] < (2, 7):  # pragma: no cover
    import unittest2 as unittest
else:
    import unittest


from jsonschema import (
    PY3, SchemaError, ValidationError, ErrorTree, Validator,
    iteritems, validate
)


if PY3:
    basestring = unicode = str


class ParametrizedTestCase(type):
    """
    A (deliberately naive & specialized) parametrized test.

    """

    def __new__(cls, name, bases, attrs):
        attr = {}

        for k, v in iteritems(attrs):
            parameters = getattr(v, "_parameters", None)

            if parameters is not None:
                for parameter in parameters:
                    parametrized_name, args = parameter[0], parameter[1:]
                    fn = partial(v, *args)

                    names = ["test", k]
                    if parametrized_name:
                        names.append(parametrized_name)

                    fn_name = "_".join(names)
                    if not PY3:
                        fn_name = fn_name.encode('utf8')
                    fn.__name__ = fn_name
                    attr[fn.__name__] = fn
            else:
                attr[k] = v

        if not PY3:
            name = name.encode('utf8')

        return super(ParametrizedTestCase, cls).__new__(cls, name, bases, attr)


# Inscrutable way to create metaclasses in a Python 2/3 compatible way
# See: http://mikewatkins.ca/2008/11/29/python-2-and-3-metaclasses/
ParameterizedTestCase = ParametrizedTestCase(
    'ParameterizedTestCase', (object,), {}
)


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


class TestValidate(ParameterizedTestCase, unittest.TestCase):
    integer = parametrized(
        ("integer", "valid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type="integer"))

    number = parametrized(
        ("integer", "valid", 1),
        ("number", "valid", 1.1),
        ("string", "invalid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type="number"))

    _string = [
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("unicode", "valid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    ]

    if not PY3:
        # The JSON module in Python2 does not always produce unicode objects :/
        _string.append(("bytestring", "valid", b"foo"))

    string = parametrized(*_string)(validation_test(type="string"))

    object = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", "foo"),
        ("object", "valid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type="object"))

    array = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", "foo"),
        ("object", "invalid", {}),
        ("array", "valid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type="array"))

    boolean = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("true", "valid", True),
        ("false", "valid", False),
        ("null", "invalid", None),
    )(validation_test(type="boolean"))

    null = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("string", "invalid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "valid", None),
    )(validation_test(type="null"))

    any = parametrized(
        ("integer", "valid", 1),
        ("number", "valid", 1.1),
        ("string", "valid", "foo"),
        ("object", "valid", {}),
        ("array", "valid", []),
        ("boolean", "valid", True),
        ("null", "valid", None),
    )(validation_test(type="any"))

    multiple_types = parametrized(
        ("integer", "valid", 1),
        ("string", "valid", "foo"),
        ("number", "invalid", 1.1),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=["integer", "string"]))

    multiple_types_schema = parametrized(
        ("match", "valid", [1, 2]),
        ("other_match", "valid", {"foo" : "bar"}),
        ("number", "invalid", 1.1),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type=["array", {"type" : "object"}]))

    multiple_types_subschema = parametrized(
        ("integer", "valid", 1),
        ("object_right_type", "valid", {"foo" : None}),
        ("object_wrong_type", "invalid", {"foo" : 1}),
        ("object_another_wrong_type", "invalid", {"foo" : 1.1}),
    )(validation_test(
        type=["integer", {"properties" : {"foo" : {"type" : "null"}}}]
    ))

    def test_multiple_types_nonobject(self):
        """
        Regression test for issue #18.

        """
        validate(
            [1, 2, 3],
            {"type" : [{"type" : ["string"]}, {"type" : ["array", "null"]}]}
        )

    properties = parametrized(
        ("", "valid", {"foo" : 1, "bar" : "baz"}),
        ("extra_property", "valid",
         {"foo" : 1, "bar" : "baz", "quux" : 42}),
        ("invalid_type", "invalid", {"foo" : 1, "bar" : []}),
    )(validation_test(
        {
            "properties" : {
                "foo" : {"type" : "number"},
                "bar" : {"type" : "string"},
            }
        }
    ))

    patternProperties = parametrized(
        ("single_match", "valid", {"foo" : 1}),
        ("multiple_match", "valid", {"foo" : 1, "fah" : 2, "bar" : "baz"}),
        ("single_mismatch", "invalid", {"foo" : "bar"}),
        ("multiple_mismatch", "invalid", {"foo" : 1, "fah" : "bar"}),
    )(validation_test(patternProperties={"f.*" : {"type" : "integer"}}))

    multiple_patternProperties = parametrized(
        ("match", "valid", {"a" : 21}),
        ("other_match", "valid", {"aaaa" : 18}),
        ("multiple_match", "valid", {"a" : 21, "aaaa" : 18}),
        ("mismatch", "invalid", {"aaa" : "bar"}),
        ("other_mismatch", "invalid", {"aaaa" : 31}),
        ("multiple_mismatch", "invalid", {"aaa" : "foo", "aaaa" : 32}),
    )(validation_test(patternProperties={
        "a*" : {"type" : "integer"},
        "aaa*" : {"maximum" : 20},
        }
    ))

    def test_additionalProperties_allowed_by_default(self):
        schema = {
            "properties" : {
                "foo" : {"type" : "number"},
                "bar" : {"type" : "string"},
            }
        }
        validate({"foo" : 1, "bar" : "baz", "quux" : False}, schema)

    @parametrized(
        ("", False),
        ("schema", {"type" : "boolean"}),
    )
    def additionalProperties(self, aP):
        schema = {
            "properties" : {
                "foo" : {"type" : "number"},
                "bar" : {"type" : "string"},
            },

            "additionalProperties" : aP,
        }

        with self.assertRaises(ValidationError):
            validate({"foo" : 1, "bar" : "baz", "quux" : "boom"}, schema)

    def test_additionalProperties_ignores_nonobjects(self):
        validate(None, {"additionalProperties" : False})

    @parametrized(
        ("single_extra", {"foo" : 2}, ["'foo' was unexpected)"]),
        ("multiple_extras",
         dict.fromkeys(["foo", "bar", "quux"]),
         ["'bar'", "'foo'", "'quux'", "were unexpected)"],
        ),
    )
    def additionalProperties_errorMessage(self, instance, errs):
        schema = {"additionalProperties" : False}

        with self.assertRaises(ValidationError) as error:
            validate(instance, schema)

        self.assertTrue(all(err in unicode(error.exception) for err in errs))

    items = parametrized(
        ("", "valid", [1, 2, 3]),
        ("wrong_type", "invalid", [1, "x"]),
    )(validation_test(items={"type" : "integer"}))

    items_tuple_typing = parametrized(
        ("", "valid", [1, "foo"]),
        ("wrong_type", "invalid", ["foo", 1])
    )(validation_test(items=[{"type" : "integer"}, {"type" : "string"}]))

    def test_additionalItems_allowed_by_default(self):
        validate(
            [1, "foo", False],
            {"items" : [{"type" : "integer"}, {"type" : "string"}]}
        )

    additionalItems = parametrized(
        ("no_additional", "valid", [1, "foo"]),
        ("additional", "invalid", [1, "foo", False]),
    )(validation_test({
        "items" : [{"type" : "integer"}, {"type" : "string"}],
        "additionalItems" : False,
    }))

    additionalItems_schema = parametrized(
        ("match", "valid", [1, "foo", 3]),
        ("mismatch", "invalid", [1, "foo", "bar"]),
    )(validation_test({
        "items" : [{"type" : "integer"}, {"type" : "string"}],
        "additionalItems" : {"type" : "integer"},
    }))

    def test_additionalItems_ignores_nonarrays(self):
        validate(None, {"additionalItems" : False})

    @parametrized(
        ("single_extra", [2], "(2 was unexpected)"),
        ("multiple_extras", [1, 2, 3], "(1, 2, 3 were unexpected)"),
    )
    def additionalItems_errorMessage(self, instance, err):
        schema = {"additionalItems" : False}
        self.assertRaisesRegexp(
            ValidationError, err, validate, instance, schema
        )

    @parametrized(
        ("false_by_default", "valid", {}, {}),
        ("false_explicit", "valid", {"required" : False}, {}),
        ("one", "valid", {"required" : True}, {}),
        ("other", "invalid", {}, {"required" : True}),
        ("both", "invalid", {"required" : True}, {"required" : True}),
    )
    def required(self, expect, foo, bar):
        schema = {
            "properties" : {
                "foo" : {"type" : "number"},
                "bar" : {"type" : "string"},
            }
        }

        schema["properties"]["foo"].update(foo)
        schema["properties"]["bar"].update(bar)

        test = validation_test(schema)
        test(self, expect, {"foo" : 1})

    dependencies = parametrized(
        ("neither", "valid", {}),
        ("nondependant", "valid", {"foo" : 1}),
        ("with_dependency", "valid", {"foo" : 1, "bar" : 2}),
        ("missing_dependency", "invalid", {"bar" : 2}),
    )(validation_test(dependencies={"bar": "foo"}))

    multiple_dependencies = parametrized(
        ("neither", "valid", {}),
        ("nondependants", "valid", {"foo" : 1, "bar" : 2}),
        ("with_dependencies", "valid", {"foo" : 1, "bar" : 2, "quux" : 3}),
        ("missing_dependency", "invalid", {"foo" : 1, "quux" : 2}),
        ("missing_other_dependency", "invalid", {"bar" : 1, "quux" : 2}),
        ("missing_both_dependencies", "invalid", {"quux" : 1}),
    )(validation_test(
        dependencies={"quux" : ["foo", "bar"]}
    ))

    multiple_dependencies_subschema = parametrized(
        ("", "valid", {"foo" : 1, "bar" : 2}),
        ("wrong_type", "invalid", {"foo" : "quux", "bar" : 2}),
        ("wrong_type_other", "invalid", {"foo" : 2, "bar" : "quux"}),
        ("wrong_type_both", "invalid", {"foo" : "quux", "bar" : "quux"}),
    )(validation_test(dependencies={
        "bar" : {
            "properties" : {
                "foo" : {"type" : "integer"},
                "bar" : {"type" : "integer"},
        }}}))

    def test_dependencies_error_message_has_single_element_not_list(self):
        with self.assertRaises(ValidationError) as e:
            validate({"bar" : 2}, {"dependencies" : {"bar" : "foo"}})
        self.assertNotIn("'foo']", e.exception.message)
        self.assertIn("'foo'", e.exception.message)

    @parametrized(
        ("", "valid", {}, 2.6),
        ("fail", "invalid", {}, .6),
        ("exclusiveMinimum", "valid", {"exclusiveMinimum" : True}, 1.2),
        ("exclusiveMinimum_fail", "invalid",
         {"exclusiveMinimum" : True}, 1.1),
    )
    def minimum(self, expect, eM, instance):
        eM["minimum"] = 1.1
        test = validation_test(eM)
        test(self, expect, instance)

    @parametrized(
        ("", "valid", {}, 2.6),
        ("fail", "invalid", {}, 3.5),
        ("exclusiveMaximum", "valid", {"exclusiveMaximum" : True}, 2.2),
        ("exclusiveMaximum_fail", "invalid",
         {"exclusiveMaximum" : True}, 3.0),
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

    uniqueItems = parametrized(
        ("unique", "valid", [1, 2]),
        ("not_unique", "invalid", [1, 1]),
        ("object_unique", "valid", [{"foo" : "bar"}, {"foo" : "baz"}]),
        ("object_not_unique", "invalid", [{"foo" : "bar"}, {"foo" : "bar"}]),
        ("array_unique", "valid", [["foo"], ["bar"]]),
        ("array_not_unique", "invalid", [["foo"], ["foo"]]),
        ("nested", "valid", [
            {"foo" : {"bar" : {"baz" : "quux"}}},
            {"foo" : {"bar" : {"baz" : "spam"}}},
        ]),
        ("nested_not_unique", "invalid", [
            {"foo" : {"bar" : {"baz" : "quux"}}},
            {"foo" : {"bar" : {"baz" : "quux"}}},
        ])
    )(validation_test(uniqueItems=True))

    pattern = parametrized(
        ("match", "valid", "aaa"),
        ("mismatch", "invalid", "ab"),
        ("ignores_other_stuff", "valid", True),
    )(validation_test(pattern="^a*$"))

    minLength = parametrized(
        ("", "valid", "foo"),
        ("too_short", "invalid", "f"),
        ("ignores_arrays", "valid", [1]),
    )(validation_test(minLength=2))

    maxLength = parametrized(
        ("", "valid", "f"),
        ("too_long", "invalid", "foo"),
        ("ignores_arrays", "valid", [1, 2, 3]),
    )(validation_test(maxLength=2))

    @parametrized(
        ("integer", "valid", 1, [1, 2, 3]),
        ("integer_fail", "invalid", 6, [1, 2, 3]),
        ("string", "valid", "foo", ["foo", "bar"]),
        ("string_fail", "invalid", "quux", ["foo", "bar"]),
        ("bool", "valid", True, [True]),
        ("bool_fail", "invalid", False, [True]),
        ("object", "valid", {"foo" : "bar"}, [{"foo" : "bar"}]),
        ("object_fail", "invalid", {"foo" : "bar"}, [{"foo" : "quux"}]),
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
        ("number_by_number_again", "valid", 1.09, .01),
        ("number_by_number_again_2", "valid", 1.89, .01),
    )
    def divisibleBy(self, expect, instance, dB):
        test = validation_test(divisibleBy=dB)
        test(self, expect, instance)

    disallow = parametrized(
        ("", "valid", "foo"),
        ("disallowed", "invalid", 1),
    )(validation_test(disallow="integer"))

    multiple_disallow = parametrized(
        ("", "valid", "foo"),
        ("mismatch", "invalid", 1),
        ("other_mismatch", "invalid", True),
    )(validation_test(disallow=["integer", "boolean"]))

    multiple_disallow_subschema = parametrized(
        ("match", "valid", 1),
        ("other_match", "valid", {"foo" : 1}),
        ("mismatch", "invalid", "foo"),
        ("other_mismatch", "invalid", {"foo" : "bar"}),
    )(validation_test(
        disallow=[
            "string",
            {"type" : "object", "properties" : {"foo" : {"type" : "string"}}},
        ]
    ))

    @parametrized(
        ("", "valid", {"foo" : "baz", "bar" : 2}),
        ("mismatch_extends", "invalid", {"foo" : "baz"}),
        ("mismatch_extended", "invalid", {"bar" : 2}),
        ("wrong_type", "invalid", {"foo" : "baz", "bar" : "quux"}),
    )
    def extends(self, expect, instance):
        schema = {
            "properties" : {"bar" : {"type" : "integer", "required" : True}},
            "extends" : {
                "properties" : {
                    "foo" : {"type" : "string", "required" : True},
                }
            },
        }

        test = validation_test(**schema)
        test(self, expect, instance)

    @parametrized(
        ("", "valid", {"foo" : "quux", "bar" : 2, "baz" : None}),
        ("mismatch_first_extends", "invalid", {"bar" : 2, "baz" : None}),
        ("mismatch_second_extends", "invalid", {"foo" : "quux", "bar" : 2}),
        ("mismatch_both", "invalid", {"bar" : 2}),
    )
    def multiple_extends(self, expect, instance):
        schema = {
            "properties" : {"bar" : {"type" : "integer", "required" : True}},
            "extends" : [
                {
                    "properties" : {
                    "foo" : {"type" : "string", "required" : True},
                    }
                },
                {
                    "properties" : {
                    "baz" : {"type" : "null", "required" : True},
                    }
                },
            ],
        }

        test = validation_test(**schema)
        test(self, expect, instance)

    extends_simple_types = parametrized(
        ("", "valid", 25),
        ("mismatch_extends", "invalid", 35)
    )(validation_test(minimum=20, extends={"maximum" : 30}))

    def test_iter_errors(self):
        instance = [1, 2]
        schema = {
            "disallow" : "array",
            "enum" : [["a", "b", "c"], ["d", "e", "f"]],
            "minItems" : 3
        }

        if PY3:
            errors = sorted([
                "'array' is disallowed for [1, 2]",
                "[1, 2] is too short",
                "[1, 2] is not one of [['a', 'b', 'c'], ['d', 'e', 'f']]",
            ])
        else:
            errors = sorted([
                "u'array' is disallowed for [1, 2]",
                "[1, 2] is too short",
                "[1, 2] is not one of [[u'a', u'b', u'c'], [u'd', u'e', u'f']]",
            ])

        self.assertEqual(
            sorted(str(e) for e in Validator().iter_errors(instance, schema)),
            errors,
        )

    def test_unknown_type_error(self):
        with self.assertRaises(SchemaError):
            validate(1, {"type" : "foo"}, unknown_type="error")

    def test_unknown_type_warn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate(1, {"type" : "foo"}, unknown_type="warn")
        self.assertEqual(len(w), 1)

    def test_unknown_type_skip(self):
        validate(1, {"type" : "foo"}, unknown_type="skip")

    def test_unknown_property_error(self):
        with self.assertRaises(SchemaError):
            validate(1, {"foo" : "bar"}, unknown_property="error")

    def test_unknown_property_warn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate(1, {"foo" : "bar"}, unknown_property="warn")
        self.assertEqual(len(w), 1)

    def test_unknown_property_skip(self):
        validate(
            1,
            {"foo" : "foo", "type" : "integer"},
            unknown_property="skip"
        )

    decimal = parametrized(
        ("integer", "valid", 1),
        ("number", "valid", 1.1),
        ("decimal", "valid", Decimal(1) / Decimal(8)),
        ("string", "invalid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(
        initkwargs={"types" : {"number" : (int, float, Decimal)}},
        type="number")
    )

    # TODO: we're in need of more meta schema tests
    def test_invalid_properties(self):
        with self.assertRaises(SchemaError):
            validate({}, {"properties": {"test": True}})

    def test_minItems_invalid_string(self):
        with self.assertRaises(SchemaError):
            validate([1], {"minItems" : "1"})  # needs to be an integer

    def test_iter_errors_multiple_failures_one_validator(self):
        instance = {"foo" : 2, "bar" : [1], "baz" : 15, "quux" : "spam"}
        schema = {
            "properties" : {
                "foo" : {"type" : "string"},
                "bar" : {"minItems" : 2},
                "baz" : {"maximum" : 10, "enum" : [2, 4, 6, 8]},
            }
        }

        errors = list(Validator().iter_errors(instance, schema))
        self.assertEqual(len(errors), 4)


class TestValidationErrorDetails(unittest.TestCase):
    # TODO: These really need unit tests for each individual validator, rather
    #       than just these higher level tests.
    def test_single_nesting(self):
        instance = {"foo" : 2, "bar" : [1], "baz" : 15, "quux" : "spam"}
        schema = {
            "properties" : {
                "foo" : {"type" : "string"},
                "bar" : {"minItems" : 2},
                "baz" : {"maximum" : 10, "enum" : [2, 4, 6, 8]},
            }
        }

        errors = Validator().iter_errors(instance, schema)
        e1, e2, e3, e4 = sorted_errors(errors)

        self.assertEqual(e1.path, ["bar"])
        self.assertEqual(e2.path, ["baz"])
        self.assertEqual(e3.path, ["baz"])
        self.assertEqual(e4.path, ["foo"])

        self.assertEqual(e1.validator, "minItems")
        self.assertEqual(e2.validator, "enum")
        self.assertEqual(e3.validator, "maximum")
        self.assertEqual(e4.validator, "type")

    def test_multiple_nesting(self):
        instance = [1, {"foo" : 2, "bar" : {"baz" : [1]}}, "quux"]
        schema = {
            "type" : "string",
            "items" : {
                "type" : ["string", "object"],
                "properties" : {
                    "foo" : {"enum" : [1, 3]},
                    "bar" : {
                        "type" : "array",
                        "properties" : {
                            "bar" : {"required" : True},
                            "baz" : {"minItems" : 2},
                        }
                    }
                }
            }
        }

        errors = Validator().iter_errors(instance, schema)
        e1, e2, e3, e4, e5, e6 = sorted_errors(errors)

        self.assertEqual(e1.path, [])
        self.assertEqual(e2.path, [0])
        self.assertEqual(e3.path, ["bar", 1])
        self.assertEqual(e4.path, ["bar", "bar", 1])
        self.assertEqual(e5.path, ["baz", "bar", 1])
        self.assertEqual(e6.path, ["foo", 1])

        self.assertEqual(e1.validator, "type")
        self.assertEqual(e2.validator, "type")
        self.assertEqual(e3.validator, "type")
        self.assertEqual(e4.validator, "required")
        self.assertEqual(e5.validator, "minItems")
        self.assertEqual(e6.validator, "enum")


class TestErrorTree(unittest.TestCase):
    def test_tree(self):
        instance = [1, {"foo" : 2, "bar" : {"baz" : [1]}}, "quux"]
        schema = {
            "type" : "string",
            "items" : {
                "type" : ["string", "object"],
                "properties" : {
                    "foo" : {"enum" : [1, 3]},
                    "bar" : {
                        "type" : "array",
                        "properties" : {
                            "bar" : {"required" : True},
                            "baz" : {"minItems" : 2},
                        }
                    }
                }
            }
        }

        errors = sorted_errors(Validator().iter_errors(instance, schema))
        e1, e2, e3, e4, e5, e6 = errors
        tree = ErrorTree(errors)

        self.assertEqual(len(tree), 6)

        self.assertIn(0, tree)
        self.assertIn(1, tree)
        self.assertIn("bar", tree[1])
        self.assertIn("foo", tree[1])
        self.assertIn("baz", tree[1]["bar"])

        self.assertEqual(tree.errors["type"], e1)
        self.assertEqual(tree[0].errors["type"], e2)
        self.assertEqual(tree[1]["bar"].errors["type"], e3)
        self.assertEqual(tree[1]["bar"]["bar"].errors["required"], e4)
        self.assertEqual(tree[1]["bar"]["baz"].errors["minItems"], e5)
        self.assertEqual(tree[1]["foo"].errors["enum"], e6)


class TestIgnorePropertiesForIrrelevantTypes(unittest.TestCase):
    def test_minimum(self):
        validate("x", {"type": ["string", "number"], "minimum": 10})

    def test_maximum(self):
        validate("x", {"type": ["string", "number"], "maximum": 10})

    def test_properties(self):
        validate(1, {"type": ["integer", "object"], "properties": {"x": {}}})

    def test_items(self):
        validate(
            1, {"type": ["integer", "array"], "items": {"type": "string"}}
        )

    def test_divisibleBy(self):
        validate("x", {"type": ["integer", "string"], "divisibleBy": 10})


def sorted_errors(errors):
    return sorted(errors, key=lambda e : [str(err) for err in e.path])
