#!/usr/bin/env python
"""
A performance benchmark using the official test suite.

This benchmarks jsonschema using every valid example in the
JSON-Schema-Test-Suite. It will take some time to complete.
"""
from perf import Runner

from jsonschema.tests._suite import Suite


def main():
    runner = Runner()
    suite = Suite()
    for version in suite.versions():
        for test in version.tests():
            runner.bench_func(
                name=test.fully_qualified_name,
                func=test.validate_ignoring_errors,
            )


if __name__ == "__main__":
    main()
