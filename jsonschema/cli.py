from __future__ import absolute_import
import argparse
import json
import sys

from jsonschema._reflect import namedAny
from jsonschema.validators import validator_for


def _namedAnyWithDefault(name):
    if "." not in name:
        name = "jsonschema." + name
    return namedAny(name)


def _json_file(path):
    with open(path) as file:
        return json.load(file)


parser = argparse.ArgumentParser(
    description="JSON Schema Validation CLI",
)
input_group = parser.add_mutually_exclusive_group()
input_group.add_argument(
    "-i", "--instance",
    action="append",
    dest="instances",
    type=_json_file,
    help=(
        "a path to a JSON instance (i.e. filename.json)"
        "to validate (may be specified multiple times)"
    ),
)
input_group.add_argument(
    "-f", "--filter",
    action="store_true",
    help="read instances one to a line from stdin, output those that validate "
         "in compact form and log to stderr those that do not."
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
    "-V", "--validator",
    type=_namedAnyWithDefault,
    help=(
        "the fully qualified object name of a validator to use, or, for "
        "validators that are registered with jsonschema, simply the name "
        "of the class."
    ),
)

parser.add_argument(
    "schema",
    help="the JSON Schema to validate with (i.e. filename.schema)",
    type=_json_file,
)


def parse_args(args):
    arguments = vars(parser.parse_args(args=args or ["--help"]))
    if arguments["validator"] is None:
        arguments["validator"] = validator_for(arguments["schema"])
    return arguments


def main(args=sys.argv[1:]):
    sys.exit(run(arguments=parse_args(args=args)))


def run(arguments, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    error_format = arguments["error_format"]
    validator = arguments["validator"](schema=arguments["schema"])

    validator.check_schema(arguments["schema"])

    errored = False
    instances = (json.loads(line) for line in stdin) if arguments.get("filter") else (arguments.get("instances") or ())
    for instance in instances:
        errors = tuple(validator.iter_errors(instance))
        if errors:
            errored = True
            for error in errors:
                stderr.write(error_format.format(error=error))
        elif arguments.get("filter"):
            json.dump(instance, stdout, separators=(',', ':'))
            stdout.write('\n')
    return errored
