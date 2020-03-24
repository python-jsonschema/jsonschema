from textwrap import dedent
from unittest import TestCase
import subprocess
import sys

from jsonschema import Draft4Validator, ValidationError, cli, __version__
from jsonschema.compat import JSONDecodeError, NativeIO
from jsonschema.tests._helpers import captured_output
from jsonschema.validators import _LATEST_VERSION as LatestValidator


def fake_validator(*errors):
    errors = list(reversed(errors))

    class FakeValidator(object):
        def __init__(self, *args, **kwargs):
            pass

        def iter_errors(self, instance):
            if errors:
                return errors.pop()
            return []

        def check_schema(self, schema):
            pass

    return FakeValidator


def fake_open(all_contents):
    def open(path):
        contents = all_contents.get(path)
        if contents is None:  # pragma: no cover
            raise RuntimeError("Unknown test fixture {!r}".format(path))
        return NativeIO(contents)
    return open


class TestCLI(TestCase):

    pretty_parsing_error_tag = "===[" + JSONDecodeError.__name__ + "]==="
    pretty_validation_error_tag = "===[ValidationError]==="
    pretty_success_tag = "===[SUCCESS]==="

    def setUp(self):
        self.assertFalse(hasattr(cli, "open"))
        cli.open = fake_open(
            {
                "an invalid instance": "1",
                "a valid instance": "25",
                "a schema": """
                    {
                        "anyOf": [
                            {"minimum": 20},
                            {"type": "string"},
                            {"required": true}
                        ]
                    }
                """,
                "an invalid schema": '{"title": 1}',
                "invalid json": "{bad_key: val}",
                "more invalid json": "{1 []}",
            },
        )
        self.addCleanup(delattr, cli, "open")

    def run_cli(self, stdin=NativeIO(), exit_code=0, **arguments):
        stdout, stderr = NativeIO(), NativeIO()
        actual_exit_code = cli.run(
            arguments,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        self.assertEqual(
            actual_exit_code, exit_code, msg=dedent(
                """
                Expected an exit code of {} != {}.

                stdout: {}

                stderr: {}
                """.format(
                    exit_code,
                    actual_exit_code,
                    stdout.getvalue(),
                    stderr.getvalue(),
                ),
            ),
        )
        return stdout.getvalue(), stderr.getvalue()

    def test_invalid_instance(self):
        error = ValidationError("I am an error!", instance=1)
        stdout, stderr = self.run_cli(
            validator=fake_validator([error]),
            schema="a schema",
            instances=["an invalid instance"],
            error_format="{error.instance} - {error.message}",
            output="plain",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertEqual(stderr, "1 - I am an error!")

    def test_invalid_instance_pretty_output(self):
        error = ValidationError("I am an error!", instance=1)
        stdout, stderr = self.run_cli(
            validator=fake_validator([error]),
            schema="a schema",
            instances=["an invalid instance"],
            error_format="",
            output="pretty",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn(self.pretty_validation_error_tag, stderr)

    def test_multiple_invalid_instances(self):
        first_errors = [
            ValidationError("9", instance=1),
            ValidationError("8", instance=1),
        ]
        second_errors = [ValidationError("7", instance=2)]
        stdout, stderr = self.run_cli(
            validator=fake_validator(first_errors, second_errors),
            schema="a schema",
            instances=["an invalid instance", "a valid instance"],
            error_format="{error.instance} - {error.message}\t",
            output="plain",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertEqual(stderr, "1 - 9\t1 - 8\t2 - 7\t")

    def test_invalid_schema(self):
        stdout, stderr = self.run_cli(
            validator=LatestValidator,
            schema="an invalid schema",
            instances=None,
            error_format="{error.message}",
            output="plain",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertTrue(stderr)

    def test_instance_is_invalid_JSON(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="a schema",
            instances=["invalid json", "more invalid json"],
            error_format="{error.message}",
            output="plain",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn("Failed to parse 'invalid json'", stderr)
        self.assertIn("Failed to parse 'more invalid json'", stderr)

    def test_instance_is_invalid_JSON_on_stdin(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="a schema",
            instances=None,
            error_format="{error.message}",
            output="plain",
            stdin=NativeIO("{foo}"),
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn("Failed to parse <stdin>", stderr)

    def test_instance_is_invalid_JSON_on_stdin_pretty_output(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="a schema",
            instances=None,
            output="pretty",
            stdin=NativeIO("{foo}"),
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn("\nTraceback (most recent call last):\n", stderr)
        self.assertIn(self.pretty_parsing_error_tag, stderr)

    def test_schema_is_invalid_JSON(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="invalid json",
            instances=["a valid instance"],
            error_format="{error.message}",
            output="plain",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn("Failed to parse 'invalid json'", stderr)

    def test_schema_and_instance_are_both_invalid_JSON(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="invalid json",
            instances=["an invalid instance"],
            error_format="",
            output="plain",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn("Failed to parse 'invalid json'", stderr)

    def test_schema_and_instance_are_both_invalid_JSON_pretty_output(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="invalid json",
            instances=["an invalid instance"],
            error_format="",
            output="pretty",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn("\nTraceback (most recent call last):\n", stderr)
        self.assertIn(self.pretty_parsing_error_tag, stderr)

    def test_successful_validation(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="a schema",
            instances=["a valid instance"],
            error_format="{error.message}",
            output="plain",
        )
        self.assertFalse(stdout)
        self.assertFalse(stderr)

    def test_successful_validation_pretty_output(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="a schema",
            instances=["a valid instance"],
            error_format="",
            output="pretty",
        )
        self.assertIn(self.pretty_success_tag, stdout)
        self.assertFalse(stderr)

    def test_piping(self):
        stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="a schema",
            instances=None,
            error_format="{error.message}",
            output="plain",
            stdin=NativeIO("{}"),
        )
        self.assertFalse(stdout)
        self.assertFalse(stderr)

    def test_draft3_schema_draft4_validator(self):
        stdout, stderr = self.run_cli(
            validator=Draft4Validator,
            schema="a schema",
            instances=["an invalid instance"],
            error_format="{error.message}",
            output="plain",
            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertTrue(stderr)


class TestParser(TestCase):

    FakeValidator = fake_validator()

    def test_find_validator_by_fully_qualified_object_name(self):
        arguments = cli.parse_args(
            [
                "--validator",
                "jsonschema.tests.test_cli.TestParser.FakeValidator",
                "--instance", "mem://some/instance",
                "mem://some/schema",
            ]
        )
        self.assertIs(arguments["validator"], self.FakeValidator)

    def test_find_validator_in_jsonschema(self):
        arguments = cli.parse_args(
            [
                "--validator", "Draft4Validator",
                "--instance", "mem://some/instance",
                "mem://some/schema",
            ]
        )
        self.assertIs(arguments["validator"], Draft4Validator)

    def test_latest_validator_is_the_default(self):
        arguments = cli.parse_args(
            [
                "--instance", "mem://some/instance",
                "mem://some/schema",
            ]
        )
        self.assertIs(arguments["validator"], LatestValidator)

    def test_unknown_output(self):
        # Avoid the help message on stdout
        with captured_output() as (stdout, stderr):
            with self.assertRaises(SystemExit):
                cli.parse_args(
                    [
                        "--output", "foo",
                        "mem://some/schema",
                    ]
                )
        self.assertIn("invalid choice: 'foo'", stderr.getvalue())
        self.assertFalse(stdout.getvalue())

    def test_useless_error_format(self):
        # Avoid the help message on stdout
        with captured_output() as (stdout, stderr):
            with self.assertRaises(SystemExit):
                cli.parse_args(
                    [
                        "--output", "pretty",
                        "--error-format", "foo",
                        "mem://some/schema",
                    ]
                )
        self.assertIn(
            "--error-format can only be used with --output plain",
            stderr.getvalue(),
        )
        self.assertFalse(stdout.getvalue())


class TestCLIIntegration(TestCase):
    def test_license(self):
        output = subprocess.check_output(
            [sys.executable, "-m", "pip", "show", "jsonschema"],
            stderr=subprocess.STDOUT,
        )
        self.assertIn(b"License: MIT", output)

    def test_version(self):
        version = subprocess.check_output(
            [sys.executable, "-m", "jsonschema", "--version"],
            stderr=subprocess.STDOUT,
        )
        version = version.decode("utf-8").strip()
        self.assertEqual(version, __version__)
