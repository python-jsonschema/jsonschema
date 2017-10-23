#!/usr/bin/env python
"""
A performance benchmark using the example from issue #.

"""
from bp.filepath import FilePath
from perf import Runner
from pyrsistent import m

from jsonschema.tests._suite import Collection
import jsonschema


collection = Collection(
    path=FilePath(__file__).sibling("issue"),
    remotes=m(),
    name="issue",
    validator=jsonschema.Draft4Validator,
)


if __name__ == "__main__":
    collection.benchmark(runner=Runner())
