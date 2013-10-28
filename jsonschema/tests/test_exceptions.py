from jsonschema import Draft4Validator, exceptions
from jsonschema.tests.compat import unittest


class TestBestMatch(unittest.TestCase):
    def best_match(self, errors):
        errors = list(errors)
        best = exceptions.best_match(errors)
        reversed_best = exceptions.best_match(reversed(errors))
        self.assertEqual(
            best,
            reversed_best,
            msg="Didn't return a consistent best match!\n"
                "Got: {0}\n\nThen: {1}".format(best, reversed_best),
        )
        return best

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
        best = self.best_match(validator.iter_errors({"foo" : {"bar" : []}}))
        self.assertEqual(best.validator, "minProperties")

    def test_oneOf_and_anyOf_are_weak_matches(self):
        """
        A property you *must* match is probably better than one you have to
        match a part of.

        """

        validator = Draft4Validator(
            {
                "minProperties" : 2,
                "anyOf" : [{"type" : "string"}, {"type" : "number"}],
                "oneOf" : [{"type" : "string"}, {"type" : "number"}],
            }
        )
        best = self.best_match(validator.iter_errors({}))
        self.assertEqual(best.validator, "minProperties")

    def test_if_the_most_relevant_error_is_anyOf_it_is_traversed(self):
        """
        If the most relevant error is an anyOf, then we traverse its context
        and select the otherwise *least* relevant error, since in this case
        that means the most specific, deep, error inside the instance.

        I.e. since only one of the schemas must match, we look for the most
        relevant one.

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
        best = self.best_match(validator.iter_errors({"foo" : {"bar" : 12}}))
        self.assertEqual(best.validator_value, "array")

    def test_if_the_most_relevant_error_is_oneOf_it_is_traversed(self):
        """
        If the most relevant error is an oneOf, then we traverse its context
        and select the otherwise *least* relevant error, since in this case
        that means the most specific, deep, error inside the instance.

        I.e. since only one of the schemas must match, we look for the most
        relevant one.

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
        best = self.best_match(validator.iter_errors({"foo" : {"bar" : 12}}))
        self.assertEqual(best.validator_value, "array")

    def test_if_the_most_relevant_error_is_allOf_it_is_traversed(self):
        """
        Now, if the error is allOf, we traverse but select the *most* relevant
        error from the context, because all schemas here must match anyways.

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
        best = self.best_match(validator.iter_errors({"foo" : {"bar" : 12}}))
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
        best = self.best_match(validator.iter_errors({"foo" : {"bar" : 12}}))
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


class TestByRelevance(unittest.TestCase):
    def test_short_paths_are_better_matches(self):
        shallow = exceptions.ValidationError("Oh no!", path=["baz"])
        deep = exceptions.ValidationError("Oh yes!", path=["foo", "bar"])
        match = max([shallow, deep], key=exceptions.by_relevance())
        self.assertIs(match, shallow)

        match = max([deep, shallow], key=exceptions.by_relevance())
        self.assertIs(match, shallow)

    def test_global_errors_are_even_better_matches(self):
        shallow = exceptions.ValidationError("Oh no!", path=[])
        deep = exceptions.ValidationError("Oh yes!", path=["foo"])

        errors = sorted([shallow, deep], key=exceptions.by_relevance())
        self.assertEqual(
            [list(error.path) for error in errors],
            [["foo"], []],
        )

        errors = sorted([deep, shallow], key=exceptions.by_relevance())
        self.assertEqual(
            [list(error.path) for error in errors],
            [["foo"], []],
        )

    def test_weak_validators_are_lower_priority(self):
        weak = exceptions.ValidationError("Oh no!", path=[], validator="a")
        normal = exceptions.ValidationError("Oh yes!", path=[], validator="b")

        best_match = exceptions.by_relevance(weak="a")

        match = max([weak, normal], key=best_match)
        self.assertIs(match, normal)

        match = max([normal, weak], key=best_match)
        self.assertIs(match, normal)

    def test_strong_validators_are_higher_priority(self):
        weak = exceptions.ValidationError("Oh no!", path=[], validator="a")
        normal = exceptions.ValidationError("Oh yes!", path=[], validator="b")
        strong = exceptions.ValidationError("Oh fine!", path=[], validator="c")

        best_match = exceptions.by_relevance(weak="a", strong="c")

        match = max([weak, normal, strong], key=best_match)
        self.assertIs(match, strong)

        match = max([strong, normal, weak], key=best_match)
        self.assertIs(match, strong)
