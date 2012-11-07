from __future__ import unicode_literals
from decimal import Decimal
from functools import wraps
import glob
import os
import re
import sys
import warnings
import json

if sys.version_info[:2] < (2, 7):  # pragma: no cover
    from unittest2 import TestCase, expectedFailure, skipIf
else:
    from unittest import TestCase, expectedFailure, skipIf

try:
    from unittest import mock
except ImportError:
    import mock

from jsonschema import (
    PY3, SchemaError, UnknownType, ValidationError, ErrorTree,
    Draft3Validator, RefResolver, iteritems, validate
)


if PY3:
    basestring = unicode = str


def make_case(schema, data, valid, cls):
    def test_case(self):
        if valid:
            validate(data, schema, cls=cls)
        else:
            with self.assertRaises(ValidationError):
                validate(data, schema, cls=cls)
    return test_case


def load_json_cases(test_dir):
    def add_test_methods(test_class):
        for filename in glob.iglob(os.path.join(test_dir, "*.json")):
            validating, _ = os.path.splitext(os.path.basename(filename))

            with open(filename) as test_file:
                data = json.load(test_file)

                for case in data:
                    for test in case["tests"]:
                        a_test = make_case(
                            case["schema"],
                            test["data"],
                            test["valid"],
                            test_class.validator_class,
                        )

                        test_name = "test_%s_%s" % (
                            validating,
                            re.sub(r"[\W ]+", "_", test["description"]),
                        )

                        if not PY3:
                            test_name = test_name.encode("utf-8")
                        a_test.__name__ = test_name

                        setattr(test_class, test_name, a_test)

        return test_class
    return add_test_methods


@load_json_cases(os.path.join(os.path.dirname(__file__), "json/tests/draft3/"))
class TestDraft3(TestCase):
    validator_class = Draft3Validator


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


