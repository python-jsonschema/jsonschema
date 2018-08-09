"""
Test runner for the JSON Schema official test suite

Tests comprehensive correctness of each draft's validator.

See https://github.com/json-schema/JSON-Schema-Test-Suite for details.

"""

from decimal import Decimal
import sys
import unittest

from jsonschema import (
    SchemaError, ValidationError, Draft3Validator,
    Draft4Validator, Draft6Validator, FormatChecker, draft3_format_checker,
    draft4_format_checker, draft6_format_checker, validate,
)
from jsonschema.compat import PY3
from jsonschema.tests._suite import Suite
from jsonschema.validators import create


SUITE = Suite()
DRAFT3 = SUITE.collection(name="draft3")
DRAFT4 = SUITE.collection(name="draft4")
DRAFT6 = SUITE.collection(name="draft6")


def maybe_skip(skip, test_fn, test):
    reason = skip(test)
    return unittest.skipIf(reason is not None, reason)(test_fn)


def load_json_cases(tests, skip=lambda test: None):
    def add_test_methods(test_class):
        for test in tests:
            test = test.with_validate_kwargs(
                **getattr(test_class, "validator_kwargs", {})
            )
            method = test.to_unittest_method()
            assert not hasattr(test_class, method.__name__), test
            setattr(
                test_class,
                method.__name__,
                maybe_skip(skip, method, test),
            )

        return test_class
    return add_test_methods


def skip_tests_containing_descriptions(**kwargs):
    def skipper(test):
        descriptions_and_reasons = kwargs.get(test.subject, {})
        return next(
            (
                reason
                for description, reason in descriptions_and_reasons.items()
                if description in test.description
            ),
            None,
        )
    return skipper


class TypesMixin(object):
    @unittest.skipIf(PY3, "In Python 3 json.load always produces unicode")
    def test_string_a_bytestring_is_a_string(self):
        self.validator_class({"type": "string"}).validate(b"foo")


class DecimalMixin(object):
    def test_it_can_validate_with_decimals(self):
        schema = {"type": "number"}
        validator = self.validator_class(
            schema, types={"number": (int, float, Decimal)}
        )

        for valid in [1, 1.1, Decimal(1) / Decimal(8)]:
            validator.validate(valid)

        for invalid in ["foo", {}, [], True, None]:
            with self.assertRaises(ValidationError):
                validator.validate(invalid)


def missing_format(checker):
    def missing_format(test):
        format = test.schema.get("format")
        if format not in checker.checkers:
            return "Format checker {0!r} not found.".format(format)
    return missing_format


class FormatMixin(object):
    def test_it_returns_true_for_formats_it_does_not_know_about(self):
        validator = self.validator_class(
            {"format": "carrot"}, format_checker=FormatChecker(),
        )
        validator.validate("bugs")

    def test_it_does_not_validate_formats_by_default(self):
        validator = self.validator_class({})
        self.assertIsNone(validator.format_checker)

    def test_it_validates_formats_if_a_checker_is_provided(self):
        checker = FormatChecker()
        bad = ValueError("Bad!")

        @checker.checks("foo", raises=ValueError)
        def check(value):
            if value == "good":
                return True
            elif value == "bad":
                raise bad
            else:  # pragma: no cover
                self.fail("What is {}? [Baby Don't Hurt Me]".format(value))

        validator = self.validator_class(
            {"format": "foo"}, format_checker=checker,
        )

        validator.validate("good")
        with self.assertRaises(ValidationError) as cm:
            validator.validate("bad")

        # Make sure original cause is attached
        self.assertIs(cm.exception.cause, bad)


is_narrow_build = sys.maxunicode == 2 ** 16 - 1
if is_narrow_build:  # pragma: no cover
    narrow_unicode_build = skip_tests_containing_descriptions(
        {
            "supplementary Unicode":
                "Not running surrogate Unicode case, this Python is narrow.",
        }
    )
else:
    def narrow_unicode_build(test):  # pragma: no cover
        return


