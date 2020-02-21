"""
The ``jsonschema`` command line.
"""

#------------------------------------------------------------------------------
# IMPORTS
#------------------------------------------------------------------------------
from __future__ import absolute_import
import argparse
import json
import sys

from jsonschema import __version__
from jsonschema._reflect import namedAny
from jsonschema.validators import validator_for
from jsonschema.exceptions import SchemaError, ValidationError


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------
class CliOutputWriter():
    PARSING_ERROR_MSG = (
        "Failed to parse {file_name}. "
        "Got the following error: {exception}\n"
    )
    PLAIN_ERROR_MSG = "{error.instance}: {error.message}\n"
    PRETTY_ERROR_MSG = "===[ERROR]===({object_name})===\n{error}\n"
    PRETTY_SUCCESS_MSG = "===[SUCCESS]===({object_name})===\n"

    def __init__(
        self,
        output_format,
        oneline_format,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        self.output_format = output_format
        self.oneline_format = oneline_format
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
        else:
            raise ValueError(
                "Output mode '{}' is unknown by this function"
                .format(self.output_format)
            )
        self.stderr.write(msg)

    def write_valid_error(self, object_name, error_obj):
        if self.output_format == "pretty":
            msg = self.PRETTY_ERROR_MSG.format(
                object_name=object_name,
                error=error_obj,
            )
        elif self.output_format == "plain":
            msg = self.PLAIN_ERROR_MSG.format(
                object_name=object_name,
                error=error_obj,
            )
        else:
            raise ValueError(
                "Output mode '{}' is unknown by this function"
                .format(self.output_format)
            )
        self.stderr.write(msg)

    def write_valid_success(self, object_name):
        if self.output_format == "pretty":
            msg = self.PRETTY_SUCCESS_MSG.format(
                object_name=object_name
            )
        elif self.output_format == "plain":
            # Nothing to print in plain mode, only errors are wanted.
            msg = ""
        else:
            raise ValueError(
                "Output mode '{}' is unknown by this function"
                .format(self.output_format)
            )
        self.stdout.write(msg)


#------------------------------------------------------------------------------
# FUNCTIONS USED BY ARGPARSE
#------------------------------------------------------------------------------
def _namedAnyWithDefault(name):
    if "." not in name:
        name = "jsonschema." + name
    return namedAny(name)


#------------------------------------------------------------------------------
# ARGUMENT PARSING
#------------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="JSON Schema Validation CLI",
)
parser.add_argument(
    "-i", "--instance",
    action="append",
    dest="instances",
    type=str,
    help=(
        "a path to a JSON instance (i.e. filename.json) "
        "to validate (may be specified multiple times)"
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
    help="the JSON Schema to validate with (i.e. schema.json)",
    type=str,
)


#------------------------------------------------------------------------------
# FUNCTIONS USED BY THE CLI
#------------------------------------------------------------------------------
def _load_json_file(path):
    with open(path) as file:
        return json.load(file)


def parse_args(args):
    arguments = vars(parser.parse_args(args=args or ["--help"]))
    if arguments["validator"] is None:
        arguments["validator"] = validator_for(arguments["schema"])
    return arguments


def make_validator(schema_path, validator_class):
    schema_obj = _load_json_file(schema_path)
    validator = validator_class(schema=schema_obj)
    validator.check_schema(schema_obj)
    return validator


def validate_instance(instance, validator, output_writer):
    # Load the instance
    if isinstance(instance, str):
        instance_name = instance
        try:
            instance_obj = _load_json_file(instance)
        except json.JSONDecodeError as exc:
            output_writer.write_parsing_error(instance_name, exc)
            raise exc
    elif isinstance(instance, dict):
        instance_name = "stdin"
        instance_obj = instance
    else:
        raise ValueError(
            "Invalid type for instance: {}".format(type(instance))
        )

    # Validate the instance
    instance_errored = False
    for error in validator.iter_errors(instance_obj):
        instance_errored = True
        output_writer.write_valid_error(instance_name, error)

    if not instance_errored:
        output_writer.write_valid_success(instance_name)
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
        validator = make_validator(arguments["schema"], arguments["validator"])
    except json.JSONDecodeError as exc:
        output_writer.write_parsing_error(arguments["schema"], exc)
        return False
    except SchemaError as exc:
        output_writer.write_valid_error(arguments["schema"], exc)
        return False

    errored = False
    for instance in arguments["instances"] or [json.load(stdin)]:
        try:
            validate_instance(instance, validator, output_writer)
        except (json.JSONDecodeError, ValidationError):
            errored = True

    return errored
