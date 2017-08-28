#!/usr/env/bin python
"""Benchmark the performance of jsonschema.

This benchmarks jsonschema using a standard example.
"""
import os

import jsonschema
from perf import Runner

from utils import load_json_test_cases, performance_test


def main():
    runner = Runner()
    cases = load_json_test_cases(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests'),
        'standard',
    )
    performance_test(runner, cases, jsonschema.Draft4Validator)


if __name__ == "__main__":
    main()
