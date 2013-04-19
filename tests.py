from __future__ import unicode_literals
from decimal import Decimal
import contextlib
import glob
import io
import json
import os
import pprint
import re
import subprocess
import sys
import textwrap

if sys.version_info[:2] < (2, 7):  # pragma: no cover
    import unittest2 as unittest
else:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

try:
    from sys import pypy_version_info
except ImportError:
    pypy_version_info = None

from jsonschema import (
    PY3, FormatError, RefResolutionError, SchemaError, UnknownType,
    ValidationError, ErrorTree, Draft3Validator, Draft4Validator,
    FormatChecker, RefResolver, ValidatorMixin, draft3_format_checker,
    draft4_format_checker, validate,
)


THIS_DIR = os.path.dirname(__file__)
TESTS_DIR = os.path.join(THIS_DIR, "json", "tests")

JSONSCHEMA_SUITE = os.path.join(THIS_DIR, "json", "bin", "jsonschema_suite")

REMOTES = subprocess.Popen(
    ["python", JSONSCHEMA_SUITE, "remotes"], stdout=subprocess.PIPE,
).stdout
if PY3:
    REMOTES = io.TextIOWrapper(REMOTES)
REMOTES = json.load(REMOTES)


def make_case(schema, data, valid):
    if valid:
        def test_case(self):
            kwargs = getattr(self, "validator_kwargs", {})
            validate(data, schema, cls=self.validator_class, **kwargs)
    else:
        def test_case(self):
            kwargs = getattr(self, "validator_kwargs", {})
            with self.assertRaises(ValidationError):
                validate(data, schema, cls=self.validator_class, **kwargs)
    return test_case


def load_json_cases(tests_glob, ignore_glob="", basedir=TESTS_DIR, skip=None):
    if ignore_glob:
        ignore_glob = os.path.join(basedir, ignore_glob)

    def add_test_methods(test_class):
        ignored = set(glob.iglob(ignore_glob))

        for filename in glob.iglob(os.path.join(basedir, tests_glob)):
            if filename in ignored:
                continue

            validating, _ = os.path.splitext(os.path.basename(filename))

            with open(filename) as test_file:
                data = json.load(test_file)

                for case in data:
                    for test in case["tests"]:
                        a_test = make_case(
                            case["schema"],
                            test["data"],
                            test["valid"],
                        )

                        test_name = "test_%s_%s" % (
                            validating,
                            re.sub(r"[\W ]+", "_", test["description"]),
                        )

                        if not PY3:
                            test_name = test_name.encode("utf-8")
                        a_test.__name__ = test_name

                        if skip is not None and skip(case):
                            a_test = unittest.skip("Checker not present.")(
                                a_test
                            )

                        setattr(test_class, test_name, a_test)

        return test_class
    return add_test_methods


class TypesMixin(object):
    @unittest.skipIf(PY3, "In Python 3 json.load always produces unicode")
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


def missing_format(checker):
    def missing_format(case):
        format = case["schema"].get("format")
        return format not in checker.checkers or (
            # datetime.datetime is overzealous about typechecking in <=1.9
            format == "date-time" and
            pypy_version_info is not None and
            pypy_version_info[:2] <= (1, 9)
        )
    return missing_format


class FormatMixin(object):
    def test_it_returns_true_for_formats_it_does_not_know_about(self):
        validator = self.validator_class(
            {"format" : "carrot"}, format_checker=FormatChecker(),
        )
        validator.validate("bugs")

    def test_it_does_not_validate_formats_by_default(self):
        validator = self.validator_class({})
        self.assertIsNone(validator.format_checker)

    def test_it_validates_formats_if_a_checker_is_provided(self):
        checker = mock.Mock(spec=FormatChecker)
        validator = self.validator_class(
            {"format" : "foo"}, format_checker=checker,
        )

        validator.validate("bar")

        checker.check.assert_called_once_with("bar", "foo")

        cause = ValueError()
        checker.check.side_effect = FormatError('aoeu', cause=cause)

        with self.assertRaises(ValidationError) as cm:
            validator.validate("bar")
        # Make sure original cause is attached
        self.assertIs(cm.exception.cause, cause)


