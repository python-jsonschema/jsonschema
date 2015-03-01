#!/usr/env/bin python
"""
Benchmark the performance of jsonschema.

Example benchmark:

    wget http://swagger.io/v2/schema.json
    wget http://petstore.swagger.io/v2/swagger.json
    python bench.py -r 5 schema.json swagger.json

"""
from __future__ import print_function
import argparse
import cProfile
import json
import time

import jsonschema


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('schema', help="path to a schema used to benchmark")
    parser.add_argument('document', help="document to validate with schema")
    parser.add_argument('-r', '--repeat', type=int, help="number of iterations")
    parser.add_argument('--profile',
                        help="Enable profiling, write profile to this filepath")
    return parser.parse_args()


def run(filename, schema, document):
    resolver = jsonschema.RefResolver(
        'file://{0}'.format(filename),
        schema,
        store={schema['id']: schema})
    jsonschema.validate(document, schema, resolver=resolver)


def format_time(time_):
    return "%.3fms" % (time_ * 1000)


def run_timeit(schema_filename, document_filename, repeat, profile):
    with open(schema_filename) as schema_file:
        schema = json.load(schema_file)

    with open(document_filename) as fh:
        document = json.load(fh)

    if profile:
        profiler = cProfile.Profile()
        profiler.enable()

    times = []
    for _ in range(repeat):
        start_time = time.time()
        run(schema_filename, schema, document)
        times.append(time.time() - start_time)

    if profile:
        profiler.disable()
        profiler.dump_stats(profile)

    print(", ".join(map(format_time, sorted(times))))
    print("Mean: {0}".format(format_time(sum(times) / repeat)))


def main():
    args = parse_args()
    run_timeit(args.schema, args.document, args.repeat, args.profile)


if __name__ == "__main__":
    main()
