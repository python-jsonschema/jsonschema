from __future__ import with_statement, unicode_literals
from decimal import Decimal
from functools import wraps
import sys
import warnings

if sys.version_info[:2] < (2, 7):  # pragma: no cover
    import unittest2 as unittest
else:
    import unittest


from jsonschema import PY3, SchemaError, ValidationError, iteritems, validate


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

    string = parametrized(
        ("integer", "invalid", 1),
        ("number", "invalid", 1.1),
        ("unicode", "valid", "foo"),
        ("str", "valid", "foo"),
        ("object", "invalid", {}),
        ("array", "invalid", []),
        ("boolean", "invalid", True),
        ("null", "invalid", None),
    )(validation_test(type="string"))

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
    )(validation_test(properties={"bar" : {"dependencies" : "foo"}}))

    multiple_dependencies = parametrized(
        ("neither", "valid", {}),
        ("nondependants", "valid", {"foo" : 1, "bar" : 2}),
        ("with_dependencies", "valid", {"foo" : 1, "bar" : 2, "quux" : 3}),
        ("missing_dependency", "invalid", {"foo" : 1, "quux" : 2}),
        ("missing_other_dependency", "invalid", {"bar" : 1, "quux" : 2}),
        ("missing_both_dependencies", "invalid", {"quux" : 1}),
    )(validation_test(
        properties={"quux" : {"dependencies" : ["foo", "bar"]}}
    ))

    multiple_dependencies_subschema = parametrized(
        ("", "valid", {"foo" : 1, "bar" : 2}),
        ("wrong_type", "invalid", {"foo" : "quux", "bar" : 2}),
        ("wrong_type_other", "invalid", {"foo" : 2, "bar" : "quux"}),
        ("wrong_type_both", "invalid", {"foo" : "quux", "bar" : "quux"}),
    )(validation_test(properties={
        "bar" : {
            "dependencies" : {
                "properties" : {
                    "foo" : {"type" : "integer"},
                    "bar" : {"type" : "integer"},
        }}}}))

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
        disallow=["string", {"properties" : {"foo" : {"type" : "string"}}}]
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

    def test_stop_on_error(self):
        instance = [1, 2]

        schema = {
            "disallow" : "array",
            "enum" : [["a", "b", "c"], ["d", "e", "f"]],
            "minItems" : 3
        }

        with self.assertRaises(ValidationError) as e:
            validate(instance, schema, stop_on_error=False)

        if PY3:
            self.assertEqual(sorted(e.exception.errors), sorted([
                "'array' is disallowed for [1, 2]",
                "[1, 2] is too short",
                "[1, 2] is not one of [['a', 'b', 'c'], ['d', 'e', 'f']]",
                ]))
        else:
            self.assertEqual(sorted(e.exception.errors), sorted([
                "u'array' is disallowed for [1, 2]",
                "[1, 2] is too short",
                "[1, 2] is not one of [[u'a', u'b', u'c'], [u'd', u'e', u'f']]",
                ]))

    def test_unknown_type_error(self):
        with self.assertRaises(SchemaError):
            validate(1, {"type" : "foo"}, unknown_type="error")

    @unittest.skipIf(
        sys.version_info[:2] == (2, 5),
        "Python 2.5 lacks catch_warnings, and I am lazy."
    )
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

    @unittest.skipIf(
        sys.version_info[:2] == (2, 5),
        "Python 2.5 lacks catch_warnings, and I am lazy."
    )
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
        initkwargs={"number_types" : (int, float, Decimal)},
        type="number")
    )

    # TODO: we're in need of more meta schema tests
    def test_minItems_invalid_string(self):
        with self.assertRaises(SchemaError):
            validate([1], {"minItems" : "1"})  # needs to be an integer

    format_date_time = parametrized(
        ("isodatetime", "valid", "2012-04-23T16:07:00Z"),
        ("missing_z", "invalid", "2012-04-23T16:07:00"),
        ("y2k", "invalid", "12-04-23T16:07:00"),
        ("overflow", "invalid", "2012-13-23T16:07:00"),
        ("extra", "invalid", "2012-13-23T16:07:00ZB"),
        ("date_only", "invalid", "2012-13-23")
    )(validation_test(format="date-time"))

    format_date = parametrized(
        ("isodate", "valid", "2012-04-23"),
        ("y2k", "invalid", "12-04-23"),
        ("overflow", "invalid", "2012-13-23"),
        ("extra", "invalid", "2012-04-23T16:07:00Z")
    )(validation_test(format="date"))

    format_time = parametrized(
        ("isotime", "valid", "16:07:00"),
        ("overflow", "invalid", "25:00:32"),
        ("extra", "invalid", "16:07:00.43")
    )(validation_test(format="time"))

    format_utc_millisec = parametrized(
        ("string", "valid", "52.0"),
        ("float", "valid", 1.2e64),
        ("integer", "valid", 1 << 70),
        ("not_number", "invalid", "FOO")
    )(validation_test(format="utc-millisec"))

    format_regex = parametrized(
        ("valid", "valid", r"^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@)"),
        ("unbalanced", "invalid", r"^(([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@")
    )(validation_test(format="regex"))

    format_phone = parametrized(
        ("valid", "valid", "+31 42 123 4567"),
        ("north_american", "invalid", "(800)555-1234")
    )(validation_test(format="phone"))

    format_ip_address = parametrized(
        ("valid", "valid", "127.0.0.1"),
        ("hostname", "invalid", "www.google.com"),
        ("valid_short", "valid", "127"),
        ("valid_numerical", "valid", str(0xffffffff))
    )(validation_test(format="ip-address"))

    format_ipv6 = parametrized(
        ("valid", "valid", "2001:0db8:85a3:0000:0000:8a2e:0370:7334"),
        ("leading_zeros", "valid", "2001:db8:85a3:0:0:8a2e:370:7334"),
        ("dotted", "valid", "2001:db8:85a3::8a2e:370:7334"),
        ("hostname", "invalid", "www.google.com")
    )(validation_test(format="ipv6"))

    format_host_name = parametrized(
        ("valid", "valid", "www.google.com"),
        ("numerical", "invalid", "127.0.0.1")
    )(validation_test(format="host-name"))
