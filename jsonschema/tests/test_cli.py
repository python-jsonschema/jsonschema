from textwrap import dedent
from unittest import TestCase
import errno
import json
import os
import subprocess
import sys

from jsonschema import Draft4Validator, cli, __version__
from jsonschema.compat import JSONDecodeError, NativeIO
from jsonschema.exceptions import SchemaError, ValidationError
from jsonschema.tests._helpers import captured_output
from jsonschema.validators import _LATEST_VERSION, validate


def fake_validator(*errors):
    errors = list(reversed(errors))

    class FakeValidator(object):
        def __init__(self, *args, **kwargs):
            pass

        def iter_errors(self, instance):
            if errors:
                return errors.pop()
            return []

        @classmethod
        def check_schema(self, schema):
            pass

    return FakeValidator


def fake_open(all_contents):
    def open(path):
        contents = all_contents.get(path)
        if contents is None:
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), path)
        return NativeIO(contents)
    return open


def _message_for(non_json):
    try:
        json.loads(non_json)
    except JSONDecodeError as error:
        return str(error)
    else:  # pragma: no cover
        raise RuntimeError("Tried and failed to capture a JSON dump error.")


class TestCLI(TestCase):
    def run_cli(
            self, argv, files={}, stdin=NativeIO(), exit_code=0, **override
    ):
        arguments = cli.parse_args(argv)
        arguments.update(override)

        self.assertFalse(hasattr(cli, "open"))
        cli.open = fake_open(files)
        try:
            stdout, stderr = NativeIO(), NativeIO()
            actual_exit_code = cli.run(
                arguments,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
            )
        finally:
            del cli.open

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

    def assertOutputs(self, stdout="", stderr="", **kwargs):
        self.assertEqual(
            self.run_cli(**kwargs),
            (dedent(stdout), dedent(stderr)),
        )

    def test_invalid_instance(self):
        error = ValidationError("I am an error!", instance=12)
        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_instance=json.dumps(error.instance),
            ),
            validator=fake_validator([error]),

            argv=["-i", "some_instance", "some_schema"],

            exit_code=1,
            stderr="12: I am an error!\n",
        )

    def test_invalid_instance_pretty_output(self):
        error = ValidationError("I am an error!", instance=12)
        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_instance=json.dumps(error.instance),
            ),
            validator=fake_validator([error]),

            argv=["-i", "some_instance", "--output", "pretty", "some_schema"],

            exit_code=1,
            stderr="""\
                ===[ValidationError]===(some_instance)===

                I am an error!
                -----------------------------
            """,
        ),

    def test_invalid_instance_explicit_plain_output(self):
        error = ValidationError("I am an error!", instance=12)
        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_instance=json.dumps(error.instance),
            ),
            validator=fake_validator([error]),

            argv=["--output", "plain", "-i", "some_instance", "some_schema"],

            exit_code=1,
            stderr="12: I am an error!\n",
        )

    def test_invalid_instance_multiple_errors(self):
        instance = 12
        first = ValidationError("First error", instance=instance)
        second = ValidationError("Second error", instance=instance)

        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_instance=json.dumps(instance),
            ),
            validator=fake_validator([first, second]),

            argv=["-i", "some_instance", "some_schema"],

            exit_code=1,
            stderr="""\
                12: First error
                12: Second error
            """,
        )

    def test_invalid_instance_multiple_errors_pretty_output(self):
        instance = 12
        first = ValidationError("First error", instance=instance)
        second = ValidationError("Second error", instance=instance)

        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_instance=json.dumps(instance),
            ),
            validator=fake_validator([first, second]),

            argv=["-i", "some_instance", "--output", "pretty", "some_schema"],

            exit_code=1,
            stderr="""\
                ===[ValidationError]===(some_instance)===

                First error
                -----------------------------
                ===[ValidationError]===(some_instance)===

                Second error
                -----------------------------
            """,
        )

    def test_multiple_invalid_instances(self):
        first_instance = 12
        first_errors = [
            ValidationError("An error", instance=first_instance),
            ValidationError("Another error", instance=first_instance),
        ]
        second_instance = "foo"
        second_errors = [ValidationError("BOOM", instance=second_instance)]

        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_first_instance=json.dumps(first_instance),
                some_second_instance=json.dumps(second_instance),
            ),
            validator=fake_validator(first_errors, second_errors),

            argv=[
                "-i", "some_first_instance",
                "-i", "some_second_instance",
                "some_schema",
            ],

            exit_code=1,
            stderr="""\
                12: An error
                12: Another error
                foo: BOOM
            """,
        )

    def test_multiple_invalid_instances_pretty_output(self):
        first_instance = 12
        first_errors = [
            ValidationError("An error", instance=first_instance),
            ValidationError("Another error", instance=first_instance),
        ]
        second_instance = "foo"
        second_errors = [ValidationError("BOOM", instance=second_instance)]

        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_first_instance=json.dumps(first_instance),
                some_second_instance=json.dumps(second_instance),
            ),
            validator=fake_validator(first_errors, second_errors),

            argv=[
                "--output", "pretty",
                "-i", "some_first_instance",
                "-i", "some_second_instance",
                "some_schema",
            ],

            exit_code=1,
            stderr="""\
                ===[ValidationError]===(some_first_instance)===

                An error
                -----------------------------
                ===[ValidationError]===(some_first_instance)===

                Another error
                -----------------------------
                ===[ValidationError]===(some_second_instance)===

                BOOM
                -----------------------------
            """,
        )

    def test_custom_error_format(self):
        first_instance = 12
        first_errors = [
            ValidationError("An error", instance=first_instance),
            ValidationError("Another error", instance=first_instance),
        ]
        second_instance = "foo"
        second_errors = [ValidationError("BOOM", instance=second_instance)]

        self.assertOutputs(
            files=dict(
                some_schema='{"does not": "matter since it is stubbed"}',
                some_first_instance=json.dumps(first_instance),
                some_second_instance=json.dumps(second_instance),
            ),
            validator=fake_validator(first_errors, second_errors),

            argv=[
                "--error-format", ":{error.message}._-_.{error.instance}:",
                "-i", "some_first_instance",
                "-i", "some_second_instance",
                "some_schema",
            ],

            exit_code=1,
            stderr=":An error._-_.12::Another error._-_.12::BOOM._-_.foo:",
        )

    def test_invalid_schema(self):
        self.assertOutputs(
            files=dict(some_schema='{"type": 12}'),
            argv=["some_schema"],

            exit_code=1,
            stderr="""\
                12: 12 is not valid under any of the given schemas
            """,
        )

    def test_invalid_schema_pretty_output(self):
        schema = {"type": 12}

        with self.assertRaises(SchemaError) as e:
            validate(schema=schema, instance="")
        error = str(e.exception)

        self.assertOutputs(
            files=dict(some_schema=json.dumps(schema)),
            argv=["--output", "pretty", "some_schema"],

            exit_code=1,
            stderr=(
                "===[SchemaError]===(some_schema)===\n\n"
                + str(error)
                + "\n-----------------------------\n"
            ),
        )

    def test_invalid_schema_multiple_errors(self):
        self.assertOutputs(
            files=dict(some_schema='{"type": 12, "items": 57}'),
            argv=["some_schema"],

            exit_code=1,
            stderr="""\
                57: 57 is not valid under any of the given schemas
            """,
        )

    def test_invalid_schema_multiple_errors_pretty_output(self):
        schema = {"type": 12, "items": 57}

        with self.assertRaises(SchemaError) as e:
            validate(schema=schema, instance="")
        error = str(e.exception)

        self.assertOutputs(
            files=dict(some_schema=json.dumps(schema)),
            argv=["--output", "pretty", "some_schema"],

            exit_code=1,
            stderr=(
                "===[SchemaError]===(some_schema)===\n\n"
                + str(error)
                + "\n-----------------------------\n"
            ),
        )

    def test_invalid_schema_with_invalid_instance(self):
        """
        "Validating" an instance that's invalid under an invalid schema
        just shows the schema error.
        """
        self.assertOutputs(
            files=dict(
                some_schema='{"type": 12, "minimum": 30}',
                some_instance="13",
            ),
            argv=["-i", "some_instance", "some_schema"],

            exit_code=1,
            stderr="""\
                12: 12 is not valid under any of the given schemas
            """,
        )

    def test_invalid_schema_with_invalid_instance_pretty_output(self):
        instance, schema = 13, {"type": 12, "minimum": 30}

        with self.assertRaises(SchemaError) as e:
            validate(schema=schema, instance=instance)
        error = str(e.exception)

        self.assertOutputs(
            files=dict(
                some_schema=json.dumps(schema),
                some_instance=json.dumps(instance),
            ),
            argv=["--output", "pretty", "-i", "some_instance", "some_schema"],

            exit_code=1,
            stderr=(
                "===[SchemaError]===(some_schema)===\n\n"
                + str(error)
                + "\n-----------------------------\n"
            ),
        )

    def test_custom_error_format_applies_to_schema_errors(self):
        instance, schema = 13, {"type": 12, "minimum": 30}

        with self.assertRaises(SchemaError):
            validate(schema=schema, instance=instance)

        self.assertOutputs(
            files=dict(some_schema=json.dumps(schema)),

            argv=[
                "--error-format", ":{error.message}._-_.{error.instance}:",
                "some_schema",
            ],

            exit_code=1,
            stderr=":12 is not valid under any of the given schemas._-_.12:",
        )

    def test_instance_is_invalid_JSON(self):
        instance = "not valid JSON!"

        self.assertOutputs(
            files=dict(some_schema="{}", some_instance=instance),
            argv=["-i", "some_instance", "some_schema"],

            exit_code=1,
            stderr="""\
                Failed to parse 'some_instance'. Got the following error: {}
            """.format(_message_for(instance)),
        )

    def test_instance_is_invalid_JSON_pretty_output(self):
        stdout, stderr = self.run_cli(
            files=dict(
                some_schema="{}",
                some_instance="not valid JSON!",
            ),

            argv=["--output", "pretty", "-i", "some_instance", "some_schema"],

            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn(
            "(some_instance)===\n\nTraceback (most recent call last):\n",
            stderr,
        )
        self.assertNotIn("some_schema", stderr)

    def test_instance_is_invalid_JSON_on_stdin(self):
        instance = "not valid JSON!"

        self.assertOutputs(
            files=dict(some_schema="{}"),
            stdin=NativeIO(instance),

            argv=["some_schema"],

            exit_code=1,
            stderr="""\
                Failed to parse <stdin>. Got the following error: {}
            """.format(_message_for(instance)),
        )

    def test_instance_is_invalid_JSON_on_stdin_pretty_output(self):
        stdout, stderr = self.run_cli(
            files=dict(some_schema="{}"),
            stdin=NativeIO("not valid JSON!"),

            argv=["--output", "pretty", "some_schema"],

            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn(
            "(<stdin>)===\n\nTraceback (most recent call last):\n",
            stderr,
        )
        self.assertNotIn("some_schema", stderr)

    def test_schema_is_invalid_JSON(self):
        schema = "not valid JSON!"

        self.assertOutputs(
            files=dict(some_schema=schema),

            argv=["some_schema"],

            exit_code=1,
            stderr="""\
                Failed to parse 'some_schema'. Got the following error: {}
            """.format(_message_for(schema)),
        )

    def test_schema_is_invalid_JSON_pretty_output(self):
        stdout, stderr = self.run_cli(
            files=dict(some_schema="not valid JSON!"),

            argv=["--output", "pretty", "some_schema"],

            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn(
            "(some_schema)===\n\nTraceback (most recent call last):\n",
            stderr,
        )

    def test_schema_and_instance_are_both_invalid_JSON(self):
        """
        Only the schema error is reported, as we abort immediately.
        """
        schema, instance = "not valid JSON!", "also not valid JSON!"
        self.assertOutputs(
            files=dict(some_schema=schema, some_instance=instance),

            argv=["some_schema"],

            exit_code=1,
            stderr="""\
                Failed to parse 'some_schema'. Got the following error: {}
            """.format(_message_for(schema)),
        )

    def test_schema_and_instance_are_both_invalid_JSON_pretty_output(self):
        """
        Only the schema error is reported, as we abort immediately.
        """
        stdout, stderr = self.run_cli(
            files=dict(
                some_schema="not valid JSON!",
                some_instance="also not valid JSON!",
            ),

            argv=["--output", "pretty", "-i", "some_instance", "some_schema"],

            exit_code=1,
        )
        self.assertFalse(stdout)
        self.assertIn(
            "(some_schema)===\n\nTraceback (most recent call last):\n",
            stderr,
        )
        self.assertNotIn("some_instance", stderr)

    def test_instance_does_not_exist(self):
        self.assertOutputs(
            files=dict(some_schema="{}"),
            argv=["-i", "nonexisting_instance", "some_schema"],

            exit_code=1,
            stderr="""\
                'nonexisting_instance' does not exist.
            """,
        )

    def test_instance_does_not_exist_pretty_output(self):
        self.assertOutputs(
            files=dict(some_schema="{}"),
            argv=[
                "--output", "pretty",
                "-i", "nonexisting_instance",
                "some_schema",
            ],

            exit_code=1,
            stderr="""\
                ===[FileNotFoundError]===(nonexisting_instance)===

                'nonexisting_instance' does not exist.
                -----------------------------
            """,
        )

    def test_schema_does_not_exist(self):
        self.assertOutputs(
            argv=["nonexisting_schema"],

            exit_code=1,
            stderr="'nonexisting_schema' does not exist.\n",
        )

    def test_schema_does_not_exist_pretty_output(self):
        self.assertOutputs(
            argv=["--output", "pretty", "nonexisting_schema"],

            exit_code=1,
            stderr="""\
                ===[FileNotFoundError]===(nonexisting_schema)===

                'nonexisting_schema' does not exist.
                -----------------------------
            """,
        )

    def test_neither_instance_nor_schema_exist(self):
        self.assertOutputs(
            argv=["-i", "nonexisting_instance", "nonexisting_schema"],

            exit_code=1,
            stderr="'nonexisting_schema' does not exist.\n",
        )

    def test_neither_instance_nor_schema_exist_pretty_output(self):
        self.assertOutputs(
            argv=[
                "--output", "pretty",
                "-i", "nonexisting_instance",
                "nonexisting_schema",
            ],

            exit_code=1,
            stderr="""\
                ===[FileNotFoundError]===(nonexisting_schema)===

                'nonexisting_schema' does not exist.
                -----------------------------
            """,
        )

    def test_successful_validation(self):
        self.assertOutputs(
            files=dict(some_schema="{}", some_instance="{}"),
            argv=["-i", "some_instance", "some_schema"],
            stdout="",
            stderr="",
        )

    def test_successful_validation_pretty_output(self):
        self.assertOutputs(
            files=dict(some_schema="{}", some_instance="{}"),
            argv=["--output", "pretty", "-i", "some_instance", "some_schema"],
            stdout="===[SUCCESS]===(some_instance)===\n",
            stderr="",
        )

    def test_successful_validation_of_stdin(self):
        self.assertOutputs(
            files=dict(some_schema="{}"),
            stdin=NativeIO("{}"),
            argv=["some_schema"],
            stdout="",
            stderr="",
        )

    def test_successful_validation_of_stdin_pretty_output(self):
        self.assertOutputs(
            files=dict(some_schema="{}"),
            stdin=NativeIO("{}"),
            argv=["--output", "pretty", "some_schema"],
            stdout="===[SUCCESS]===(<stdin>)===\n",
            stderr="",
        )

    def test_successful_validation_of_just_the_schema(self):
        self.assertOutputs(
            files=dict(some_schema="{}", some_instance="{}"),
            argv=["-i", "some_instance", "some_schema"],
            stdout="",
            stderr="",
        )

    def test_successful_validation__of_just_the_schema_pretty_output(self):
        self.assertOutputs(
            files=dict(some_schema="{}", some_instance="{}"),
            argv=["--output", "pretty", "-i", "some_instance", "some_schema"],
            stdout="===[SUCCESS]===(some_instance)===\n",
            stderr="",
        )

    def test_real_validator(self):
        self.assertOutputs(
            files=dict(some_schema='{"minimum": 30}', some_instance="37"),
            argv=["-i", "some_instance", "some_schema"],
            stdout="",
            stderr="",
        )


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
        self.assertIs(arguments["validator"], _LATEST_VERSION)

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
