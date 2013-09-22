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
            [["foo", "bar"], ["foo"]],
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
            [["foo"], []],
        )

    def test_oneOf_and_anyOf_are_weak_matches(self):
        """
        A property you *must* match is probably better than one you have to
        match a part of.

        """

        validator = Draft4Validator(
            {
                "minProperties" : 2,
                "oneOf" : [{"type" : "string"}, {"type" : "number"}],
            }
        )
        errors = sorted(validator.iter_errors({}))
        self.assertEqual(
            [error.validator for error in errors], ["oneOf", "minProperties"],
        )

    def test_cannot_sort_errors_of_mixed_types(self):
        with self.assertRaises(TypeError):
            v = exceptions.ValidationError("Oh", instance=3)
            s = exceptions.SchemaError("No!", instance=3)
            v < s


class TestBestMatch(unittest.TestCase):
    def test_for_errors_without_context_it_returns_the_max(self):
        """
        The ``max`` will be the error which is most "shallow" in the instance.

        """

        validator = Draft4Validator(
            {
                "properties" : {
                    "foo" : {
                        "minProperties" : 2,
                        "properties" : {"bar" : {"type" : "object"}},
                    },
                },
            }
        )
        errors = sorted(validator.iter_errors({"foo" : {"bar" : []}}))
        self.assertIs(exceptions.best_match(errors), errors[-1])

    def test_context_for_anyOf(self):
        """
        For the anyOf validator, we use the min, to assume the least.

        Other errors are not necessarily relevant, since only one needs to
        match.

        """

        validator = Draft4Validator(
            {
                "properties" : {
                    "foo" : {
                        "anyOf" : [
                            {"type" : "string"},
                            {"properties" : {"bar" : {"type" : "array"}}},
                        ],
                    },
                },
            },
        )
        errors = validator.iter_errors({"foo" : {"bar" : 12}})
        best = exceptions.best_match(errors)
        self.assertEqual(best.validator_value, "array")

    def test_context_for_oneOf(self):
        """
        For the oneOf validator, we use the min, to assume the least.

        Other errors are not necessarily relevant, since only one needs to
        match.

        """

        validator = Draft4Validator(
            {
                "properties" : {
                    "foo" : {
                        "oneOf" : [
                            {"type" : "string"},
                            {"properties" : {"bar" : {"type" : "array"}}},
                        ],
                    },
                },
            },
        )
        errors = validator.iter_errors({"foo" : {"bar" : 12}})
        best = exceptions.best_match(errors)
        self.assertEqual(best.validator_value, "array")

    def test_context_for_allOf(self):
        """
        allOf just yields all the errors globally, so each should be considered

        """

        validator = Draft4Validator(
            {
                "properties" : {
                    "foo" : {
                        "allOf" : [
                            {"type" : "string"},
                            {"properties" : {"bar" : {"type" : "array"}}},
                        ],
                    },
                },
            },
        )
        errors = validator.iter_errors({"foo" : {"bar" : 12}})
        best = exceptions.best_match(errors)
        self.assertEqual(best.validator_value, "string")

    def test_nested_context_for_oneOf(self):
        validator = Draft4Validator(
            {
                "properties" : {
                    "foo" : {
                        "oneOf" : [
                            {"type" : "string"},
                            {
                                "oneOf" : [
                                    {"type" : "string"},
                                    {
                                        "properties" : {
                                            "bar" : {"type" : "array"}
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                },
            },
        )
        errors = validator.iter_errors({"foo" : {"bar" : 12}})
        best = exceptions.best_match(errors)
        self.assertEqual(best.validator_value, "array")

    def test_one_error(self):
        validator = Draft4Validator({"minProperties" : 2})
        error, = validator.iter_errors({})
        self.assertEqual(
            exceptions.best_match(validator.iter_errors({})), error,
        )

    def test_no_errors(self):
        validator = Draft4Validator({})
        self.assertIsNone(exceptions.best_match(validator.iter_errors({})))
