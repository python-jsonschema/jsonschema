"""
The ``jsonschema`` command line.
"""

from __future__ import absolute_import
from abc import ABCMeta
import argparse
import json
import sys

from jsonschema import __version__
from jsonschema._reflect import namedAny
from jsonschema.validators import validator_for
from jsonschema.exceptions import SchemaError, ValidationError


class _CliOutputWriter():

    __metaclass__ = ABCMeta

    PARSING_ERROR_MSG = (
        "Failed to parse {file_name}. "
        "Got the following error: {exception}\n"
    )

    def __init__(
        self,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        self.stdout = stdout
        self.stderr = stderr

    def write_parsing_error(self, file_name, exception):
        # If not overriden, default behaviour is to write nothing.
        pass

    def write_validation_error(self, object_name, error_obj):
        # If not overriden, default behaviour is to write nothing.
        pass

    def write_validation_success(self, object_name):
        # If not overriden, default behaviour is to write nothing.
        pass


class _PrettyOutputWriter(_CliOutputWriter):

    PRETTY_ERROR_MSG = "===[ERROR]===({object_name})===\n{error}\n"
    PRETTY_SUCCESS_MSG = "===[SUCCESS]===({object_name})===\n"

    def write_parsing_error(self, file_name, exception):
        self.stderr.write(
            self.PRETTY_ERROR_MSG.format(
                object_name=file_name,
                error=self.PARSING_ERROR_MSG.format(
                    file_name=file_name,
                    exception=exception,
                ),
            )
        )

    def write_validation_error(self, object_name, error_obj):
        self.stderr.write(
            self.PRETTY_ERROR_MSG.format(
                object_name=object_name,
                error=error_obj,
            )
        )

    def write_validation_success(self, object_name):
        self.stdout.write(
            self.PRETTY_SUCCESS_MSG.format(
                object_name=object_name
            )
        )


class _PlainOutputWriter(_CliOutputWriter):

    def __init__(
        self,
        plain_format,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        self.plain_format = plain_format
        super(_PlainOutputWriter, self).__init__(stdout, stderr)

    def write_parsing_error(self, file_name, exception):
        self.stderr.write(
            self.PARSING_ERROR_MSG.format(
                file_name=file_name,
                exception=exception,
            )
        )

    def write_validation_error(self, object_name, error_obj):
        self.stderr.write(
            self.plain_format.format(
                object_name=object_name,
                error=error_obj,
            )
        )


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
    elif arguments["output"] == "plain" and arguments["error_format"] is None:
        arguments["error_format"] = "{error.instance}: {error.message}\n",
    return arguments


def _make_validator(schema_path, validator_class, output_writer):
    try:
        schema_obj = _load_json_file(schema_path)
    except (ValueError, IOError) as exc:
        output_writer.write_parsing_error(schema_path, exc)
        raise exc

    try:
        validator = validator_class(schema=schema_obj)
        validator.check_schema(schema_obj)
    except SchemaError as exc:
        output_writer.write_validation_error(schema_path, exc)
        raise exc

    return validator


def _load_stdin(stdin, output_writer):
    try:
        instance_obj = json.load(stdin)
    except ValueError as exc:
        output_writer.write_parsing_error("stdin", exc)
        raise exc
    return instance_obj


def _load_instance_file(instance_path, output_writer):
    try:
        instance_obj = _load_json_file(instance_path)
    except (ValueError, IOError) as exc:
        output_writer.write_parsing_error(instance_path, exc)
        raise exc
    return instance_obj


def _validate_instance(instance_name, instance_obj, validator, output_writer):
    instance_errored = False
    for error in validator.iter_errors(instance_obj):
        instance_errored = True
        output_writer.write_validation_error(instance_name, error)

    if not instance_errored:
        output_writer.write_validation_success(instance_name)
    else:
        raise ValidationError("Some errors appeared in this instance.")


def main(args=sys.argv[1:]):
    sys.exit(run(arguments=parse_args(args=args)))


def run(arguments, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin):
    if arguments["output"] == "plain":
        output_writer = _PlainOutputWriter(
            arguments["error_format"],
            stdout,
            stderr,
        )
    elif arguments["output"] == "pretty":
        output_writer = _PrettyOutputWriter(
            stdout,
            stderr,
        )

    try:
        validator = _make_validator(
            arguments["schema"],
            arguments["validator"],
            output_writer,
        )
    except (IOError, ValueError, SchemaError):
        return True

    errored = False
    if arguments["instances"]:
        for instance_path in arguments["instances"]:
            try:
                _validate_instance(
                    instance_path,
                    _load_instance_file(instance_path, output_writer),
                    validator,
                    output_writer,
                )
            except (ValueError, IOError, ValidationError):
                errored = True
    elif (
        stdin is sys.stdin and not sys.stdin.isatty()
        or stdin is not sys.stdin and stdin is not None
    ):
        try:
            _validate_instance(
                "stdin",
                _load_stdin(stdin, output_writer),
                validator,
                output_writer,
            )
        except (ValueError, ValidationError):
            errored = True

    return errored
