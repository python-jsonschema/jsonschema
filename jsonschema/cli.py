"""
The ``jsonschema`` command line.
"""

from __future__ import absolute_import
from textwrap import dedent
import argparse
import json
import sys

import attr

from jsonschema import __version__
from jsonschema._reflect import namedAny
from jsonschema.exceptions import SchemaError, ValidationError
from jsonschema.validators import validator_for


@attr.s
class _PrettyOutputFormatter(object):

    _ERROR_MSG = dedent(
        """\
        ===[{error.__class__.__name__}]===({file_name})===
        {error}
        -----------------------------
        """,
    )
    _SUCCESS_MSG = "===[SUCCESS]===({file_name})===\n"

    def parsing_error(self, file_name, exception):
        return self._ERROR_MSG.format(file_name=file_name, error=exception)

    def validation_error(self, file_name, error_obj):
        return self._ERROR_MSG.format(file_name=file_name, error=error_obj)

    def validation_success(self, file_name):
        return self._SUCCESS_MSG.format(file_name=file_name)


@attr.s
class _PlainOutputFormatter(object):

    _error_format = attr.ib()

    def parsing_error(self, file_name, exception):
        return (
            "Failed to parse {file_name}. "
            "Got the following error: {exception}\n"
        ).format(file_name=file_name, exception=exception)

    def validation_error(self, file_name, error_obj):
        return self._error_format.format(file_name=file_name, error=error_obj)

    def validation_success(self, file_name):
        return ""


def _namedAnyWithDefault(name):
    if "." not in name:
        name = "jsonschema." + name
    return namedAny(name)


parser = argparse.ArgumentParser(
    description="JSON Schema Validation CLI",
)
parser.add_argument(
    "-i", "--instance",
    action="append",
    dest="instances",
    type=str,
    help=(
        "A path to a JSON instance (i.e. filename.json) "
        "to validate (may be specified multiple times). "
        "If this option is not used, an instance can be given through stdin. "
        "If neither -i nor stdin is given, only the schema is checked."
    ),
)
parser.add_argument(
    "-F", "--error-format",
    help=(
        "The format to use for each error output message, specified in "
        "a form suitable for passing to str.format, which will be called "
        "with 'error' for each error. This is only used when --output=plain "
        "(default)."
    ),
)
parser.add_argument(
    "-o", "--output",
    choices=["plain", "pretty"],
    default="plain",
    help=(
        "Select the output format. "
        "'plain': one line per error, minimum text. "
        "'pretty': human-readable output with multiline details. "
    ),
)
parser.add_argument(
    "-V", "--validator",
    type=_namedAnyWithDefault,
    help=(
        "the fully qualified object name of a validator to use, or, for "
        "validators that are registered with jsonschema, simply the name "
        "of the class."
    ),
)
parser.add_argument(
    "--version",
    action="version",
    version=__version__,
)
parser.add_argument(
    "schema",
    help="Path to the JSON Schema to validate with (i.e. schema.json)",
    type=str,
)


def _load_json_file(path):
    with open(path) as file:
        return json.load(file)


def parse_args(args):
    arguments = vars(parser.parse_args(args=args or ["--help"]))
    if arguments["validator"] is None:
        arguments["validator"] = validator_for(arguments["schema"])
    if arguments["instances"] is None:
        arguments["instances"] = []
    if arguments["output"] != "plain" and arguments["error_format"]:
        raise parser.error(
            "--error-format can only be used with --output plain"
        )
    if arguments["output"] == "plain" and arguments["error_format"] is None:
        arguments["error_format"] = "{error.instance}: {error.message}\n"
    return arguments


def _make_validator(schema_path, Validator, formatter, stderr):
    try:
        schema_obj = _load_json_file(schema_path)
    except (ValueError, IOError) as exc:
        stderr.write(formatter.parsing_error(schema_path, exc))
        raise exc

    try:
        validator = Validator(schema=schema_obj)
        validator.check_schema(schema_obj)
    except SchemaError as exc:
        stderr.write(formatter.validation_error(schema_path, exc))
        raise exc

    return validator


def _load_stdin(stdin, formatter, stderr):
    try:
        instance_obj = json.load(stdin)
    except ValueError as exc:
        stderr.write(formatter.parsing_error("stdin", exc))
        raise exc
    return instance_obj


def _load_instance_file(instance_path, formatter, stderr):
    try:
        instance_obj = _load_json_file(instance_path)
    except (ValueError, IOError) as exc:
        stderr.write(formatter.parsing_error(instance_path, exc))
        raise exc
    return instance_obj


def _validate_instance(
    instance_path,
    instance,
    validator,
    formatter,
    stdout,
    stderr,
):
    instance_errored = False
    for error in validator.iter_errors(instance):
        instance_errored = True
        stderr.write(formatter.validation_error(instance_path, error))

    if not instance_errored:
        stdout.write(formatter.validation_success(instance_path))
    else:
        raise ValidationError("Some errors appeared in this instance.")


def main(args=sys.argv[1:]):
    sys.exit(run(arguments=parse_args(args=args)))


def run(arguments, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin):
    if arguments["output"] == "plain":
        formatter = _PlainOutputFormatter(arguments["error_format"])
    elif arguments["output"] == "pretty":
        formatter = _PrettyOutputFormatter()

    try:
        validator = _make_validator(
            schema_path=arguments["schema"],
            Validator=arguments["validator"],
            formatter=formatter,
            stderr=stderr,
        )
    except (IOError, ValueError, SchemaError):
        return True

    errored = False
    if arguments["instances"]:
        for instance_path in arguments["instances"]:
            try:
                _validate_instance(
                    instance_path=instance_path,
                    instance=_load_instance_file(
                        instance_path=instance_path,
                        formatter=formatter,
                        stderr=stderr,
                    ),
                    validator=validator,
                    formatter=formatter,
                    stdout=stdout,
                    stderr=stderr,
                )
            except (ValueError, IOError, ValidationError):
                errored = True
    elif (
        stdin is sys.stdin and not sys.stdin.isatty()
        or stdin is not sys.stdin and stdin is not None
    ):
        try:
            _validate_instance(
                instance_path="stdin",
                instance=_load_stdin(
                    stdin=stdin,
                    stderr=stderr,
                    formatter=formatter,
                ),
                validator=validator,
                formatter=formatter,
                stdout=stdout,
                stderr=stderr,
            )
        except (ValueError, ValidationError):
            errored = True

    return errored
