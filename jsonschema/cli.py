"""
The ``jsonschema`` command line.
"""

from __future__ import absolute_import
import argparse
import json
import sys

from jsonschema import __version__
from jsonschema._reflect import namedAny
from jsonschema.validators import validator_for
from jsonschema.exceptions import SchemaError, ValidationError


class CliOutputWriter():
    PARSING_ERROR_MSG = (
        "Failed to parse {file_name}. "
        "Got the following error: {exception}\n"
    )
    PRETTY_ERROR_MSG = "===[ERROR]===({object_name})===\n{error}\n"
    PRETTY_SUCCESS_MSG = "===[SUCCESS]===({object_name})===\n"

    def __init__(
        self,
        output_format,
        plain_format,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        self.output_format = output_format
        self.plain_format = plain_format
        self.stdout = stdout
        self.stderr = stderr

    def write_parsing_error(self, file_name, exception):
        if self.output_format == "pretty":
            msg = self.PRETTY_ERROR_MSG.format(
                object_name=file_name,
                error=self.PARSING_ERROR_MSG.format(
                    file_name=file_name,
                    exception=exception,
                ),
            )
        elif self.output_format == "plain":
            msg = self.PARSING_ERROR_MSG.format(
                file_name=file_name,
                exception=exception,
            )
        else:  # pragma: no cover
            raise ValueError(
                "Output mode '{}' is unknown by this function"
                .format(self.output_format)
            )
        self.stderr.write(msg)

    def write_validation_error(self, object_name, error_obj):
        if self.output_format == "pretty":
            msg = self.PRETTY_ERROR_MSG.format(
                object_name=object_name,
                error=error_obj,
            )
        elif self.output_format == "plain":
            msg = self.plain_format.format(
                object_name=object_name,
                error=error_obj,
            )
        else:  # pragma: no cover
            raise ValueError(
                "Output mode '{}' is unknown by this function"
                .format(self.output_format)
            )
        self.stderr.write(msg)

    def write_validation_success(self, object_name):
        if self.output_format == "pretty":
            msg = self.PRETTY_SUCCESS_MSG.format(
                object_name=object_name
            )
        elif self.output_format == "plain":
            # Nothing to print in plain mode, only errors are wanted.
            msg = ""
        else:  # pragma: no cover
            raise ValueError(
                "Output mode '{}' is unknown by this function"
                .format(self.output_format)
            )
        self.stdout.write(msg)


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
    default="{error.instance}: {error.message}\n",
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
    return arguments


def make_validator(schema_path, validator_class, output_writer):
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


def load_stdin(stdin, output_writer):
    try:
        instance_obj = json.load(stdin)
    except ValueError as exc:
        output_writer.write_parsing_error("stdin", exc)
        raise exc
    return instance_obj


def load_instance_file(instance_path, output_writer):
    try:
        instance_obj = _load_json_file(instance_path)
    except (ValueError, IOError) as exc:
        output_writer.write_parsing_error(instance_path, exc)
        raise exc
    return instance_obj


def validate_instance(instance_name, instance_obj, validator, output_writer):
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
    output_writer = CliOutputWriter(
        arguments["output"],
        arguments["error_format"],
        stdout,
        stderr,
    )

    try:
        validator = make_validator(
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
                validate_instance(
                    instance_path,
                    load_instance_file(instance_path, output_writer),
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
            validate_instance(
                "stdin",
                load_stdin(stdin, output_writer),
                validator,
                output_writer,
            )
        except (ValueError, ValidationError):
            errored = True

    return errored