@load_json_cases(
    "draft3/*.json", ignore_glob=os.path.join("draft3", "refRemote.json")
)
@load_json_cases(
    "draft3/optional/format.json", skip=missing_format(draft3_format_checker)
)
@load_json_cases("draft3/optional/bignum.json")
@load_json_cases("draft3/optional/zeroTerminatedFloats.json")
class TestDraft3(
    unittest.TestCase, TypesMixin, DecimalMixin, FormatMixin
):

    validator_class = Draft3Validator
    validator_kwargs = {"format_checker" : draft3_format_checker}

    def test_any_type_is_valid_for_type_any(self):
        validator = self.validator_class({"type" : "any"})
        validator.validate(mock.Mock())

    # TODO: we're in need of more meta schema tests
    def test_invalid_properties(self):
        with self.assertRaises(SchemaError):
            validate({}, {"properties": {"test": True}},
                     cls=self.validator_class)

    def test_minItems_invalid_string(self):
        with self.assertRaises(SchemaError):
            # needs to be an integer
            validate([1], {"minItems" : "1"}, cls=self.validator_class)


@load_json_cases(
    "draft4/*.json", ignore_glob=os.path.join("draft4", "refRemote.json")
)
@load_json_cases(
    "draft4/optional/format.json", skip=missing_format(draft4_format_checker)
)
@load_json_cases("draft4/optional/bignum.json")
@load_json_cases("draft4/optional/zeroTerminatedFloats.json")
class TestDraft4(
    unittest.TestCase, TypesMixin, DecimalMixin, FormatMixin
):
    validator_class = Draft4Validator
    validator_kwargs = {"format_checker" : draft4_format_checker}

    # TODO: we're in need of more meta schema tests
    def test_invalid_properties(self):
        with self.assertRaises(SchemaError):
            validate({}, {"properties": {"test": True}},
                     cls=self.validator_class)

    def test_minItems_invalid_string(self):
        with self.assertRaises(SchemaError):
            # needs to be an integer
            validate([1], {"minItems" : "1"}, cls=self.validator_class)


class RemoteRefResolutionMixin(object):
    def setUp(self):
        patch = mock.patch("jsonschema.requests")
        requests = patch.start()
        requests.get.side_effect = self.resolve
        self.addCleanup(patch.stop)

    def resolve(self, reference):
        _, _, reference = reference.partition("http://localhost:1234/")
        return mock.Mock(**{"json.return_value" : REMOTES.get(reference)})


@load_json_cases("draft3/refRemote.json")
class Draft3RemoteResolution(RemoteRefResolutionMixin, unittest.TestCase):
    validator_class = Draft3Validator


@load_json_cases("draft4/refRemote.json")
class Draft4RemoteResolution(RemoteRefResolutionMixin, unittest.TestCase):
    validator_class = Draft4Validator


class TestIterErrors(unittest.TestCase):
    def setUp(self):
        self.validator = Draft3Validator({})

    def test_iter_errors(self):
        instance = [1, 2]
        schema = {
            "disallow" : "array",
            "enum" : [["a", "b", "c"], ["d", "e", "f"]],
            "minItems" : 3
        }

        got = (e.message for e in self.validator.iter_errors(instance, schema))
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


class TestValidationErrorMessages(unittest.TestCase):
    def message_for(self, instance, schema, *args, **kwargs):
        kwargs.setdefault("cls", Draft3Validator)
        with self.assertRaises(ValidationError) as e:
            validate(instance, schema, *args, **kwargs)
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

    def test_invalid_format_default_message(self):
        checker = FormatChecker(formats=())
        check_fn = mock.Mock(return_value=False)
        checker.checks("thing")(check_fn)

        schema = {"format" : "thing"}
        message = self.message_for("bla", schema, format_checker=checker)

        self.assertIn(repr("bla"), message)
        self.assertIn(repr("thing"), message)
        self.assertIn("is not a", message)


