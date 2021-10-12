import argparse
import sys

from jsonschema.cli import (
    _CannotLoadFile,
    _namedAnyWithDefault,
    _Outputter,
    _validate_instance,
)
from jsonschema.exceptions import SchemaError
from jsonschema.validators import RefResolver, validator_for

parser = argparse.ArgumentParser(
    description="JSON Schema Validation pre-commit CLI",
)
parser.add_argument(
    "-s", "--schema",
    required=True,
    help="the path to a JSON Schema to validate with (i.e. schema.json)",
)
parser.add_argument(
    "-F", "--error-format",
    help="""
        the format to use for each validation error message, specified
        in a form suitable for str.format. This string will be passed
        one formatted object named 'error' for each ValidationError.
        Only provide this option when using --output=plain, which is the
        default. If this argument is unprovided and --output=plain is
        used, a simple default representation will be used."
    """,
)
parser.add_argument(
    "-o", "--output",
    choices=["plain", "pretty"],
    default="plain",
    help="""
        an output format to use. 'plain' (default) will produce minimal
        text with one line for each error, while 'pretty' will produce
        more detailed human-readable output on multiple lines.
    """,
)
parser.add_argument(
    "-V", "--validator",
    type=_namedAnyWithDefault,
    help="""
        the fully qualified object name of a validator to use, or, for
        validators that are registered with jsonschema, simply the name
        of the class.
    """,
)
parser.add_argument(
    "--base-uri",
    help="""
        a base URI to assign to the provided schema, even if it does not
        declare one (via e.g. $id). This option can be used if you wish to
        resolve relative references to a particular URI (or local path)
    """,
)
parser.add_argument(
    "files",
    nargs="*",
    help="the path to a JSON Schema to validate with (i.e. schema.json)",
)


def parse_args(args):
    arguments = vars(parser.parse_args(args=args))
    if arguments["output"] != "plain" and arguments["error_format"]:
        raise parser.error(
            "--error-format can only be used with --output plain",
        )
    if arguments["output"] == "plain" and arguments["error_format"] is None:
        arguments["error_format"] = "{error.instance}: {error.message}\n"
    return arguments


def run(arguments, stdout=sys.stdout, stderr=sys.stderr):
    outputter = _Outputter.from_arguments(
        arguments=arguments,
        stdout=stdout,
        stderr=stderr,
    )

    try:
        schema = outputter.load(arguments["schema"])
    except _CannotLoadFile:
        return 1

    if arguments["validator"] is None:
        arguments["validator"] = validator_for(schema)

    try:
        arguments["validator"].check_schema(schema)
    except SchemaError as error:
        outputter.validation_error(
            instance_path=arguments["schema"],
            error=error,
        )
        return 1

    load, instances = outputter.load, arguments["files"]

    resolver = RefResolver(
        base_uri=arguments["base_uri"],
        referrer=schema,
    ) if arguments["base_uri"] is not None else None

    validator = arguments["validator"](schema, resolver=resolver)
    exit_code = 0
    for each in instances:
        try:
            instance = load(each)
        except _CannotLoadFile:
            exit_code = 1
        else:
            exit_code |= _validate_instance(
                instance_path=each,
                instance=instance,
                validator=validator,
                outputter=outputter,
            )

    return exit_code


def main(argv=None):
    return run(arguments=parse_args(argv))


if __name__ == '__main__':
    sys.exit(main())
