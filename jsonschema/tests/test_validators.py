from __future__ import unicode_literals
import contextlib
import json
import pprint
import textwrap

from jsonschema import FormatChecker, ValidationError
from jsonschema.compat import PY3
from jsonschema.tests.compat import mock, unittest
from jsonschema.validators import (
    RefResolutionError, UnknownType, ErrorTree, Draft3Validator,
    Draft4Validator, RefResolver, create, extend, validator_for, validate,
)


class TestCreateAndExtend(unittest.TestCase):
    def setUp(self):
        self.meta_schema = {"properties" : {"smelly" : {}}}
        self.smelly = mock.MagicMock()
        self.validators = {"smelly" : self.smelly}
        self.types = {"dict" : dict}
        self.Validator = create(
            meta_schema=self.meta_schema,
            validators=self.validators,
            default_types=self.types,
        )

        self.validator_value = 12
        self.schema = {"smelly" : self.validator_value}
        self.validator = self.Validator(self.schema)

    def test_attrs(self):
        self.assertEqual(self.Validator.VALIDATORS, self.validators)
        self.assertEqual(self.Validator.META_SCHEMA, self.meta_schema)
        self.assertEqual(self.Validator.DEFAULT_TYPES, self.types)

    def test_init(self):
        self.assertEqual(self.validator.schema, self.schema)

    def test_iter_errors(self):
        instance = "hello"

        self.smelly.return_value = []
        self.assertEqual(list(self.validator.iter_errors(instance)), [])

        error = mock.Mock()
        self.smelly.return_value = [error]
        self.assertEqual(list(self.validator.iter_errors(instance)), [error])

        self.smelly.assert_called_with(
            self.validator, self.validator_value, instance, self.schema,
        )

    def test_if_a_version_is_provided_it_is_registered(self):
        with mock.patch("jsonschema.validators.validates") as validates:
            validates.side_effect = lambda version : lambda cls : cls
            Validator = create(meta_schema={"id" : "id"}, version="my version")
        validates.assert_called_once_with("my version")
        self.assertEqual(Validator.__name__, "MyVersionValidator")

    def test_if_a_version_is_not_provided_it_is_not_registered(self):
        with mock.patch("jsonschema.validators.validates") as validates:
            create(meta_schema={"id" : "id"})
        self.assertFalse(validates.called)

    def test_extend(self):
        validators = dict(self.Validator.VALIDATORS)
        new = mock.Mock()

        Extended = extend(self.Validator, validators={"a new one" : new})

        validators.update([("a new one", new)])
        self.assertEqual(Extended.VALIDATORS, validators)
        self.assertNotIn("a new one", self.Validator.VALIDATORS)

        self.assertEqual(Extended.META_SCHEMA, self.Validator.META_SCHEMA)
        self.assertEqual(Extended.DEFAULT_TYPES, self.Validator.DEFAULT_TYPES)


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

        validator = Draft3Validator(schema)
        errors = list(validator.iter_errors(instance))
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

        validator = Draft3Validator(schema)
        errors = validator.iter_errors(instance)
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

        validator = Draft3Validator(schema)
        errors = validator.iter_errors(instance)
        e1, e2, e3, e4, e5, e6 = sorted_errors(errors)

        self.assertEqual(list(e1.path), [])
        self.assertEqual(list(e2.path), [0])
        self.assertEqual(list(e3.path), [1, "bar"])
        self.assertEqual(list(e4.path), [1, "bar", "bar"])
        self.assertEqual(list(e5.path), [1, "bar", "baz"])
        self.assertEqual(list(e6.path), [1, "foo"])

        self.assertEqual(list(e1.schema_path), ["type"])
        self.assertEqual(list(e2.schema_path), ["items", "type"])
        self.assertEqual(
            list(e3.schema_path), ["items", "properties", "bar", "type"],
        )
        self.assertEqual(
            list(e4.schema_path),
            ["items", "properties", "bar", "properties", "bar", "required"],
        )
        self.assertEqual(
            list(e5.schema_path),
            ["items", "properties", "bar", "properties", "baz", "minItems"]
        )
        self.assertEqual(
            list(e6.schema_path), ["items", "properties", "foo", "enum"],
        )

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

        validator = Draft3Validator(schema)
        errors = validator.iter_errors(instance)
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

        validator = Draft3Validator(schema)
        errors = validator.iter_errors(instance)
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

        validator = Draft3Validator(schema)
        errors = validator.iter_errors(instance)
        e1, e2 = sorted_errors(errors)

        self.assertEqual(list(e1.path), [0])
        self.assertEqual(list(e2.path), [1])

        self.assertEqual(e1.validator, "type")
        self.assertEqual(e2.validator, "minimum")

    def test_additionalItems_with_items(self):
        instance = ["foo", "bar", 1]
        schema = {
            "items": [{}],
            "additionalItems" : {"type": "integer", "minimum": 5}
        }

        validator = Draft3Validator(schema)
        errors = validator.iter_errors(instance)
        e1, e2 = sorted_errors(errors)

        self.assertEqual(list(e1.path), [1])
        self.assertEqual(list(e2.path), [2])

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