class TestErrorReprStr(unittest.TestCase):

    message = "hello"

    def setUp(self):
        self.error = ValidationError(
            message=self.message,
            validator="type",
            validator_value="string",
            instance=5,
            schema={"type" : "string"},
        )

    def assertShows(self, message):
        if PY3:
            message = message.replace("u'", "'")
        message = textwrap.dedent(message).rstrip("\n")

        message_line, _, rest = str(self.error).partition("\n")
        self.assertEqual(message_line, self.message)
        self.assertEqual(rest, message)

    def test_repr(self):
        self.assertEqual(
            repr(self.error),
            "<ValidationError: %r>" % self.message,
        )

    def test_unset_error(self):
        error = ValidationError("message")
        self.assertEqual(str(error), "message")

        kwargs = {
            "validator": "type",
            "validator_value": "string",
            "instance": 5,
            "schema": {"type": "string"}
        }
        # Just the message should show if any of the attributes are unset
        for attr in kwargs:
            k = dict(kwargs)
            del k[attr]
            error = ValidationError("message", **k)
            self.assertEqual(str(error), "message")

    def test_empty_paths(self):
        self.error.path = self.error.schema_path = []
        self.assertShows(
            """
            Failed validating u'type' in schema:
                {u'type': u'string'}

            On instance:
                5
            """
        )

    def test_one_item_paths(self):
        self.error.path = [0]
        self.error.schema_path = ["items"]
        self.assertShows(
            """
            Failed validating u'type' in schema:
                {u'type': u'string'}

            On instance[0]:
                5
            """
        )

    def test_multiple_item_paths(self):
        self.error.path = [0, "a"]
        self.error.schema_path = ["items", 0, 1]
        self.assertShows(
            """
            Failed validating u'type' in schema[u'items'][0]:
                {u'type': u'string'}

            On instance[0][u'a']:
                5
            """
        )

    def test_uses_pprint(self):
        with mock.patch.object(pprint, "pformat") as pformat:
            str(self.error)
            self.assertGreater(pformat.call_count, 1)  # schema + instance


class TestValidationErrorDetails(unittest.TestCase):
    def setUp(self):
        self.validator = Draft3Validator({})

    # TODO: These really need unit tests for each individual validator, rather
    #       than just these higher level tests.
    def test_anyOf(self):
        instance = 5
        schema = {
            "anyOf": [
                {"minimum": 20},
                {"type": "string"}
            ]
        }

        validator = Draft4Validator(schema)
        errors = list(validator.iter_errors(instance))
        self.assertEqual(len(errors), 1)
        e = errors[0]

        self.assertEqual(e.validator, "anyOf")
        self.assertEqual(list(e.schema_path), ["anyOf"])
        self.assertEqual(e.validator_value, schema["anyOf"])
        self.assertEqual(e.instance, instance)
        self.assertEqual(e.schema, schema)
        self.assertEqual(list(e.path), [])
        self.assertEqual(len(e.context), 2)

        e1, e2 = sorted_errors(e.context)

        self.assertEqual(e1.validator, "minimum")
        self.assertEqual(list(e1.schema_path), [0, "minimum"])
        self.assertEqual(e1.validator_value, schema["anyOf"][0]["minimum"])
        self.assertEqual(e1.instance, instance)
        self.assertEqual(e1.schema, schema["anyOf"][0])
        self.assertEqual(list(e1.path), [])
        self.assertEqual(len(e1.context), 0)

        self.assertEqual(e2.validator, "type")
        self.assertEqual(list(e2.schema_path), [1, "type"])
        self.assertEqual(e2.validator_value, schema["anyOf"][1]["type"])
        self.assertEqual(e2.instance, instance)
        self.assertEqual(e2.schema, schema["anyOf"][1])
        self.assertEqual(list(e2.path), [])
        self.assertEqual(len(e2.context), 0)

    def test_type(self):
        instance = {"foo": 1}
        schema = {
            "type": [
                {"type": "integer"},
                {
                    "type": "object",
                    "properties": {
                        "foo": {"enum": [2]}
                    }
                }
            ]
        }

        errors = list(self.validator.iter_errors(instance, schema))
        self.assertEqual(len(errors), 1)
        e = errors[0]

        self.assertEqual(e.validator, "type")
        self.assertEqual(list(e.schema_path), ["type"])
        self.assertEqual(e.validator_value, schema["type"])
        self.assertEqual(e.instance, instance)
        self.assertEqual(e.schema, schema)
        self.assertEqual(list(e.path), [])
        self.assertEqual(len(e.context), 2)

        e1, e2 = sorted_errors(e.context)

        self.assertEqual(e1.validator, "type")
        self.assertEqual(list(e1.schema_path), [0, "type"])
        self.assertEqual(e1.validator_value, schema["type"][0]["type"])
        self.assertEqual(e1.instance, instance)
        self.assertEqual(e1.schema, schema["type"][0])
        self.assertEqual(list(e1.path), [])
        self.assertEqual(len(e1.context), 0)

        self.assertEqual(e2.validator, "enum")
        self.assertEqual(
            list(e2.schema_path),
            [1, "properties", "foo", "enum"]
        )
        self.assertEqual(
            e2.validator_value,
            schema["type"][1]["properties"]["foo"]["enum"]
        )
        self.assertEqual(e2.instance, instance["foo"])
        self.assertEqual(e2.schema, schema["type"][1]["properties"]["foo"])
        self.assertEqual(list(e2.path), ["foo"])
        self.assertEqual(len(e2.context), 0)

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

        self.assertEqual(list(e1.path), ["bar"])
        self.assertEqual(list(e2.path), ["baz"])
        self.assertEqual(list(e3.path), ["baz"])
        self.assertEqual(list(e4.path), ["foo"])

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

        self.assertEqual(list(e1.path), [])
        self.assertEqual(list(e2.path), [0])
        self.assertEqual(list(e3.path), [1, "bar"])
        self.assertEqual(list(e4.path), [1, "bar", "bar"])
        self.assertEqual(list(e5.path), [1, "bar", "baz"])
        self.assertEqual(list(e6.path), [1, "foo"])

        self.assertEqual(e1.validator, "type")
        self.assertEqual(e2.validator, "type")
        self.assertEqual(e3.validator, "type")
        self.assertEqual(e4.validator, "required")
        self.assertEqual(e5.validator, "minItems")
        self.assertEqual(e6.validator, "enum")

    def test_additionalProperties(self):
        instance = {"bar": "bar", "foo": 2}
        schema = {
            "additionalProperties" : {"type": "integer", "minimum": 5}
        }

        errors = self.validator.iter_errors(instance, schema)
        e1, e2 = sorted_errors(errors)

        self.assertEqual(list(e1.path), ["bar"])
        self.assertEqual(list(e2.path), ["foo"])

        self.assertEqual(e1.validator, "type")
        self.assertEqual(e2.validator, "minimum")

    def test_patternProperties(self):
        instance = {"bar": 1, "foo": 2}
        schema = {
            "patternProperties" : {
                "bar": {"type": "string"},
                "foo": {"minimum": 5}
            }
        }

        errors = self.validator.iter_errors(instance, schema)
        e1, e2 = sorted_errors(errors)

        self.assertEqual(list(e1.path), ["bar"])
        self.assertEqual(list(e2.path), ["foo"])

        self.assertEqual(e1.validator, "type")
        self.assertEqual(e2.validator, "minimum")

    def test_additionalItems(self):
        instance = ["foo", 1]
        schema = {
            "items": [],
            "additionalItems" : {"type": "integer", "minimum": 5}
        }

        errors = self.validator.iter_errors(instance, schema)
        e1, e2 = sorted_errors(errors)

        self.assertEqual(list(e1.path), [0])
        self.assertEqual(list(e2.path), [1])

        self.assertEqual(e1.validator, "type")
        self.assertEqual(e2.validator, "minimum")


