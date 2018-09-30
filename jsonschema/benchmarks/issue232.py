#!/usr/bin/env python
"""
A performance benchmark using the example from issue #232:

https://github.com/Julian/jsonschema/pull/232

"""
from bp.filepath import FilePath
from perf import Runner
from pyrsistent import m

from jsonschema.tests._suite import Collection
import jsonschema


collection = Collection(
    path=FilePath(__file__).sibling("issue232"),
    remotes=m(),
    name="issue232",
    validator=jsonschema.Draft7Validator,
)


if __name__ == "__main__":
    collection.benchmark(runner=Runner())
