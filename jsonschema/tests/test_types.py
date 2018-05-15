"""
Tests on the new type interface. The actual correctness of the type checking
is handled in test_jsonschema_test_suite; these tests check that TypeChecker
functions correctly and can facilitate extensions to type checking
"""
from collections import namedtuple
from unittest import TestCase

from jsonschema import _types, ValidationError, _validators
from jsonschema.exceptions import UndefinedTypeCheck
from jsonschema.validators import Draft4Validator, extend


def is_int_or_string_int(checker, instance):
    if Draft4Validator.TYPE_CHECKER.is_type(instance, "integer"):
        return True

    if checker.is_type(instance, "string"):
        try:
            int(instance)
            return True
        except ValueError:
            pass
    return False


def is_namedtuple(instance):
    if isinstance(instance, tuple) and getattr(instance, '_fields',
                                               None):
        return True

    return False


def is_object_or_named_tuple(checker, instance):
    if Draft4Validator.TYPE_CHECKER.is_type(instance, "object"):
        return True

    if is_namedtuple(instance):
        return True

    return False


def coerce_named_tuple(fn):
    def coerced(validator, value, instance, schema):
        if is_namedtuple(instance):
            instance = instance._asdict()
        return fn(validator, value, instance, schema)
    return coerced


required = coerce_named_tuple(_validators.required)
properties = coerce_named_tuple(_validators.properties)


class TestTypeChecker(TestCase):

    def test_initialised_empty(self):
        tc = _types.TypeChecker()
        self.assertEqual(len(tc._type_checkers), 0)

    def test_checks_can_be_added_at_init(self):
        tc = _types.TypeChecker({"integer": _types.is_integer})
        self.assertEqual(len(tc._type_checkers), 1)

    def test_checks_can_be_added(self):
        tc = _types.TypeChecker()
        tc = tc.redefine("integer", _types.is_integer)
        self.assertEqual(len(tc._type_checkers), 1)

    def test_added_checks_are_accessible(self):
        tc = _types.TypeChecker()
        tc = tc.redefine("integer", _types.is_integer)

        self.assertTrue(tc.is_type(4, "integer"))
        self.assertFalse(tc.is_type(4.4, "integer"))

    def test_checks_can_be_redefined(self):
        tc = _types.TypeChecker()
        tc = tc.redefine("integer", _types.is_integer)
        self.assertEqual(tc._type_checkers["integer"], _types.is_integer)
        tc = tc.redefine("integer", _types.is_string)
        self.assertEqual(tc._type_checkers["integer"], _types.is_string)

    def test_checks_can_be_removed(self):
        tc = _types.TypeChecker()
        tc = tc.redefine("integer", _types.is_integer)
        tc = tc.remove("integer")

        with self.assertRaises(UndefinedTypeCheck):
            tc.is_type(4, "integer")

    def test_changes_do_not_affect_original(self):
        tc = _types.TypeChecker()
        tc2 = tc.redefine("integer", _types.is_integer)
        self.assertEqual(len(tc._type_checkers), 0)

        tc2.remove("integer")
        self.assertEqual(len(tc2._type_checkers), 1)

    def test_many_checks_can_be_added(self):
        tc = _types.TypeChecker()
        tc = tc.redefine_many(
            {"integer": _types.is_integer, "string": _types.is_string},
        )

        self.assertEqual(len(tc._type_checkers), 2)

    def test_many_checks_can_be_removed(self):
        tc = _types.TypeChecker()
        tc = tc.redefine_many(
            {"integer": _types.is_integer, "string": _types.is_string},
        )

        tc = tc.remove_many(("integer", "string"))

        self.assertEqual(len(tc._type_checkers), 0)

    def test_unknown_type_raises_exception_on_is_type(self):
        tc = _types.TypeChecker()
        with self.assertRaises(UndefinedTypeCheck) as context:
            tc.is_type(4, 'foobar')

        self.assertIn('foobar', str(context.exception))

    def test_unknown_type_raises_exception_on_remove(self):
        tc = _types.TypeChecker()
        with self.assertRaises(UndefinedTypeCheck) as context:
            tc.remove('foobar')

        self.assertIn('foobar', str(context.exception))

    def test_type_check_can_raise_key_error(self):
        def raises_keyerror(checker, instance):
            raise KeyError("internal error")

        tc = _types.TypeChecker({"object": raises_keyerror})

        with self.assertRaises(KeyError) as context:
            tc.is_type(4, "object")

        self.assertNotIn("object", str(context.exception))
        self.assertIn("internal error", str(context.exception))


class TestCustomTypes(TestCase):

    def test_simple_type_can_be_extended(self):
        schema = {'type': 'integer'}

        type_checker = Draft4Validator.TYPE_CHECKER.redefine(
            "integer", is_int_or_string_int
        )

        CustomValidator = extend(Draft4Validator, type_checker=type_checker)
        v = CustomValidator(schema)

        v.validate(4)
        v.validate('4')

        with self.assertRaises(ValidationError):
            v.validate(4.4)

    def test_object_can_be_extended(self):
        schema = {'type': 'object'}

        Point = namedtuple('Point', ['x', 'y'])

        type_checker = Draft4Validator.TYPE_CHECKER.redefine(
            u"object", is_object_or_named_tuple
        )

        CustomValidator = extend(Draft4Validator, type_checker=type_checker)
        v = CustomValidator(schema)

        v.validate(Point(x=4, y=5))

    def test_object_extensions_require_custom_validators(self):
        schema = {"type": "object", "required": ["x"]}

        type_checker = Draft4Validator.TYPE_CHECKER.redefine(
            u"object", is_object_or_named_tuple
        )

        CustomValidator = extend(Draft4Validator, type_checker=type_checker)
        v = CustomValidator(schema)

        Point = namedtuple("Point", ["x", "y"])
        # Cannot handle required
        with self.assertRaises(ValidationError):
            v.validate(Point(x=4, y=5))

    def test_object_extensions_can_handle_custom_validators(self):
        schema = {
            "type": "object",
            "required": ["x"],
            "properties": {"x": {"type": "integer"}},
        }

        type_checker = Draft4Validator.TYPE_CHECKER.redefine(
            u"object", is_object_or_named_tuple
        )

        CustomValidator = extend(
            Draft4Validator,
            type_checker=type_checker,
            validators={"required": required, "properties": properties},
        )

        v = CustomValidator(schema)

        Point = namedtuple("Point", ["x", "y"])
        # Can now process required and properties
        v.validate(Point(x=4, y=5))

        with self.assertRaises(ValidationError):
            v.validate(Point(x="not an integer", y=5))
