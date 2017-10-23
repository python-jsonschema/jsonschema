#!/usr/bin/env python
"""
A performance benchmark using the example from issue #.

"""
from bp.filepath import FilePath
from perf import Runner
from pyrsistent import m

from jsonschema.tests._suite import Collection
import jsonschema


def main():
    runner = Runner()
    collection = Collection(
        path=FilePath(__file__).sibling("issue"),
        remotes=m(),
        name="issue",
        validator=jsonschema.Draft4Validator,
    )
    for test in collection.tests():
        runner.bench_func(
            name=test.fully_qualified_name,
            func=test.validate_ignoring_errors,
        )


if __name__ == "__main__":
    main()