class TestErrorTree(unittest.TestCase):
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
            ValidationError("a bar -> 0 message", path=["bar", 0]),
        ]
        tree = ErrorTree(errors)
        self.assertIn(0, tree["bar"])
        self.assertNotIn(1, tree["bar"])

    def test_children_have_their_errors_dicts_built(self):
        e1, e2 = (
            ValidationError("message 1", validator="foo", path=["bar", 0]),
            ValidationError("message 2", validator="quux", path=["bar", 0]),
        )
        tree = ErrorTree([e1, e2])
        self.assertEqual(tree["bar"][0].errors, {"foo" : e1, "quux" : e2})

    def test_it_does_not_contain_subtrees_that_are_not_in_the_instance(self):
        error = ValidationError("a message", validator="foo", instance=[])
        tree = ErrorTree([error])

        with self.assertRaises(IndexError):
            tree[0]

    def test_if_its_in_the_tree_anyhow_it_does_not_raise_an_error(self):
        """
        If a validator is dumb (like :validator:`required` in draft 3) and
        refers to a path that isn't in the instance, the tree still properly
        returns a subtree for that path.

        """

        error = ValidationError(
            "a message", validator="foo", instance={}, path=["foo"],
        )
        tree = ErrorTree([error])
        self.assertIsInstance(tree["foo"], ErrorTree)


