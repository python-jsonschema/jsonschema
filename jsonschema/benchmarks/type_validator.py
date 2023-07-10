"""
Compare the performance of type validator implementations.
"""
from pyperf import Runner

from jsonschema._utils import ensure_list
from jsonschema.exceptions import ValidationError
import jsonschema.validators


def type_any_generator(validator, types, instance, schema):
    types = ensure_list(types)

    if not any(validator.is_type(instance, type) for type in types):
        reprs = ", ".join(repr(type) for type in types)
        yield ValidationError(f"{instance!r} is not of type {reprs}")


def type_for_loop(validator, types, instance, schema):
    types = ensure_list(types)

    for type in types:
        if validator.is_type(instance, type):
            break
    else:
        reprs = ", ".join(repr(type) for type in types)
        yield ValidationError(f"{instance!r} is not of type {reprs}")


schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "properties": {
        "array": {"type": "array"},
        "boolean": {"type": "boolean"},
        "integer": {"type": "integer"},
        "object": {"type": "object"},
        "null": {"type": "null"},
        "number": {"type": "number"},
        "string": {"type": "string"},
    }
}

validator_any_generator = jsonschema.validators.extend(
    jsonschema.validators.Draft4Validator,
    validators={
        "type": type_any_generator,
    },
)(schema)

validator_for_loop = jsonschema.validators.extend(
    jsonschema.validators.Draft4Validator,
    validators={
        "type": type_for_loop,
    },
)(schema)

instance = {
    "array": "",
    "boolean": "",
    "integer": "",
    "object": "",
    "null": "",
    "number": "",
    "string": 1,
}

if __name__ == "__main__":
    runner = Runner()

    runner.bench_func(
        "any generator",
        lambda: list(validator_any_generator.iter_errors(instance)),
    )
    runner.bench_func(
        "for loop",
        lambda: list(validator_for_loop.iter_errors(instance)),
    )
