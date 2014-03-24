import StringIO

import pytest

from .compat import mock, unittest
from .. import (
    cli, Draft4Validator, Draft3Validator,
    draft3_format_checker, draft4_format_checker,
)

MOCK_SCHEMAS = {
    'draft3': {"$schema": "http://json-schema.org/draft-03/schema#"},
    'draft4': {"$schema": "http://json-schema.org/draft-04/schema#"},
}


class TestCLI(unittest.TestCase):
    def test_missing_arguments(self):
        with pytest.raises(SystemExit) as e:
            cli.main([])

    @mock.patch('__builtin__.open')
    @mock.patch('jsonschema.cli.validate')
    def test_filename_argument_order(self, validate, open_):
        def mock_file(filename, mode):
            return StringIO.StringIO('{"filename": "%s"}' % filename)
        open_.side_effect = mock_file

        cli.main(['document.json', 'schema.json'])

        open_.assert_has_calls([mock.call('document.json', 'r'),
                                mock.call('schema.json', 'r')],
                               any_order=True)
        self.assertEqual(open_.call_count, 2)

        validate.assert_called_once_with({'filename': 'schema.json'},
                                         {'filename': 'document.json'},
                                         Draft4Validator,
                                         format_checker=None)

    @mock.patch('__builtin__.open')
    @mock.patch('jsonschema.cli.json.load')
    @mock.patch('jsonschema.cli.validate')
    def test_raise_exception(self, validate, json_load, open_):
        validate.side_effect = Exception('Did not validate correctly')
        with pytest.raises(Exception) as e:
            cli.main([None, None])
        self.assertEqual(e.exconly(), "Exception: Did not validate correctly")

    @mock.patch('__builtin__.open')
    @mock.patch('jsonschema.cli.json.load')
    @mock.patch('jsonschema.cli.validate')
    def test_format(self, validate, json_load, open_):
        schema = {"$schema": "http://json-schema.org/draft-04/schema#"}
        json_load.return_value = schema

        cli.main([None, None])
        validate.assert_called_once_with(schema, schema, Draft4Validator,
                                         format_checker=None)
        validate.reset_mock()
        cli.main([None, None, '--format'])
        validate.assert_called_once_with(schema, schema, Draft4Validator,
                                         format_checker=draft4_format_checker)

    @mock.patch('__builtin__.open')
    @mock.patch('jsonschema.cli.json.load')
    @mock.patch('jsonschema.cli.validate')
    def test_draft3(self, validate, json_load, open_):
        schema = {"$schema": "http://json-schema.org/draft-03/schema#"}
        json_load.return_value = schema

        cli.main([None, None])
        validate.assert_called_once_with(schema, schema, Draft3Validator,
                                         format_checker=None)
        validate.reset_mock()
        cli.main([None, None, '--format'])
        validate.assert_called_once_with(schema, schema, Draft3Validator,
                                         format_checker=draft3_format_checker)
