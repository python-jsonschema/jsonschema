import glob
import json
import os
from collections import namedtuple
from functools import partial

import jsonschema

TestCase = namedtuple('TestCase', ['name', 'data', 'schema'])


def load_json_test_cases(test_dir, name_prefix):
    cases = []
    for filepath in glob.iglob(os.path.join(test_dir, '*.json')):
        if 'ref' in filepath:
            continue
        with open(filepath) as file_:
            groups = json.load(file_)
        for group in groups:
            for test in group['tests']:
                if test['valid']:
                    name = "{} {} {}".format(
                        name_prefix, group['description'], test['description'],
                    )
                    cases.append(TestCase(name, test['data'], group['schema']))
    return cases


def performance_test(runner, cases, validator_class):
    validate = partial(jsonschema.validate, cls=validator_class)
    for case in cases:
        runner.bench_func(case.name, validate, case.data, case.schema)
