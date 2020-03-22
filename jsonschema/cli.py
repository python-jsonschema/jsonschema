"""
The ``jsonschema`` command line.
"""

from __future__ import absolute_import
from textwrap import dedent
import argparse
import json
import sys
import traceback

import attr

from jsonschema import __version__
from jsonschema._reflect import namedAny
from jsonschema.compat import JSONDecodeError
from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for


@attr.s
class _PrettyOutputFormatter(object):

    _ERROR_MSG = dedent(
        """\
        ===[{type.__name__}]===({path})===

        {body}
        -----------------------------
        """,
    )
    _SUCCESS_MSG = "===[SUCCESS]===({path})===\n"

    def parsing_error(self, path, exc_info):
        exc_type, exc_value, exc_traceback = exc_info
        exc_lines = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback),
        )
        return self._ERROR_MSG.format(path=path, type=exc_type, body=exc_lines)

    def validation_error(self, instance_path, error):
        return self._ERROR_MSG.format(
            path=instance_path,
            type=error.__class__,
            body=error,
        )

    def validation_success(self, instance_path):
        return self._SUCCESS_MSG.format(path=instance_path)


@attr.s
class _PlainOutputFormatter(object):

    _error_format = attr.ib()

    def parsing_error(self, path, exc_info):
        return (
            "Failed to parse {path}. Got the following error: {exc_info[1]}\n"
        ).format(path=path, exc_info=exc_info)

    def validation_error(self, instance_path, error):
        return self._error_format.format(file_name=instance_path, error=error)

    def validation_success(self, instance_path):
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
    except (ValueError, IOError) as error:
        stderr.write(
            formatter.parsing_error(path=schema_path, exc_info=sys.exc_info()),
        )
        raise error

    try:
        validator = Validator(schema=schema_obj)
        validator.check_schema(schema_obj)
    except SchemaError as error:
        stderr.write(
            formatter.validation_error(
                instance_path=schema_path,
                error=error,
            ),
        )
        raise error

    return validator


def _validate_instance(
    instance_path,
    instance,
    validator,
    formatter,
    stdout,
    stderr,
):
    invalid = False
    for error in validator.iter_errors(instance):
        invalid = True
        stderr.write(
            formatter.validation_error(
                instance_path=instance_path,
                error=error,
            ),
        )

    if not invalid:
        stdout.write(formatter.validation_success(instance_path=instance_path))
    return invalid


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
        return 1

    if arguments["instances"]:
        load, instances = _load_json_file, arguments["instances"]
    else:
        def load(_):
            return json.load(stdin)
        instances = ["<stdin>"]

    exit_code = 0
    for each in instances:
        try:
            instance = load(each)
        except JSONDecodeError:
            stderr.write(
                formatter.parsing_error(path=each, exc_info=sys.exc_info()),
            )
            exit_code = 1
        else:
            exit_code |= _validate_instance(
                instance_path=each,
                instance=instance,
                validator=validator,
                formatter=formatter,
                stdout=stdout,
                stderr=stderr,
            )

    return exit_code
