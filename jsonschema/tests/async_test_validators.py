import asyncio
import unittest
from unittest import TestCase

from jsonschema import exceptions, validators
from jsonschema.compat import PY36

async def async_validator(validator, value, instance, schema):
    await asyncio.sleep(0)
    yield exceptions.ValidationError(u"Async whoops!")

@unittest.skipIf(not PY36, "Asynchronous validation is not supported before Python 3.6")
class TestAsyncIterErrors(TestCase):
    def setUp(self):
        all_validators = dict(validators.Draft3Validator.VALIDATORS)
        all_validators['async'] = async_validator
        self.validator = validators.create(
            meta_schema=validators.Draft3Validator.META_SCHEMA,
            validators=all_validators,
        )({})

    def test_async_iter_errors(self):
        async def _test_async_iter_errors():
            instance = {}
            schema = {
                u"async": True
            }
            expected = [u"Async whoops!"]
            got = [e.message async for e in self.validator.async_iter_errors(instance, schema)]
            self.assertEqual(sorted(got), sorted(expected))

        asyncio.get_event_loop().run_until_complete(_test_async_iter_errors())

    def test_not_supported_async_iter_errors(self):
        instance = {}
        schema = {
            u"async": True
        }
        expected = [u"async validation not supported"]
        got = [e.message for e in self.validator.iter_errors(instance, schema)]
        self.assertEqual(sorted(got), sorted(expected))
