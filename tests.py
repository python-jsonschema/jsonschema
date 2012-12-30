from __future__ import unicode_literals
from decimal import Decimal
from io import BytesIO
import glob
import os
import re
import sys
import json

if sys.version_info[:2] < (2, 7):  # pragma: no cover
    from unittest2 import TestCase, skipIf
else:
    from unittest import TestCase, skipIf

try:
    from unittest import mock
except ImportError:
    import mock

from jsonschema import (
    PY3, SchemaError, UnknownType, ValidationError, ErrorTree,
    Draft3Validator, RefResolver, validate
)


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


class ByteStringMixin(object):
    @skipIf(PY3, "The JSON module in Python 3 always produces unicode")
    def test_string_a_bytestring_is_a_string(self):
        self.validator_class({"type" : "string"}).validate(b"foo")


class DecimalMixin(object):
    def test_it_can_validate_with_decimals(self):
        schema = {"type" : "number"}
        validator = self.validator_class(
            schema, types={"number" : (int, float, Decimal)}
        )

        for valid in [1, 1.1, Decimal(1) / Decimal(8)]:
            validator.validate(valid)

        for invalid in ["foo", {}, [], True, None]:
            with self.assertRaises(ValidationError):
                validator.validate(invalid)


class AnyTypeMixin(object):
    def test_any_type_is_valid_for_type_any(self):
        validator = self.validator_class({"type" : "any"})
        validator.validate(mock.Mock())


@load_json_cases(os.path.join(os.path.dirname(__file__), "json/tests/draft3/"))
class TestDraft3(TestCase, ByteStringMixin, DecimalMixin, AnyTypeMixin):
    validator_class = Draft3Validator

    # TODO: we're in need of more meta schema tests
    def test_invalid_properties(self):
        with self.assertRaises(SchemaError):
            validate({}, {"properties": {"test": True}})

    def test_minItems_invalid_string(self):
        with self.assertRaises(SchemaError):
            validate([1], {"minItems" : "1"})  # needs to be an integer


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

    def test_it_knows_how_many_total_errors_it_contains(self):
        errors = [mock.MagicMock() for _ in range(8)]
        tree = ErrorTree(errors)
        self.assertEqual(tree.total_errors, 8)

    def test_it_contains_an_item_if_the_item_had_an_error(self):
        errors = [ValidationError("a message", path=["bar"])]
        tree = ErrorTree(errors)
        self.assertIn("bar", tree)

    def test_it_does_not_contain_an_item_if_the_item_had_no_error(self):
        errors = [ValidationError("a message", path=["bar"])]
        tree = ErrorTree(errors)
        self.assertNotIn("foo", tree)

    def test_validators_that_failed_appear_in_errors_dict(self):
        error = ValidationError("a message", validator="foo")
        tree = ErrorTree([error])
        self.assertEqual(tree.errors, {"foo" : error})

    def test_it_creates_a_child_tree_for_each_nested_path(self):
        errors = [
            ValidationError("a bar message", path=["bar"]),
            ValidationError("a bar -> 0 message", path=[0, "bar"]),
        ]
        tree = ErrorTree(errors)
        self.assertIn(0, tree["bar"])
        self.assertNotIn(1, tree["bar"])

    def test_children_have_their_errors_dicts_built(self):
        e1, e2 = (
            ValidationError("message 1", validator="foo", path=[0, "bar"]),
            ValidationError("message 2", validator="quux", path=[0, "bar"]),
        )
        tree = ErrorTree([e1, e2])
        self.assertEqual(tree["bar"][0].errors, {"foo" : e1, "quux" : e2})


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

        resolver.resolve.assert_called_once_with(schema["$ref"])

    def test_is_type_is_true_for_valid_type(self):
        self.assertTrue(self.validator.is_type("foo", "string"))

    def test_is_type_is_false_for_invalid_type(self):
        self.assertFalse(self.validator.is_type("foo", "array"))

    def test_is_type_is_true_for_any_type(self):
        self.assertTrue(self.validator.is_type(mock.Mock(), "any"))

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
        self.base_uri = ""
        self.referrer = {}
        self.store = {}
        self.resolver = RefResolver(self.base_uri, self.referrer, self.store)

    def test_it_does_not_retrieve_schema_urls_from_the_network(self):
        ref = Draft3Validator.META_SCHEMA["id"]
        with mock.patch.object(self.resolver, "resolve_remote") as remote:
            resolved = self.resolver.resolve(ref)

        self.assertEqual(resolved, Draft3Validator.META_SCHEMA)
        self.assertFalse(remote.called)

    def test_it_resolves_local_refs(self):
        ref = "#/properties/foo"
        self.referrer["properties"] = {"foo" : object()}
        resolved = self.resolver.resolve(ref)
        self.assertEqual(resolved, self.referrer["properties"]["foo"])

    def test_it_retrieves_stored_refs(self):
        ref = self.resolver.store["cached_ref"] = {"foo" : 12}
        resolved = self.resolver.resolve("cached_ref#/foo")
        self.assertEqual(resolved, 12)

    def test_it_retrieves_unstored_refs_via_urlopen(self):
        ref = "http://bar#baz"
        schema = {"baz" : 12}

        with mock.patch("jsonschema.urlopen") as urlopen:
            urlopen.return_value.read.return_value = json.dumps(schema)
            resolved = self.resolver.resolve(ref)

        self.assertEqual(resolved, 12)
        urlopen.assert_called_once_with("http://bar")

    def test_it_can_construct_a_base_uri_from_a_schema(self):
        schema = {"id" : "foo"}
        resolver = RefResolver.from_schema(schema)
        self.assertEqual(resolver.base_uri, "foo")
        self.assertEqual(resolver.referrer, schema)

    def test_it_can_construct_a_base_uri_from_a_schema_without_id(self):
        schema = {}
        resolver = RefResolver.from_schema(schema)
        self.assertEqual(resolver.base_uri, "")
        self.assertEqual(resolver.referrer, schema)


def sorted_errors(errors):
    def key(error) : return ([str(e) for e in error.path], error.validator)
    return sorted(errors, key=key)
