from __future__ import unicode_literals

import unittest

from jsons import ValidationError, validate


class TestValidate(unittest.TestCase):
    def validate_test(self, valids=(), invalids=(), **schema):
        for valid in valids:
            validate(valid, schema)

        for invalid in invalids:
            with self.assertRaises(ValidationError):
                validate(invalid, schema)

    def type_test(self, type, valids, invalids):
        self.validate_test(valids=valids, invalids=invalids, type=type)

    def test_type_integer(self):
        self.type_test("integer", [1], [1.1, "foo", {}, [], True, None])

    def test_type_number(self):
        self.type_test("number", [1, 1.1], ["foo", {}, [], True, None])

    def test_type_string(self):
        self.type_test("string", ["foo"], [1, 1.1, {}, [], True, None])

    def test_type_object(self):
        self.type_test("object", [{}], [1, 1.1, "foo", [], True, None])

    def test_type_array(self):
        self.type_test("array", [[]], [1, 1.1, "foo", {}, True, None])

    def test_type_boolean(self):
        self.type_test(
            "boolean", [True, False], [1, 1.1, "foo", {}, [], None]
        )

    def test_type_null(self):
        self.type_test("null", [None], [1, 1.1, "foo", {}, [], True])

    def test_type_any(self):
        self.type_test("any", [1, 1.1, "foo", {}, [], True, None], [])

    def test_multiple_types(self):
        self.type_test(
            ["integer", "string"], [1, "foo"], [1.1, {}, [], True, None]
        )

    def test_multiple_types_subschema(self):
        self.type_test(
            ["array", {"type" : "object"}],
            [[1, 2], {"foo" : "bar"}],
            [1.1, True, None]
        )

        self.type_test(
            ["integer", {"properties" : {"foo" : {"type" : "null"}}}],
            [1, {"foo" : None}],
            [{"foo" : 1}, {"foo" : 1.1}],
        )

    def test_properties(self):
        schema = {
            "properties" : {
                "foo" : {"type" : "number"},
                "bar" : {"type" : "string"},
            }
        }

        valids = [
            {"foo" : 1, "bar" : "baz"},
            {"foo" : 1, "bar" : "baz", "quux" : 42},
        ]

        self.validate_test(valids, [{"foo" : 1, "bar" : []}], **schema)

    def test_patternProperties(self):
        self.validate_test(
            [{"foo" : 1}, {"foo" : 1, "fah" : 2, "bar" : "baz"}],
            [{"foo" : "bar"}, {"foo" : 1, "fah" : "bar"}],
            patternProperties={"f.*" : {"type" : "integer"}},
        )

    def test_multiple_patternProperties(self):
        pattern = {"a*" : {"type" : "integer"}, "aaa*" : {"maximum" : 20}}
        self.validate_test(
            [{"a" : 1}, {"a" : 21}, {"aaaa" : 18}],
            [{"aaa" : "foo"}, {"aaaa" : 31}],
            patternProperties=pattern,
        )

    def test_additionalProperties(self):
        ex = {"foo" : 1, "bar" : "baz", "quux" : False}
        schema = {
            "properties" : {
                "foo" : {"type" : "number"},
                "bar" : {"type" : "string"},
            }
        }

        validate(ex, schema)

        with self.assertRaises(ValidationError):
            validate(ex, dict(additionalProperties=False, **schema))

        invalids = [{"foo" : 1, "bar" : "baz", "quux" : "boom"}]
        additional = {"type" : "boolean"}

        self.validate_test(
            [ex], invalids, additionalProperties=additional, **schema
        )

    def test_items(self):
        validate([1, "foo", False], {"type" : "array"})
        self.validate_test([[1, 2, 3]], [[1, "x"]], items={"type" : "integer"})

    def test_items_tuple_typing(self):
        items = [{"type" : "integer"}, {"type" : "string"}]
        self.validate_test([[1, "foo"]], [["foo", 1], [1, False]], items=items)

    def test_additionalItems(self):
        schema = {"items" : [{"type" : "integer"}, {"type" : "string"}]}

        validate([1, "foo", False], schema)

        self.validate_test(
            [[1, "foo"]], [[1, "foo", False]], additionalItems=False, **schema
        )

        self.validate_test(
            [[1, "foo", 3]],
            [[1, "foo", "bar"]],
            additionalItems={"type" : "integer"},
            **schema
        )

    def test_required(self):
        schema = {
            "properties" : {
                "foo" : {"type" : "number"},
                "bar" : {"type" : "string"},
            }
        }

        validate({"foo" : 1}, schema)

        schema["properties"]["foo"]["required"] = False

        validate({"foo" : 1}, schema)

        schema["properties"]["foo"]["required"] = True
        schema["properties"]["bar"]["required"] = True

        with self.assertRaises(ValidationError):
            validate({"foo" : 1}, schema)

    def test_dependencies(self):
        schema = {"properties" : {"bar" : {"dependencies" : "foo"}}}
        self.validate_test(
            [{}, {"foo" : 1}, {"foo" : 1, "bar" : 2}], [{"bar" : 2}], **schema
        )

    def test_multiple_dependencies(self):
        schema = {
            "properties" : {
                "quux" : {"dependencies" : ["foo", "bar"]}
            }
        }

        valids = [
            {},
            {"foo" : 1},
            {"foo" : 1, "bar" : 2},
            {"foo" : 1, "bar" : 2, "quux" : 3},
        ]

        invalids = [
            {"foo" : 1, "quux" : 2},
            {"bar" : 1, "quux" : 2},
            {"quux" : 1},
        ]

        self.validate_test(valids, invalids, **schema)

    def test_multiple_dependencies_subschema(self):
        dependencies = {
            "properties" : {
                "foo" : {"type" : "integer"},
                "bar" : {"type" : "integer"},
            }
        }

        schema = {"properties" : {"bar" : {"dependencies" : dependencies}}}

        self.validate_test(
            [{"foo" : 1, "bar" : 2}], [{"foo" : "quux", "bar" : 2}], **schema
        )

    def test_minimum(self):
        self.validate_test([2.6], [.6], minimum=1.2)
        self.validate_test(invalids=[1.2], minimum=1.2, exclusiveMinimum=True)

    def test_maximum(self):
        self.validate_test([2.7], [3.5], maximum=3.0)
        self.validate_test(invalids=[3.0], maximum=3.0, exclusiveMaximum=True)

    def test_minItems(self):
        self.validate_test([[1, 2], [1]], [[]], minItems=1)

    def test_maxItems(self):
        self.validate_test([[1, 2], [1], []], [[1, 2, 3]], maxItems=2)

    def test_uniqueItems(self):
        pass

    def test_minLength(self):
        self.validate_test(["foo"], ["f"], minLength=2)

    def test_maxLength(self):
        self.validate_test(["f"], ["foo"], maxLength=2)

    # Test that only the types that are json-loaded validate (e.g. bytestrings)