@load_json_cases(tests=DRAFT3.tests(), skip=narrow_unicode_build)
@load_json_cases(
    tests=DRAFT3.optional_tests_of(name="format"),
    skip=lambda test: (
        missing_format(draft3_format_checker)(test) or
        skip_tests_containing_descriptions(
            format={
                "case-insensitive T and Z":  "Upstream bug in strict_rfc3339",
            },
        )(test)
    ),
)
@load_json_cases(tests=DRAFT3.optional_tests_of(name="bignum"))
@load_json_cases(tests=DRAFT3.optional_tests_of(name="zeroTerminatedFloats"))
class TestDraft3(unittest.TestCase, TypesMixin, DecimalMixin, FormatMixin):
    validator_class = Draft3Validator
    validator_kwargs = {"format_checker": draft3_format_checker}

    def test_any_type_is_valid_for_type_any(self):
        validator = self.validator_class({"type": "any"})
        validator.validate(object())

    # TODO: we're in need of more meta schema tests
    def test_invalid_properties(self):
        with self.assertRaises(SchemaError):
            validate({}, {"properties": {"test": True}},
                     cls=self.validator_class)

    def test_minItems_invalid_string(self):
        with self.assertRaises(SchemaError):
            # needs to be an integer
            validate([1], {"minItems": "1"}, cls=self.validator_class)


@load_json_cases(
    tests=DRAFT4.tests(),
    skip=lambda test: (
        narrow_unicode_build(test) or skip_tests_containing_descriptions(
            ref={
                "valid tree":  "An actual bug, this needs fixing.",
            },
            refRemote={
                "number is valid": "An actual bug, this needs fixing.",
                "string is invalid": "An actual bug, this needs fixing.",
            },
        )(test)
    ),
)
@load_json_cases(
    tests=DRAFT4.optional_tests_of(name="format"),
    skip=lambda test: (
        missing_format(draft4_format_checker)(test) or
        skip_tests_containing_descriptions(
            format={
                "case-insensitive T and Z":  "Upstream bug in strict_rfc3339",
            },
        )(test)
    ),
)
@load_json_cases(tests=DRAFT4.optional_tests_of(name="bignum"))
@load_json_cases(tests=DRAFT4.optional_tests_of(name="zeroTerminatedFloats"))
class TestDraft4(unittest.TestCase, TypesMixin, DecimalMixin, FormatMixin):
    validator_class = Draft4Validator
    validator_kwargs = {"format_checker": draft4_format_checker}

    # TODO: we're in need of more meta schema tests
    def test_invalid_properties(self):
        with self.assertRaises(SchemaError):
            validate({}, {"properties": {"test": True}},
                     cls=self.validator_class)

    def test_minItems_invalid_string(self):
        with self.assertRaises(SchemaError):
            # needs to be an integer
            validate([1], {"minItems": "1"}, cls=self.validator_class)


@load_json_cases(
    tests=DRAFT6.tests(),
    skip=lambda test: (
        narrow_unicode_build(test) or skip_tests_containing_descriptions(
            ref={
                "valid tree":  "An actual bug, this needs fixing.",
            },
            refRemote={
                "number is valid": "An actual bug, this needs fixing.",
                "string is invalid": "An actual bug, this needs fixing.",
            },
        )(test)
    ),
)
@load_json_cases(
    tests=DRAFT6.optional_tests_of(name="format"),
    skip=lambda test: (
        missing_format(draft6_format_checker)(test) or
        skip_tests_containing_descriptions(
            format={
                "case-insensitive T and Z":  "Upstream bug in strict_rfc3339",
            },
        )(test)
    ),
)
@load_json_cases(tests=DRAFT6.optional_tests_of(name="bignum"))
@load_json_cases(tests=DRAFT6.optional_tests_of(name="zeroTerminatedFloats"))
class TestDraft6(unittest.TestCase, TypesMixin, DecimalMixin, FormatMixin):
    validator_class = Draft6Validator
    validator_kwargs = {"format_checker": draft6_format_checker}


@load_json_cases(tests=DRAFT3.tests_of(name="type"))
class TestDraft3LegacyTypeCheck(unittest.TestCase):
    Validator = create(meta_schema=Draft3Validator.META_SCHEMA,
                       validators=Draft3Validator.VALIDATORS,
                       type_checker=None)
    validator_class = Validator


@load_json_cases(tests=DRAFT4.tests_of(name="type"))
class TestDraft4LegacyTypeCheck(unittest.TestCase):
    Validator = create(meta_schema=Draft4Validator.META_SCHEMA,
                       validators=Draft4Validator.VALIDATORS,
                       type_checker=None)
    validator_class = Validator
