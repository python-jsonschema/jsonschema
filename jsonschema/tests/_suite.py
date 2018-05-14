"""
Python representations of the JSON Schema Test Suite tests.

"""

import json
import os
import re
import subprocess
import sys

from bp.filepath import FilePath
from pyrsistent import pmap
import attr

from jsonschema.compat import PY3
from jsonschema.validators import validators
import jsonschema


def _find_suite():
    root = os.environ.get("JSON_SCHEMA_TEST_SUITE")
    if root is not None:
        return FilePath(root)

    root = FilePath(jsonschema.__file__).parent().sibling("json")
    if not root.isdir():
        raise ValueError(
            (
                "Can't find the JSON-Schema-Test-Suite directory. "
                "Set the 'JSON_SCHEMA_TEST_SUITE' environment "
                "variable or run the tests from alongside a checkout "
                "of the suite."
            ),
        )
    return root


@attr.s(hash=True)
class Suite(object):

    _root = attr.ib(default=attr.Factory(_find_suite))

    def _remotes(self):
        jsonschema_suite = self._root.descendant(["bin", "jsonschema_suite"])
        remotes = subprocess.check_output(
            [sys.executable, jsonschema_suite.path, "remotes"],
        )
        return {
            "http://localhost:1234/" + name: schema
            for name, schema in json.loads(remotes.decode("utf-8")).items()
        }

    def benchmark(self, runner):
        for name in validators:
            self.collection(name=name).benchmark(runner=runner)

    def collection(self, name):
        return Collection(
            name=name,
            path=self._root.descendant(["tests", name]),
            validator=validators[name],
            remotes=self._remotes(),
        )


@attr.s(hash=True)
class Collection(object):

    _path = attr.ib()
    _remotes = attr.ib()

    name = attr.ib()
    validator = attr.ib()

    def benchmark(self, runner):
        for test in self.tests():
            runner.bench_func(
                name=test.fully_qualified_name,
                func=test.validate_ignoring_errors,
            )

    def tests(self):
        return (
            test
            for child in self._path.globChildren("*.json")
            for test in self._tests_in(
                subject=child.basename()[:-5],
                path=child,
            )
        )

    def format_tests(self):
        path = self._path.descendant(["optional", "format"])
        return (
            test
            for child in path.globChildren("*.json")
            for test in self._tests_in(
                subject=child.basename()[:-5],
                path=child,
            )
        )

    def tests_of(self, name):
        return self._tests_in(
            subject=name,
            path=self._path.child(name + ".json"),
        )

    def optional_tests_of(self, name):
        return self._tests_in(
            subject=name,
            path=self._path.descendant(["optional", name + ".json"]),
        )

    def _tests_in(self, subject, path):
        for each in json.loads(path.getContent().decode("utf-8")):
            for test in each["tests"]:
                yield _Test(
                    collection=self,
                    subject=subject,
                    case_description=each["description"],
                    schema=each["schema"],
                    remotes=self._remotes,
                    **test
                )


@attr.s(hash=True, repr=False)
class _Test(object):

    collection = attr.ib()

    subject = attr.ib()
    case_description = attr.ib()
    description = attr.ib()

    data = attr.ib()
    schema = attr.ib(repr=False)

    valid = attr.ib()

    _remotes = attr.ib()
    _validate_kwargs = attr.ib(default=pmap())

    def __repr__(self):
        return "<Test {}>".format(self.fully_qualified_name)

    @property
    def fully_qualified_name(self):
        return " > ".join(
            [
                self.collection.name,
                self.subject,
                self.case_description,
                self.description,
            ]
        )

    def to_unittest_method(self):
        name = "test_%s_%s_%s" % (
            self.subject,
            re.sub(r"[\W ]+", "_", self.case_description),
            re.sub(r"[\W ]+", "_", self.description),
        )

        if not PY3:
            name = name.encode("utf-8")

        if self.valid:
            def fn(this):
                self.validate()
        else:
            def fn(this):
                with this.assertRaises(jsonschema.ValidationError):
                    self.validate()

        fn.__name__ = name
        return fn

    def validate(self):
        resolver = jsonschema.RefResolver.from_schema(
            schema=self.schema, store=self._remotes,
        )
        jsonschema.validate(
            instance=self.data,
            schema=self.schema,
            cls=self.collection.validator,
            resolver=resolver,
            **self._validate_kwargs
        )

    def validate_ignoring_errors(self):
        try:
            self.validate()
        except jsonschema.ValidationError:
            pass

    def with_validate_kwargs(self, **kwargs):
        validate_kwargs = self._validate_kwargs.update(kwargs)
        return attr.evolve(self, validate_kwargs=validate_kwargs)
