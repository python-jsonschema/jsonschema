'use strict';

var Ajv = require('ajv');
var jsonSchemaTest = require('json-schema-test');
var assert = require('assert');

var refs = {
  'http://localhost:1234/integer.json': require('./remotes/integer.json'),
  'http://localhost:1234/subSchemas.json': require('./remotes/subSchemas.json'),
  'http://localhost:1234/folder/folderInteger.json': require('./remotes/folder/folderInteger.json'),
  'http://localhost:1234/name.json': require('./remotes/name.json')
};

runTest(4);
runTest(6);

function runTest(draft) {
  var opts = {
    format: 'full',
    formats: {'json-pointer': /^(?:\/(?:[^~\/]|~0|~1)*)*$/}
  };
  if (draft == 4) opts.meta = false;
  var ajv = new Ajv(opts);
  ajv.addMetaSchema(require('ajv/lib/refs/json-schema-draft-04.json'));
  if (draft == 4) ajv._opts.defaultMeta = 'http://json-schema.org/draft-04/schema#';
  for (var uri in refs) ajv.addSchema(refs[uri], uri);

  jsonSchemaTest(ajv, {
    description: 'Test suite draft-0' + draft,
    suites: {tests: './tests/draft' + draft + '/{**/,}*.json'},
    skip: draft == 4 ? ['optional/zeroTerminatedFloats'] : [],
    cwd: __dirname,
    hideFolder: 'tests/'
  });
}
