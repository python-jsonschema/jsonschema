"""
Test runner for the JSON Schema official test suite

Tests comprehensive correctness of each draft's validator.

See https://github.com/json-schema/JSON-Schema-Test-Suite for details.

"""

import sys
import unittest

from jsonschema import (
    SchemaError,
    Draft3Validator,
    Draft4Validator,
    Draft6Validator,
    draft3_format_checker,
    draft4_format_checker,
    draft6_format_checker,
    validate,
)
from jsonschema.tests._suite import Suite
from jsonschema.validators import _DEPRECATED_DEFAULT_TYPES, create


SUITE = Suite()
DRAFT3 = SUITE.collection(name="draft3")
DRAFT4 = SUITE.collection(name="draft4")
DRAFT6 = SUITE.collection(name="draft6")


def maybe_skip(reason):
    return unittest.skipIf(reason is not None, reason)


def load_json_cases(name, *suites, **kwargs):
    skip = kwargs.pop("skip", lambda test: None)
    methods = {
        test.method_name: maybe_skip(skip(test))(
            test.to_unittest_method(**kwargs),
        )
        for suite in suites
        for test in suite
    }
    return type(name, (unittest.TestCase,), methods)


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


def missing_format(checker):
    def missing_format(test):
        schema = test.schema
        if schema is True or schema is False or "format" not in schema:
            return

        if schema["format"] not in checker.checkers:
            return "Format checker {0!r} not found.".format(schema["format"])
    return missing_format


is_narrow_build = sys.maxunicode == 2 ** 16 - 1
if is_narrow_build:  # pragma: no cover
    narrow_unicode_build = skip_tests_containing_descriptions(
        maxLength={
            "supplementary Unicode":
                "Not running surrogate Unicode case, this Python is narrow.",
        },
        minLength={
            "supplementary Unicode":
                "Not running surrogate Unicode case, this Python is narrow.",
        },
    )
else:
    def narrow_unicode_build(test):  # pragma: no cover
        return


TestDraft3 = load_json_cases(
    "TestDraft3",
    DRAFT3.tests(),
    DRAFT3.optional_tests_of(name="format"),
    DRAFT3.optional_tests_of(name="bignum"),
    DRAFT3.optional_tests_of(name="zeroTerminatedFloats"),
    Validator=Draft3Validator,
    format_checker=draft3_format_checker,
    skip=lambda test: (
        narrow_unicode_build(test) or
        missing_format(draft3_format_checker)(test) or
        skip_tests_containing_descriptions(
            format={
                "case-insensitive T and Z":  "Upstream bug in strict_rfc3339",
            },
        )(test)
    ),
)


TestDraft4 = load_json_cases(
    "TestDraft4",
    DRAFT4.tests(),
    DRAFT4.optional_tests_of(name="format"),
    DRAFT4.optional_tests_of(name="bignum"),
    DRAFT4.optional_tests_of(name="zeroTerminatedFloats"),
    Validator=Draft4Validator,
    format_checker=draft4_format_checker,
    skip=lambda test: (
        narrow_unicode_build(test) or
        missing_format(draft4_format_checker)(test) or
        skip_tests_containing_descriptions(
            format={
                "case-insensitive T and Z":  "Upstream bug in strict_rfc3339",
            },
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


TestDraft6 = load_json_cases(
    "TestDraft6",
    DRAFT6.tests(),
    DRAFT6.optional_tests_of(name="format"),
    DRAFT6.optional_tests_of(name="bignum"),
    DRAFT6.optional_tests_of(name="zeroTerminatedFloats"),
    Validator=Draft6Validator,
    format_checker=draft6_format_checker,
    skip=lambda test: (
        narrow_unicode_build(test) or
        missing_format(draft6_format_checker)(test) or
        skip_tests_containing_descriptions(
            format={
                "case-insensitive T and Z":  "Upstream bug in strict_rfc3339",
            },
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


TestDraft3LegacyTypeCheck = load_json_cases(
    "TestDraft3LegacyTypeCheck",
    DRAFT3.tests_of(name="type"),
    Validator=create(
        meta_schema=Draft3Validator.META_SCHEMA,
        validators=Draft3Validator.VALIDATORS,
        default_types=_DEPRECATED_DEFAULT_TYPES,
    ),
)


TestDraft4LegacyTypeCheck = load_json_cases(
    "TestDraft4LegacyTypeCheck",
    DRAFT4.tests_of(name="type"),
    Validator=create(
        meta_schema=Draft4Validator.META_SCHEMA,
        validators=Draft4Validator.VALIDATORS,
        default_types=_DEPRECATED_DEFAULT_TYPES,
    ),
)