class TestValidatorFor(unittest.TestCase):
    def test_draft_3(self):
        schema = {"$schema" : "http://json-schema.org/draft-03/schema"}
        self.assertIs(validator_for(schema), Draft3Validator)

        schema = {"$schema" : "http://json-schema.org/draft-03/schema#"}
        self.assertIs(validator_for(schema), Draft3Validator)

    def test_draft_4(self):
        schema = {"$schema" : "http://json-schema.org/draft-04/schema"}
        self.assertIs(validator_for(schema), Draft4Validator)

        schema = {"$schema" : "http://json-schema.org/draft-04/schema#"}
        self.assertIs(validator_for(schema), Draft4Validator)

    def test_custom_validator(self):
        Validator = create(meta_schema={"id" : "meta schema id"}, version="12")
        schema = {"$schema" : "meta schema id"}
        self.assertIs(validator_for(schema), Validator)

    def test_validator_for_jsonschema_default(self):
        self.assertIs(validator_for({}), Draft4Validator)

    def test_validator_for_custom_default(self):
        self.assertIs(validator_for({}, default=None), None)


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

    def test_it_resolves_local_refs_with_id(self):
        schema = {"id": "foo://bar/schema#", "a": {"foo": "bar"}}
        resolver = RefResolver.from_schema(schema)
        with resolver.resolving("#/a") as resolved:
            self.assertEqual(resolved, schema["a"])
        with resolver.resolving("foo://bar/schema#/a") as resolved:
            self.assertEqual(resolved, schema["a"])

    def test_it_retrieves_stored_refs(self):
        with self.resolver.resolving(self.stored_uri) as resolved:
            self.assertIs(resolved, self.stored_schema)

        self.resolver.store["cached_ref"] = {"foo" : 12}
        with self.resolver.resolving("cached_ref#/foo") as resolved:
            self.assertEqual(resolved, 12)

    def test_it_retrieves_unstored_refs_via_requests(self):
        ref = "http://bar#baz"
        schema = {"baz" : 12}

        with mock.patch("jsonschema.validators.requests") as requests:
            requests.get.return_value.json.return_value = schema
            with self.resolver.resolving(ref) as resolved:
                self.assertEqual(resolved, 12)
        requests.get.assert_called_once_with("http://bar")

    def test_it_retrieves_unstored_refs_via_urlopen(self):
        ref = "http://bar#baz"
        schema = {"baz" : 12}

        with mock.patch("jsonschema.validators.requests", None):
            with mock.patch("jsonschema.validators.urlopen") as urlopen:
                urlopen.return_value.read.return_value = (
                    json.dumps(schema).encode("utf8"))
                with self.resolver.resolving(ref) as resolved:
                    self.assertEqual(resolved, 12)
        urlopen.assert_called_once_with("http://bar")

    def test_it_can_construct_a_base_uri_from_a_schema(self):
        schema = {"id" : "foo"}
        resolver = RefResolver.from_schema(schema)
        self.assertEqual(resolver.base_uri, "foo")
        with resolver.resolving("") as resolved:
            self.assertEqual(resolved, schema)
        with resolver.resolving("#") as resolved:
            self.assertEqual(resolved, schema)
        with resolver.resolving("foo") as resolved:
            self.assertEqual(resolved, schema)
        with resolver.resolving("foo#") as resolved:
            self.assertEqual(resolved, schema)

    def test_it_can_construct_a_base_uri_from_a_schema_without_id(self):
        schema = {}
        resolver = RefResolver.from_schema(schema)
        self.assertEqual(resolver.base_uri, "")
        with resolver.resolving("") as resolved:
            self.assertEqual(resolved, schema)
        with resolver.resolving("#") as resolved:
            self.assertEqual(resolved, schema)

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


def sorted_errors(errors):
    def key(error):
        return (
            [str(e) for e in error.path],
            [str(e) for e in error.schema_path]
        )
    return sorted(errors, key=key)
