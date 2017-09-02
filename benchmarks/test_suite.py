#!/usr/env/bin python
"""Benchmark the performance of jsonschema.

This benchmarks jsonschema using every valid example in the
JSON-Schema-Test-Suite. It will take some time to complete.
"""

import os

from perf import Runner
from utils import load_json_test_cases, performance_test

import jsonschema


REPO_ROOT = os.path.join(os.path.dirname(jsonschema.__file__), os.path.pardir)
SUITE = os.getenv("JSON_SCHEMA_TEST_SUITE", os.path.join(REPO_ROOT, "json"))
TESTS_DIR = os.path.join(SUITE, "tests")


def main():
    runner = Runner()
    draft3_cases = load_json_test_cases(os.path.join(TESTS_DIR, 'draft3'), 'draft3')
    performance_test(runner, draft3_cases, jsonschema.Draft3Validator)
    draft4_cases = load_json_test_cases(os.path.join(TESTS_DIR, 'draft4'), 'draft4')
    performance_test(runner, draft4_cases, jsonschema.Draft4Validator)



if __name__ == "__main__":
    main()
