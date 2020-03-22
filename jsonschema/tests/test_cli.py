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

    def test_none_validator(self):
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


class TestCLI(TestCase):
    instance_file_1 = "foo1.json"
    instance_file_2 = "foo2.json"
    schema_file = "schema.json"
    schema_error_file = "schema_error.json"
    bad_json_file_1 = "bad1.json"
    bad_json_file_2 = "bad2.json"
    pretty_parsing_error_tag = "===[" + JSONDecodeError.__name__ + "]==="
    pretty_validation_error_tag = "===[ValidationError]==="
    pretty_success_tag = "===[SUCCESS]==="

    def setUp(self):
        self.assertFalse(hasattr(cli, "open"))
        cli.open = fake_open(
            {
                self.instance_file_1: "1",
                self.instance_file_2: "25",
                self.schema_file: """
                    {
                        "anyOf": [
                            {"minimum": 20},
                            {"type": "string"},
                            {"required": true}
                        ]
                    }
                """,
                self.schema_error_file: '{"title": 1}',
                self.bad_json_file_1: "{bad_key: val}",
                self.bad_json_file_2: "{1 []}",
            },
        )
        self.addCleanup(delattr, cli, "open")

    def run_cli(self, stdin=NativeIO(), **arguments):
        stdout, stderr = NativeIO(), NativeIO()
        exit_code = cli.run(
            arguments,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        return exit_code, stdout, stderr

    def test_draft3_schema_draft4_validator(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=Draft4Validator,
            schema="schema.json",
            instances=["foo1.json"],
            error_format="{error.message}",
            output="plain",
        )
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue())
        self.assertEqual(exit_code, 1)

    def test_successful_validation(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="schema.json",
            instances=["foo2.json"],
            error_format="{error.message}",
            output="plain",
        )
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())
        self.assertEqual(exit_code, 0)

    def test_unsuccessful_validation(self):
        error = ValidationError("I am an error!", instance=1)
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator([error]),
            schema="schema.json",
            instances=["foo1.json"],
            error_format="{error.instance} - {error.message}",
            output="plain",
        )
        self.assertFalse(stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "1 - I am an error!")
        self.assertEqual(exit_code, 1)

    def test_unsuccessful_validation_multiple_instances(self):
        first_errors = [
            ValidationError("9", instance=1),
            ValidationError("8", instance=1),
        ]
        second_errors = [ValidationError("7", instance=2)]
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(first_errors, second_errors),
            schema="schema.json",
            instances=["foo1.json", "foo2.json"],
            error_format="{error.instance} - {error.message}\t",
            output="plain",
        )
        self.assertFalse(stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "1 - 9\t1 - 8\t2 - 7\t")
        self.assertEqual(exit_code, 1)

    def test_piping(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="schema.json",
            instances=None,
            error_format="{error.message}",
            output="plain",
            stdin=NativeIO("{}"),
        )
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())
        self.assertEqual(exit_code, 0)

    def test_schema_parsing_error(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="bad1.json",
            instances=["foo1.json"],
            error_format="{error.message}",
            output="plain",
        )
        self.assertFalse(stdout.getvalue())
        self.assertIn("Failed to parse bad1.json", stderr.getvalue())
        self.assertEqual(exit_code, 1)

    def test_instance_parsing_error(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="schema.json",
            instances=["bad1.json", "bad2.json"],
            error_format="{error.message}",
            output="plain",
        )
        output_err = stderr.getvalue()
        self.assertFalse(stdout.getvalue())
        self.assertIn("Failed to parse bad1.json", output_err)
        self.assertIn("Failed to parse bad2.json", output_err)
        self.assertEqual(exit_code, 1)

    def test_stdin_parsing_error(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="schema.json",
            instances=None,
            error_format="{error.message}",
            output="plain",
            stdin=NativeIO("{foo}"),
        )
        self.assertFalse(stdout.getvalue())
        self.assertIn("Failed to parse <stdin>", stderr.getvalue())
        self.assertEqual(exit_code, 1)

    def test_stdin_pretty_parsing_error(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="schema.json",
            instances=None,
            output="pretty",
            stdin=NativeIO("{foo}"),
        )
        self.assertFalse(stdout.getvalue())
        self.assertIn(
            "\nTraceback (most recent call last):\n", stderr.getvalue(),
        )
        self.assertIn(self.pretty_parsing_error_tag, stderr.getvalue())
        self.assertEqual(exit_code, 1)

    def test_parsing_error(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="bad1.json",
            instances=["foo1.json"],
            error_format="",
            output="plain",
        )
        self.assertFalse(stdout.getvalue())
        self.assertIn("Failed to parse bad1.json", stderr.getvalue())
        self.assertEqual(exit_code, 1)

    def test_pretty_parsing_error(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="bad1.json",
            instances=["foo1.json"],
            error_format="",
            output="pretty",
        )
        self.assertFalse(stdout.getvalue())
        self.assertIn(
            "\nTraceback (most recent call last):\n", stderr.getvalue(),
        )
        self.assertIn(self.pretty_parsing_error_tag, stderr.getvalue())
        self.assertEqual(exit_code, 1)

    def test_pretty_successful_validation(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator(),
            schema="schema.json",
            instances=["foo2.json"],
            error_format="",
            output="pretty",
        )
        self.assertIn(self.pretty_success_tag, stdout.getvalue())
        self.assertFalse(stderr.getvalue())
        self.assertEqual(exit_code, 0)

    def test_pretty_unsuccessful_validation(self):
        error = ValidationError("I am an error!", instance=1)
        exit_code, stdout, stderr = self.run_cli(
            validator=fake_validator([error]),
            schema="schema.json",
            instances=["foo1.json"],
            error_format="",
            output="pretty",
        )
        self.assertFalse(stdout.getvalue())
        self.assertIn(self.pretty_validation_error_tag, stderr.getvalue())
        self.assertEqual(exit_code, 1)

    def test_schema_validation(self):
        exit_code, stdout, stderr = self.run_cli(
            validator=LatestValidator,
            schema="schema_error.json",
            instances=None,
            error_format="{error.message}",
            output="plain",
        )
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue())
        self.assertEqual(exit_code, 1)

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
