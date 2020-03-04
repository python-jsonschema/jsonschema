import asyncio
import unittest
from unittest import TestCase

from jsonschema import exceptions, validators
from jsonschema.compat import PY36


async def async_validator(validator, value, instance, schema):
    await asyncio.sleep(0)
    if not value:
        yield exceptions.ValidationError(u"Async whoops!")


@unittest.skipIf(not PY36, "Asynchronous validation is not supported before Python 3.6")
class TestAsyncIterErrors(TestCase):
    def setUp(self):
        all_validators = dict(validators.Draft7Validator.VALIDATORS)
        all_validators['async_valid'] = async_validator
        self.validator = validators.create(
            meta_schema=validators.Draft7Validator.META_SCHEMA,
            validators=all_validators,
        )({})

    def test_async_iter_errors(self):
        async def _test_async_iter_errors():
            instance = {}
            schema = {
                u"async_valid": False,
            }
            expected = [u"Async whoops!"]
            got = []
            async for e in self.validator.async_iter_errors(instance, schema):
                got.append(e.message)
            self.assertEqual(got, expected)

        asyncio.get_event_loop().run_until_complete(_test_async_iter_errors())

    def test_not_supported_async_iter_errors(self):
        instance = {}
        schema = {
            u"async_valid": False,
        }
        expected = [u"async validation not supported"]
        got = [e.message for e in self.validator.iter_errors(instance, schema)]
        self.assertEqual(got, expected)

    def test_async_breakpoint_with_anyof(self):
        async def _test_async_breakpoint_with_anyof():
            instance = {}
            schema = {
                u"anyOf": [
                    {
                        u"async_valid": True,
                    }, {
                        u"type": u"string",
                    },
                ],
            }
            errors = []
            async for e in self.validator.async_iter_errors(instance, schema):
                errors.append(e)
            self.assertEqual(len(errors), 0)

        asyncio.get_event_loop().run_until_complete(
            _test_async_breakpoint_with_anyof()
        )
