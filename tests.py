from __future__ import with_statement

import sys

if (sys.version_info[0], sys.version_info[1]) < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from jsonschema import ValidationError, validate


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
        self.type_test(u"integer", [1], [1.1, u"foo", {}, [], True, None])

    def test_type_number(self):
        self.type_test(u"number", [1, 1.1], [u"foo", {}, [], True, None])

    def test_type_string(self):
        self.type_test(
            u"string", [u"foo", "foo"], [1, 1.1, {}, [], True, None]
        )

    def test_type_object(self):
        self.type_test(u"object", [{}], [1, 1.1, u"foo", [], True, None])

    def test_type_array(self):
        self.type_test(u"array", [[]], [1, 1.1, u"foo", {}, True, None])

    def test_type_boolean(self):
        self.type_test(
            u"boolean", [True, False], [1, 1.1, u"foo", {}, [], None]
        )

    def test_type_null(self):
        self.type_test(u"null", [None], [1, 1.1, u"foo", {}, [], True])

    def test_type_any(self):
        self.type_test(u"any", [1, 1.1, u"foo", {}, [], True, None], [])

    def test_multiple_types(self):
        self.type_test(
            [u"integer", u"string"], [1, u"foo"], [1.1, {}, [], True, None]
        )

    def test_multiple_types_subschema(self):
        self.type_test(
            [u"array", {u"type" : u"object"}],
            [[1, 2], {u"foo" : u"bar"}],
            [1.1, True, None]
        )

        self.type_test(
            [u"integer", {u"properties" : {u"foo" : {u"type" : u"null"}}}],
            [1, {u"foo" : None}],
            [{u"foo" : 1}, {u"foo" : 1.1}],
        )

    def test_properties(self):
        schema = {
            "properties" : {
                u"foo" : {u"type" : u"number"},
                u"bar" : {u"type" : u"string"},
            }
        }

        valids = [
            {u"foo" : 1, u"bar" : u"baz"},
            {u"foo" : 1, u"bar" : u"baz", u"quux" : 42},
        ]

        self.validate_test(valids, [{u"foo" : 1, u"bar" : []}], **schema)

    def test_patternProperties(self):
        self.validate_test(
            [{u"foo" : 1}, {u"foo" : 1, u"fah" : 2, u"bar" : u"baz"}],
            [{u"foo" : u"bar"}, {u"foo" : 1, u"fah" : u"bar"}],
            patternProperties={u"f.*" : {u"type" : u"integer"}},
        )

    def test_multiple_patternProperties(self):
        pattern = {u"a*" : {u"type" : u"integer"}, u"aaa*" : {u"maximum" : 20}}
        self.validate_test(
            [{u"a" : 1}, {u"a" : 21}, {u"aaaa" : 18}],
            [{u"aaa" : u"foo"}, {u"aaaa" : 31}],
            patternProperties=pattern,
        )

    def test_additionalProperties(self):
        ex = {u"foo" : 1, u"bar" : u"baz", u"quux" : False}
        schema = {
            "properties" : {
                u"foo" : {u"type" : u"number"},
                u"bar" : {u"type" : u"string"},
            }
        }

        validate(ex, schema)

        with self.assertRaises(ValidationError):
            validate(ex, dict(additionalProperties=False, **schema))

        invalids = [{u"foo" : 1, u"bar" : u"baz", u"quux" : u"boom"}]
        additional = {u"type" : u"boolean"}

        self.validate_test(
            [ex], invalids, additionalProperties=additional, **schema
        )

    def test_items(self):
        validate([1, u"foo", False], {u"type" : u"array"})
        self.validate_test(
            [[1, 2, 3]], [[1, u"x"]], items={u"type" : u"integer"}
        )

    def test_items_tuple_typing(self):
        items = [{u"type" : u"integer"}, {u"type" : u"string"}]
        self.validate_test(
            [[1, u"foo"]], [[u"foo", 1], [1, False]], items=items
        )

    def test_additionalItems(self):
        schema = {"items" : [{u"type" : u"integer"}, {u"type" : u"string"}]}

        validate([1, u"foo", False], schema)

        self.validate_test(
            [[1, u"foo"]],
            [[1, u"foo", False]],
            additionalItems=False,
            **schema
        )

        self.validate_test(
            [[1, u"foo", 3]],
            [[1, u"foo", u"bar"]],
            additionalItems={u"type" : u"integer"},
            **schema
        )

    def test_required(self):
        schema = {
            u"properties" : {
                u"foo" : {u"type" : u"number"},
                u"bar" : {u"type" : u"string"},
            }
        }

        validate({u"foo" : 1}, schema)

        schema[u"properties"][u"foo"][u"required"] = False

        validate({u"foo" : 1}, schema)

        schema[u"properties"][u"foo"][u"required"] = True
        schema[u"properties"][u"bar"][u"required"] = True

        with self.assertRaises(ValidationError):
            validate({u"foo" : 1}, schema)

    def test_dependencies(self):
        schema = {"properties" : {u"bar" : {u"dependencies" : u"foo"}}}
        self.validate_test(
            [{}, {u"foo" : 1}, {u"foo" : 1, u"bar" : 2}],
            [{u"bar" : 2}],
            **schema
        )

    def test_multiple_dependencies(self):
        schema = {
            "properties" : {
                u"quux" : {u"dependencies" : [u"foo", u"bar"]}
            }
        }

        valids = [
            {},
            {u"foo" : 1},
            {u"foo" : 1, u"bar" : 2},
            {u"foo" : 1, u"bar" : 2, u"quux" : 3},
        ]

        invalids = [
            {u"foo" : 1, u"quux" : 2},
            {u"bar" : 1, u"quux" : 2},
            {u"quux" : 1},
        ]

        self.validate_test(valids, invalids, **schema)

    def test_multiple_dependencies_subschema(self):
        dependencies = {
            "properties" : {
                u"foo" : {u"type" : u"integer"},
                u"bar" : {u"type" : u"integer"},
            }
        }

        schema = {"properties" : {u"bar" : {u"dependencies" : dependencies}}}

        self.validate_test(
            [{u"foo" : 1, u"bar" : 2}],
            [{u"foo" : u"quux", u"bar" : 2}],
            **schema
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

    def test_pattern(self):
        self.validate_test([u"aaa"], [u"ab"], pattern=u"^a*$")

    def test_minLength(self):
        self.validate_test([u"foo"], [u"f"], minLength=2)

    def test_maxLength(self):
        self.validate_test([u"f"], [u"foo"], maxLength=2)

    def test_enum(self):
        self.validate_test([1], [5], enum=[1, 2, 3])
        self.validate_test([u"foo"], [u"quux"], enum=[u"foo", u"bar"])
        self.validate_test([True], [False], enum=[True])
        self.validate_test(
            [{u"foo" : u"bar"}], [{u"foo" : u"baz"}], enum=[{u"foo" : u"bar"}]
        )

    def test_divisibleBy(self):
        self.validate_test([10], [7], divisibleBy=2)
        self.validate_test([10.0], [7.0], divisibleBy=2)
        self.validate_test([.75], [.751], divisibleBy=.01)
        self.validate_test([3.3], [3.5], divisibleBy=1.1)

    # Test that only the types that are json-loaded validate (e.g. bytestrings)
