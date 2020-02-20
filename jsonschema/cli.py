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
from jsonschema.exceptions import SchemaError


#------------------------------------------------------------------------------
# CONSTANTS
#------------------------------------------------------------------------------
HUMAN_ERROR_MSG = "===[ERROR]===({instance_name})===\n{error}\n"
HUMAN_SUCCESS_MSG = "===[SUCCESS]===({instance_name})===\n"


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
        "the format to use for each error output message, specified in "
        "a form suitable for passing to str.format, which will be called "
        "with 'error' for each error"
    ),
)
parser.add_argument(
    "-H", "--human",
    action="store_true",
    help=(
        "Format the output in a human readable way. For each instance, it "
        "prints a success message when all validation passed, and prints "
        "a detailed error report if at least one validation failed."
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


def main(args=sys.argv[1:]):
    sys.exit(run(arguments=parse_args(args=args)))


def run(arguments, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin):
    # Build the validator
    try:
        schema_obj = _load_json_file(arguments["schema"])
    except json.JSONDecodeError as exc:
        stderr.write(
            "Failed to parse schema {}. Got the following error: {}\n"
            .format(arguments["schema"], exc)
        )
        return False
    validator = arguments["validator"](schema=schema_obj)

    # Check the schema before validating any instance
    try:
        validator.check_schema(schema_obj)
    except SchemaError as exc:
        if arguments["human"]:
            error_content = exc
        else:
            error_content = (
                "{error.instance}: {error.message}".format(error=exc)
            )
        stderr.write(
            "Failed to check schema {}. Got the following error: {}\n"
            .format(arguments["schema"], error_content)
        )
        return False

    # This variable indicates if at least one instance failed
    errored = False

    # Loop on instances (files and/or stdin)
    for instance in arguments["instances"] or [json.load(stdin)]:
        # Load the instance and set the instance name
        if isinstance(instance, str):
            instance_name = instance
            try:
                instance_obj = _load_json_file(instance)
            except json.JSONDecodeError as exc:
                error_msg = (
                    "Failed to parse {}. Got the following error: {}\n"
                    .format(instance_name, exc)
                )
                if arguments["human"]:
                    stderr.write(HUMAN_ERROR_MSG.format(
                        instance_name=instance_name,
                        error=error_msg
                    ))
                else:
                    stderr.write(error_msg)
                # Skip this instance
                errored = True
                continue
        else:
            instance_name = "stdin"
            instance_obj = instance

        # Validate this instance
        instance_errored = False
        for error in validator.iter_errors(instance_obj):
            instance_errored = True
            errored = True
            # Print the appropriate error message
            if arguments["human"]:
                stderr.write(HUMAN_ERROR_MSG.format(
                    error=error,
                    instance_name=instance_name
                ))
            else:
                stderr.write(arguments["error_format"].format(
                    error=error,
                    instance_name=instance_name
                ))
        if not instance_errored and arguments["human"]:
            stdout.write(HUMAN_SUCCESS_MSG.format(
                instance_name=instance_name
            ))

    return errored
