from jsonschema import Draft4Validator, exceptions
from jsonschema.tests.compat import mock, unittest


class TestValidationErrorSorting(unittest.TestCase):
    def test_shallower_errors_are_better_matches(self):
        validator = Draft4Validator(
            {
                "properties" : {
                    "foo" : {
                        "minProperties" : 2,
                        "properties" : {"bar" : {"type" : "object"}},
                    }
                }
            }
        )
        errors = sorted(validator.iter_errors({"foo" : {"bar" : []}}))
        self.assertEqual(
            [list(error.path) for error in errors],
            [["foo"], ["foo", "bar"]],
        )

    def test_global_errors_are_even_better_matches(self):
        validator = Draft4Validator(
            {
                "minProperties" : 2,
                "properties" : {"foo" : {"type" : "array"}},
            }
        )
        errors = sorted(validator.iter_errors({"foo" : {"bar" : []}}))
        self.assertEqual(
            [list(error.path) for error in errors],
            [[], ["foo"]],
        )

    def test_cannot_sort_errors_of_mixed_types(self):
        with self.assertRaises(TypeError):
            v = exceptions.ValidationError("Oh", instance=3)
            s = exceptions.SchemaError("No!", instance=3)
            v < s
