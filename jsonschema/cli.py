import argparse
import json
import sys

from . import (
    validate, Draft4Validator, Draft3Validator,
    draft3_format_checker, draft4_format_checker,
)
from .validators import validator_for


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='JSON Schema validator')
    parser.add_argument('schema', help='filename of the JSON Schema')
    parser.add_argument('document', help='filename of the JSON document to validate')
    parser.add_argument('--format', help='validate value format', action='store_true')
    args = parser.parse_args(args)

    schema = json.load(open(args.schema, 'r'))
    document = json.load(open(args.document, 'r'))

    validator = validator_for(schema)
    if args.format:
        if validator == Draft4Validator:
            format_checker = draft4_format_checker
        elif validator == Draft3Validator:
            format_checker = draft3_format_checker
        else:
            raise NotImplementedError("No format validator for %s specified"
                                      % validator.__name__)
    else:
        format_checker = None

    validate(document, schema, validator, format_checker=format_checker)
    # validate raises if the document is invalid, and will show a Traceback to
    # the user. If the document is valid, show a congratulating message.
    print("JSON document is valid.")

if __name__ == '__main__':
    main()
