from unittest import TestCase

from jsonschema._annotation import Annotator
from jsonschema.exceptions import UnknownType
from jsonschema.validators import _LATEST_VERSION, extend


class TestAnnotator(TestCase):
    def test_descend(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        errors = {
            error.message
            for error in annotator.descend(instance=37, schema=False)
        }
        self.assertEqual(errors, {"False schema does not allow 37"})

    def test_descend_multiple_errors(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        errors = {
            error.message
            for error in annotator.descend(
                instance=37,
                schema={"type": "string", "minimum": 38},
            )
        }
        self.assertEqual(
            errors, {
                "37 is less than the minimum of 38",
                "37 is not of type 'string'",
            },
        )

    def test_descend_extend_path(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        errors = {
            (
                error.message,
                tuple(error.absolute_path),
                tuple(error.absolute_schema_path),
            ) for error in annotator.descend(
                instance={"b": {"c": 37}},
                schema={
                    "properties": {"b": {"const": "a"}},
                    "minProperties": 2,
                },
                path="a",
            )
        }
        self.assertEqual(
            errors, {
                (
                    "{'b': {'c': 37}} does not have enough properties",
                    ("a",),
                    ("minProperties",)
                ),
                (
                    "'a' was expected",
                    ("a", "b"),
                    ("properties", "b", "const"),
                ),
            },
        )

    def test_descend_extend_schema_path(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        errors = {
            (
                error.message,
                tuple(error.absolute_path),
                tuple(error.absolute_schema_path),
            ) for error in annotator.descend(
                instance={"b": {"c": 37}},
                schema={
                    "properties": {"b": {"const": "a"}},
                    "minProperties": 2,
                },
                schema_path="no37",
            )
        }
        self.assertEqual(
            errors, {
                (
                    "{'b': {'c': 37}} does not have enough properties",
                    (),
                    ("no37", "minProperties")
                ),
                (
                    "'a' was expected",
                    ("b",),
                    ("no37", "properties", "b", "const"),
                ),
            },
        )

    def test_descend_extend_both_paths(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        errors = {
            (
                error.message,
                tuple(error.absolute_path),
                tuple(error.absolute_schema_path),
            ) for error in annotator.descend(
                instance={"b": {"c": 37}},
                schema={
                    "properties": {"b": {"const": "a"}},
                    "minProperties": 2,
                },
                path="foo",
                schema_path="no37",
            )
        }
        self.assertEqual(
            errors, {
                (
                    "{'b': {'c': 37}} does not have enough properties",
                    ("foo",),
                    ("no37", "minProperties")
                ),
                (
                    "'a' was expected",
                    ("foo", "b"),
                    ("no37", "properties", "b", "const"),
                ),
            },
        )

    def test_is_type(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        self.assertTrue(annotator.is_type("foo", "string"))

    def test_is_not_type(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        self.assertFalse(annotator.is_type(37, "string"))

    def test_is_unknown_type(self):
        annotator = Annotator(validator=_LATEST_VERSION({}))
        with self.assertRaises(UnknownType) as e:
            self.assertFalse(annotator.is_type(37, "boopety"))
        self.assertEqual(
            vars(e.exception),
            {"type": "boopety", "instance": 37, "schema": {}},
        )

    def test_repr(self):
        validator = extend(_LATEST_VERSION)({})
        annotator = Annotator(validator=validator)
        self.assertEqual(
            repr(annotator),
            "Annotator(_validator=<Validator>)",
        )

    def test_it_does_not_allow_subclassing(self):
        with self.assertRaises(RuntimeError) as e:
            class NoNo(Annotator):
                pass
        self.assertIn("support subclassing", str(e.exception))