class TestValidate(ParameterizedTestCase, TestCase):
    @skipIf(PY3, "The JSON module in Python 3 always produces unicode")
    def test_string_a_bytestring_is_a_string(self):
        validate(b"foo", {"type" : "string"})

    # A horrible name and horrible test. I will repent.
    # See https://groups.google.com/d/msg/json-schema/Q5F30CZtMb4/yk_niLnsdQ0J
    p_pP_aP = parametrized(
        ("property_validates_property", "valid", {"foo" : [1, 2]}),
        ("property_invalidates_property", "invalid", {"foo" : [1, 2, 3, 4]}),
        ("patternProperty_invalidates_property", "invalid", {"foo" : []}),
        ("patternProperty_validates_nonproperty", "valid", {"fxo" : [1, 2]}),
        ("patternProperty_invalidates_nonproperty", "invalid", {"fxo" : []}),
        ("additionalProperty_ignores_property", "valid", {"bar" : []}),
        ("additionalProperty_validates_others", "valid", {"quux" : 3}),
        ("additionalProperty_invalidates_others", "invalid", {"quux" : "foo"}),
    )(validation_test(
        properties={
            "foo" : {"type" : "array", "maxItems" : 3},
            "bar" : {"type" : "array"}
        },
        patternProperties={"f.o" : {"minItems" : 2}},
        additionalProperties={"type" : "integer"},
    ))

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

    def test_additionalItems_ignored_when_items_is_not_tuple(self):
        validate([1, 2], {"additionalItems" : False})

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

    @parametrized(
        ("int_by_int", "valid", 10, 2),
        ("int_by_int_fail", "invalid", 7, 2),
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

    root_pointer_ref = parametrized(
        ("match", "valid", {"foo": False}),
        ("recursive_match", "valid", {"foo": {"foo": False}}),
        ("mismatch", "invalid", {"bar": False}),
        ("recursive_mismatch", "invalid", {"foo": {"bar": False}})
    )(validation_test(
        properties={"foo": {"$ref": "#"}}, additionalProperties=False)
    )

    relative_pointer_ref = parametrized(
        ("match", "valid", {"bar": 3}),
        ("mismatch", "invalid", {"bar": True})
    )(validation_test(
        properties={"foo": {"type": "integer"},
                    "bar": {"$ref": "#/properties/foo"}}
    ))

    escaped_pointer_ref = parametrized(
        ("slash", "invalid", {"slash": "aoeu"}),
        ("tilda", "invalid", {"tilda": "aoeu"}),
        ("percent", "invalid", {"percent": "aoeu"})
    )(validation_test(
        schema= {
            "tilda~field": {"type": "integer"},
            "slash/field": {"type": "integer"},
            "percent%field": {"type": "integer"},
            "properties": {
                "tilda": {"$ref": "#/tilda~0field"},
                "slash": {"$ref": "#/slash~1field"},
                "percent": {"$ref": "#/percent%25field"}
            }
        }
    ))


class TestIterErrors(TestCase):
    def setUp(self):
        self.validator = Draft3Validator({})

    def test_iter_errors(self):
        instance = [1, 2]
        schema = {
            "disallow" : "array",
            "enum" : [["a", "b", "c"], ["d", "e", "f"]],
            "minItems" : 3
        }

        got = (str(e) for e in self.validator.iter_errors(instance, schema))
        expected = [
            "%r is disallowed for [1, 2]" % (schema["disallow"],),
            "[1, 2] is too short",
            "[1, 2] is not one of %r" % (schema["enum"],),
        ]
        self.assertEqual(sorted(got), sorted(expected))

    def test_iter_errors_multiple_failures_one_validator(self):
        instance = {"foo" : 2, "bar" : [1], "baz" : 15, "quux" : "spam"}
        schema = {
            "properties" : {
                "foo" : {"type" : "string"},
                "bar" : {"minItems" : 2},
                "baz" : {"maximum" : 10, "enum" : [2, 4, 6, 8]},
            }
        }

        errors = list(self.validator.iter_errors(instance, schema))
        self.assertEqual(len(errors), 4)


class TestValidationErrorMessages(TestCase):
    def message_for(self, instance, schema):
        with self.assertRaises(ValidationError) as e:
            validate(instance, schema)
        return e.exception.message

    def test_single_type_failure(self):
        message = self.message_for(instance=1, schema={"type" : "string"})
        self.assertEqual(message, "1 is not of type %r" % "string")

    def test_single_type_list_failure(self):
        message = self.message_for(instance=1, schema={"type" : ["string"]})
        self.assertEqual(message, "1 is not of type %r" % "string")

    def test_multiple_type_failure(self):
        types = ("string", "object")
        message = self.message_for(instance=1, schema={"type" : list(types)})
        self.assertEqual(message, "1 is not of type %r, %r" % types)

    def test_object_without_title_type_failure(self):
        type = {"type" : [{"minimum" : 3}]}
        message = self.message_for(instance=1, schema={"type" : [type]})
        self.assertEqual(message, "1 is not of type %r" % (type,))

    def test_object_with_name_type_failure(self):
        name = "Foo"
        schema = {"type" : [{"name" : name, "minimum" : 3}]}
        message = self.message_for(instance=1, schema=schema)
        self.assertEqual(message, "1 is not of type %r" % (name,))

    def test_dependencies_failure_has_single_element_not_list(self):
        depend, on = "bar", "foo"
        schema = {"dependencies" : {depend : on}}
        message = self.message_for({"bar" : 2}, schema)
        self.assertEqual(message, "%r is a dependency of %r" % (on, depend))

    def test_additionalItems_single_failure(self):
        message = self.message_for(
            [2], {"items" : [], "additionalItems" : False},
        )
        self.assertIn("(2 was unexpected)", message)

    def test_additionalItems_multiple_failures(self):
        message = self.message_for(
            [1, 2, 3], {"items" : [], "additionalItems" : False}
        )
        self.assertIn("(1, 2, 3 were unexpected)", message)

    def test_additionalProperties_single_failure(self):
        additional = "foo"
        schema = {"additionalProperties" : False}
        message = self.message_for({additional : 2}, schema)
        self.assertIn("(%r was unexpected)" % (additional,), message)

    def test_additionalProperties_multiple_failures(self):
        schema = {"additionalProperties" : False}
        message = self.message_for(dict.fromkeys(["foo", "bar"]), schema)

        self.assertIn(repr("foo"), message)
        self.assertIn(repr("bar"), message)
        self.assertIn("were unexpected)", message)


class TestValidationErrorDetails(TestCase):
    def setUp(self):
        self.validator = Draft3Validator({})

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

        errors = self.validator.iter_errors(instance, schema)
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

        errors = self.validator.iter_errors(instance, schema)
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


class TestErrorTree(TestCase):
    def setUp(self):
        self.validator = Draft3Validator({})

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

        errors = sorted_errors(self.validator.iter_errors(instance, schema))
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


class TestDraft3Validator(TestCase):
    def setUp(self):
        self.instance = mock.Mock()
        self.schema = {}
        self.resolver = mock.Mock()
        self.validator = Draft3Validator(self.schema)

    def test_valid_instances_are_valid(self):
        errors = iter([])

        with mock.patch.object(
            self.validator, "iter_errors", return_value=errors,
        ):
            self.assertTrue(
                self.validator.is_valid(self.instance, self.schema)
            )

    def test_invalid_instances_are_not_valid(self):
        errors = iter([mock.Mock()])

        with mock.patch.object(
            self.validator, "iter_errors", return_value=errors,
        ):
            self.assertFalse(
                self.validator.is_valid(self.instance, self.schema)
            )

    def test_non_existent_properties_are_ignored(self):
        instance, my_property, my_value = mock.Mock(), mock.Mock(), mock.Mock()
        validate(instance=instance, schema={my_property : my_value})

    def test_it_creates_a_ref_resolver_if_not_provided(self):
        self.assertIsInstance(self.validator.resolver, RefResolver)

    def test_it_delegates_to_a_ref_resolver(self):
        resolver = mock.Mock()
        resolver.resolve.return_value = {"type" : "integer"}
        schema = {"$ref" : mock.Mock()}

        with self.assertRaises(ValidationError):
            Draft3Validator(schema, resolver=resolver).validate(None)

        resolver.resolve.assert_called_once_with(schema, schema["$ref"])

    def test_is_type_is_true_for_valid_type(self):
        self.assertTrue(self.validator.is_type("foo", "string"))

    def test_is_type_is_false_for_invalid_type(self):
        self.assertFalse(self.validator.is_type("foo", "array"))

    def test_is_type_evades_bool_inheriting_from_int(self):
        self.assertFalse(self.validator.is_type(True, "integer"))
        self.assertFalse(self.validator.is_type(True, "number"))

    def test_is_type_does_not_evade_bool_if_it_is_being_tested(self):
        self.assertTrue(self.validator.is_type(True, "boolean"))
        self.assertTrue(self.validator.is_type(True, "any"))

    def test_is_type_raises_exception_for_unknown_type(self):
        with self.assertRaises(UnknownType):
            self.validator.is_type("foo", object())


class TestRefResolver(TestCase):
    def setUp(self):
        self.resolver = RefResolver()
        self.schema = mock.MagicMock()

    def test_it_resolves_local_refs(self):
        ref = "#/properties/foo"
        resolved = self.resolver.resolve(self.schema, ref)
        self.assertEqual(resolved, self.schema["properties"]["foo"])

    def test_it_accepts_a_ref_store(self):
        store = mock.Mock()
        self.assertEqual(RefResolver(store).store, store)

    def test_it_retrieves_stored_refs(self):
        ref = self.resolver.store["cached_ref"] = mock.Mock()
        resolved = self.resolver.resolve(self.schema, "cached_ref")
        self.assertEqual(resolved, ref)


class TestIgnorePropertiesForIrrelevantTypes(TestCase):
    def test_minimum_ignores_nonnumbers(self):
        validate("x", {"type": ["string", "number"], "minimum": 10})

    def test_maximum_ignores_nonnumbers(self):
        validate("x", {"type": ["string", "number"], "maximum": 10})

    def test_properties_ignores_nonobjects(self):
        validate(1, {"type": ["integer", "object"], "properties": {"x": {}}})

    def test_additionalProperties_ignores_nonobjects(self):
        validate(None, {"additionalProperties" : False})

    def test_minLength_ignores_nonstrings(self):
        validate([1], {"minLength" : 3})

    def test_maxLength_ignores_nonstrings(self):
        validate([1, 2, 3], {"minLength" : 2})

    def test_pattern_ignores_non_strings(self):
        validate(True, {"pattern" : "^a*$"})

    def test_items_ignores_nonarrays(self):
        validate(
            1, {"type": ["integer", "array"], "items": {"type": "string"}}
        )

    def test_minItems_ignores_nonarrays(self):
        validate("x", {"minItems" : 3})

    def test_maxItems_ignores_nonarrays(self):
        validate("xxxx", {"maxItems" : 3})

    def test_additionalItems_ignores_nonarrays(self):
        validate(None, {"additionalItems" : False})

    def test_divisibleBy_ignores_nonnumbers(self):
        validate("x", {"type": ["integer", "string"], "divisibleBy": 10})

    def test_dependencies_ignores_nonobjects(self):
        validate("foo", {"dependencies" : {"foo": "bar"}})


def sorted_errors(errors):
    return sorted(errors, key=lambda e : [str(err) for err in e.path])
