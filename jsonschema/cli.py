# encoding=utf-8

import argparse
import json

from jsonschema import validate

def main():
    parser = argparse.ArgumentParser(description='JSON Schema validator')
    parser.add_argument('schema', help='filename of the JSON Schema')
    parser.add_argument('document', help='filename of the JSON document to validate')
    args = parser.parse_args()

    schema = json.load(open(args.schema, 'r'))
    document = json.load(open(args.document, 'r'))

    validate(document, schema)
    # validate raises if the document is invalid, and will show a Traceback to
    # the user. If the document is valid, show a congratulating message.
    print("√ JSON document is valid.")

if __name__ == '__main__':
    main()