class ValidatorTestMixin(object):
    def setUp(self):
        self.instance = mock.Mock()
        self.schema = {}
        self.resolver = mock.Mock()
        self.validator = self.validator_class(self.schema)

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
        resolver = RefResolver("", {})
        schema = {"$ref" : mock.Mock()}

        @contextlib.contextmanager
        def resolving():
            yield {"type": "integer"}

        with mock.patch.object(resolver, "resolving") as resolve:
            resolve.return_value = resolving()
            with self.assertRaises(ValidationError):
                self.validator_class(schema, resolver=resolver).validate(None)

        resolve.assert_called_once_with(schema["$ref"])

    def test_is_type_is_true_for_valid_type(self):
        self.assertTrue(self.validator.is_type("foo", "string"))

    def test_is_type_is_false_for_invalid_type(self):
        self.assertFalse(self.validator.is_type("foo", "array"))

    def test_is_type_evades_bool_inheriting_from_int(self):
        self.assertFalse(self.validator.is_type(True, "integer"))
        self.assertFalse(self.validator.is_type(True, "number"))

    def test_is_type_raises_exception_for_unknown_type(self):
        with self.assertRaises(UnknownType):
            self.validator.is_type("foo", object())


class TestDraft3Validator(ValidatorTestMixin, unittest.TestCase):
    validator_class = Draft3Validator

    def test_is_type_is_true_for_any_type(self):
        self.assertTrue(self.validator.is_valid(mock.Mock(), {"type": "any"}))

    def test_is_type_does_not_evade_bool_if_it_is_being_tested(self):
        self.assertTrue(self.validator.is_type(True, "boolean"))
        self.assertTrue(self.validator.is_valid(True, {"type": "any"}))


class TestDraft4Validator(ValidatorTestMixin, unittest.TestCase):
    validator_class = Draft4Validator


class TestValidate(unittest.TestCase):
    def test_draft3_validator_is_chosen(self):
        schema = {"$schema" : "http://json-schema.org/draft-03/schema#"}
        with mock.patch.object(Draft3Validator, "check_schema") as chk_schema:
            validate({}, schema)
            chk_schema.assert_called_once_with(schema)
        # Make sure it works without the empty fragment
        schema = {"$schema" : "http://json-schema.org/draft-03/schema"}
        with mock.patch.object(Draft3Validator, "check_schema") as chk_schema:
            validate({}, schema)
            chk_schema.assert_called_once_with(schema)

    def test_draft4_validator_is_chosen(self):
        schema = {"$schema" : "http://json-schema.org/draft-04/schema#"}
        with mock.patch.object(Draft4Validator, "check_schema") as chk_schema:
            validate({}, schema)
            chk_schema.assert_called_once_with(schema)

    def test_draft4_validator_is_the_default(self):
        with mock.patch.object(Draft4Validator, "check_schema") as chk_schema:
            validate({}, {})
            chk_schema.assert_called_once_with({})


class TestValidatorMixin(unittest.TestCase):
    def test_if_ref_is_present_then_the_schema_is_replaced(self):
        class Validator(ValidatorMixin):
            validate_ref = mock.Mock(return_value=[])
            validate_type = mock.Mock(return_value=[])

        Validator({"$ref" : "foo", "type" : "quux"}).validate(1)

        self.assertTrue(Validator.validate_ref.called)
        self.assertFalse(Validator.validate_type.called)


