import time

from jsonschema.tests.compat import unittest
from jsonschema.validators import (
    Draft3Validator, Draft4Validator, validate,
)


class TestBenchmarks(unittest.TestCase):

    def run_for_sometime(self, sec):
        now = time.time()
        then = now + sec
        run = 0
        while now < then:
            yield run
            run += 1
            now = time.time()

    run_interval_sec = 2.0

    def print_results(self, runs, interval_sec):
        print("%i runs in %s sec\n\t%.2f ms/run, %.4f runs/sec" % (runs, interval_sec, 1000*interval_sec/(runs), interval_sec / runs))

    def test_V3_meta_schema(self):
        runs = 0
        for run in self.run_for_sometime(self.run_interval_sec):
            runs = run
            v_class = Draft3Validator
            schema = v_class.META_SCHEMA
            v_class(schema).validate(schema)

        self.print_results(runs, self.run_interval_sec)


    def test_V4_meta_schema(self):
        runs = 0
        for run in self.run_for_sometime(self.run_interval_sec):
            runs = run
            v_class = Draft4Validator
            schema = v_class.META_SCHEMA
            v_class(schema).validate(schema)

        self.print_results(runs, self.run_interval_sec)


    def test_both_meta_schemas(self):
        v_classes = [Draft3Validator, Draft4Validator]
        runs = 0
        for run in self.run_for_sometime(self.run_interval_sec):
            runs = run
            for v_class in v_classes:
                schema = v_class.META_SCHEMA
                v_class(schema).validate(schema)


        self.print_results(runs, self.run_interval_sec)