class TestRefResolver(unittest.TestCase):

    base_uri = ""
    stored_uri = "foo://stored"
    stored_schema = {"stored" : "schema"}

    def setUp(self):
        self.referrer = {}
        self.store = {self.stored_uri : self.stored_schema}
        self.resolver = RefResolver(self.base_uri, self.referrer, self.store)

    def test_it_does_not_retrieve_schema_urls_from_the_network(self):
        ref = Draft3Validator.META_SCHEMA["id"]
        with mock.patch.object(self.resolver, "resolve_remote") as remote:
            with self.resolver.resolving(ref) as resolved:
                self.assertEqual(resolved, Draft3Validator.META_SCHEMA)
        self.assertFalse(remote.called)

    def test_it_resolves_local_refs(self):
        ref = "#/properties/foo"
        self.referrer["properties"] = {"foo" : object()}
        with self.resolver.resolving(ref) as resolved:
            self.assertEqual(resolved, self.referrer["properties"]["foo"])

    def test_it_retrieves_stored_refs(self):
        with self.resolver.resolving(self.stored_uri) as resolved:
            self.assertIs(resolved, self.stored_schema)

        self.resolver.store["cached_ref"] = {"foo" : 12}
        with self.resolver.resolving("cached_ref#/foo") as resolved:
            self.assertEqual(resolved, 12)

    def test_it_retrieves_unstored_refs_via_requests(self):
        ref = "http://bar#baz"
        schema = {"baz" : 12}

        with mock.patch("jsonschema.requests") as requests:
            requests.get.return_value.json.return_value = schema
            with self.resolver.resolving(ref) as resolved:
                self.assertEqual(resolved, 12)
        requests.get.assert_called_once_with("http://bar")

    def test_it_retrieves_unstored_refs_via_urlopen(self):
        ref = "http://bar#baz"
        schema = {"baz" : 12}

        with mock.patch("jsonschema.requests", None):
            with mock.patch("jsonschema.urlopen") as urlopen:
                urlopen.return_value.read.return_value = (
                    json.dumps(schema).encode("utf8"))
                with self.resolver.resolving(ref) as resolved:
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

    def test_custom_uri_scheme_handlers(self):
        schema = {"foo": "bar"}
        ref = "foo://bar"
        foo_handler = mock.Mock(return_value=schema)
        resolver = RefResolver("", {}, handlers={"foo": foo_handler})
        with resolver.resolving(ref) as resolved:
            self.assertEqual(resolved, schema)
        foo_handler.assert_called_once_with(ref)

    def test_cache_remote_on(self):
        ref = "foo://bar"
        foo_handler = mock.Mock()
        resolver = RefResolver(
            "", {}, cache_remote=True, handlers={"foo" : foo_handler},
        )
        with resolver.resolving(ref):
            pass
        with resolver.resolving(ref):
            pass
        foo_handler.assert_called_once_with(ref)

    def test_cache_remote_off(self):
        ref = "foo://bar"
        foo_handler = mock.Mock()
        resolver = RefResolver(
            "", {}, cache_remote=False, handlers={"foo" : foo_handler},
        )
        with resolver.resolving(ref):
            pass
        with resolver.resolving(ref):
            pass
        self.assertEqual(foo_handler.call_count, 2)

    def test_if_you_give_it_junk_you_get_a_resolution_error(self):
        ref = "foo://bar"
        foo_handler = mock.Mock(side_effect=ValueError("Oh no! What's this?"))
        resolver = RefResolver("", {}, handlers={"foo" : foo_handler})
        with self.assertRaises(RefResolutionError) as err:
            with resolver.resolving(ref):
                pass
        self.assertEqual(str(err.exception), "Oh no! What's this?")


class TestFormatChecker(unittest.TestCase):
    def setUp(self):
        self.fn = mock.Mock()

    def test_it_can_validate_no_formats(self):
        checker = FormatChecker(formats=())
        self.assertFalse(checker.checkers)

    def test_it_raises_a_key_error_for_unknown_formats(self):
        with self.assertRaises(KeyError):
            FormatChecker(formats=["o noes"])

    def test_it_can_register_cls_checkers(self):
        with mock.patch.dict(FormatChecker.checkers, clear=True):
            FormatChecker.cls_checks("new")(self.fn)
            self.assertEqual(FormatChecker.checkers, {"new" : (self.fn, ())})

    def test_it_can_register_checkers(self):
        checker = FormatChecker()
        checker.checks("new")(self.fn)
        self.assertEqual(
            checker.checkers,
            dict(FormatChecker.checkers, new=(self.fn, ()))
        )

    def test_it_catches_registered_errors(self):
        checker = FormatChecker()
        cause = self.fn.side_effect = ValueError()

        checker.checks("foo", raises=ValueError)(self.fn)

        with self.assertRaises(FormatError) as cm:
            checker.check("bar", "foo")

        self.assertIs(cm.exception.cause, cause)
        self.assertIs(cm.exception.__cause__, cause)

        # Unregistered errors should not be caught
        self.fn.side_effect = AttributeError
        with self.assertRaises(AttributeError):
            checker.check("bar", "foo")

    def test_format_error_causes_become_validation_error_causes(self):
        checker = FormatChecker()
        checker.checks("foo", raises=ValueError)(self.fn)
        cause = self.fn.side_effect = ValueError()
        validator = Draft4Validator({"format" : "foo"}, format_checker=checker)

        with self.assertRaises(ValidationError) as cm:
            validator.validate("bar")

        self.assertIs(cm.exception.__cause__, cause)


def sorted_errors(errors):
    def key(error):
        return (
            [str(e) for e in error.path],
            [str(e) for e in error.schema_path]
        )
    return sorted(errors, key=key)
