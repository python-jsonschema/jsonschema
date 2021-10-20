# JSON Schema Test Suite [![Build Status](https://github.com/json-schema-org/JSON-Schema-Test-Suite/workflows/Test%20Suite%20Sanity%20Checking/badge.svg)](https://github.com/json-schema-org/JSON-Schema-Test-Suite/actions?query=workflow%3A%22Test+Suite+Sanity+Checking%22)

This repository contains a set of JSON objects that implementors of JSON Schema
validation libraries can use to test their validators.

It is meant to be language agnostic and should require only a JSON parser.

The conversion of the JSON objects into tests within your test framework of
choice is still the job of the validator implementor.

## Structure of a Test

The tests in this suite are contained in the `tests` directory at the root of
this repository. Inside that directory is a subdirectory for each draft or
version of the specification.

Inside each draft directory, there are a number of `.json` files and one or more
special subdirectories. The subdirectories contain `.json` files meant for a
specific testing purpose, and each `.json` file logically groups a set of test
cases together. Often the grouping is by property under test, but not always.

The subdirectories are described in the next section.

Inside each `.json` file is a single array containing objects. It's easiest to
illustrate the structure of these with an example:

```json
{
    "description": "The description of the test case",
    "schema": {
        "description": "The schema against which the data in each test is validated",
        "type": "string"
    },
    "tests": [
        {
            "description": "Test for a valid instance",
            "data": "the instance to validate",
            "valid": true
        },
        {
            "description": "Test for an invalid instance",
            "data": 15,
            "valid": false
        }
    ]
}
```

In short: a description, a schema under test, and some tests, where each test
in the `tests` array is an objects with a description of the case itself, the
instance under test, and a boolean indicating whether it should be valid
or invalid.

## Test Subdirectories

There is currently only one subdirectory that may exist within each draft
directory. This is:

1. `optional/`: Contains tests that are considered optional.

## Coverage

All JSON Schema specification releases should be well covered by this suite,
including drafts 2020-12, 2019-09, 07, 06, 04 and 03. Additional coverage is
always welcome, particularly for bugs encountered in real-world
implementations.

Drafts 04 and 03 are considered "frozen" in that less effort is put in to
backport new tests to these versions.

Contributions are very welcome, especially from implementers as they add support
to their own implementations.

If you see anything missing from the current supported drafts, or incorrect on
any draft still accepting bug fixes, please
[file an issue](https://github.com/json-schema-org/JSON-Schema-Test-Suite/issues)
or [submit a PR](https://github.com/json-schema-org/JSON-Schema-Test-Suite).

## Who Uses the Test Suite

This suite is being used by:

### Clojure

* [jinx](https://github.com/juxt/jinx)
* [json-schema](https://github.com/tatut/json-schema)

### Coffeescript

* [jsck](https://github.com/pandastrike/jsck)

### Common Lisp

* [json-schema](https://github.com/fisxoj/json-schema)

### C++

* [Modern C++ JSON schema validator](https://github.com/pboettch/json-schema-validator)

### Dart

* [json\_schema](https://github.com/patefacio/json_schema)

### Elixir

* [ex\_json\_schema](https://github.com/jonasschmidt/ex_json_schema)

### Erlang

* [jesse](https://github.com/for-GET/jesse)

### Go

* [gojsonschema](https://github.com/sigu-399/gojsonschema)
* [validate-json](https://github.com/cesanta/validate-json)

### Haskell

* [aeson-schema](https://github.com/timjb/aeson-schema)
* [hjsonschema](https://github.com/seagreen/hjsonschema)

### Java

* [json-schema-validator](https://github.com/daveclayton/json-schema-validator)
* [everit-org/json-schema](https://github.com/everit-org/json-schema)
* [networknt/json-schema-validator](https://github.com/networknt/json-schema-validator)
* [Justify](https://github.com/leadpony/justify)
* [Snow](https://github.com/ssilverman/snowy-json)
* [jsonschemafriend](https://github.com/jimblackler/jsonschemafriend)

### JavaScript

* [json-schema-benchmark](https://github.com/Muscula/json-schema-benchmark)
* [direct-schema](https://github.com/IreneKnapp/direct-schema)
* [is-my-json-valid](https://github.com/mafintosh/is-my-json-valid)
* [jassi](https://github.com/iclanzan/jassi)
* [JaySchema](https://github.com/natesilva/jayschema)
* [json-schema-valid](https://github.com/ericgj/json-schema-valid)
* [Jsonary](https://github.com/jsonary-js/jsonary)
* [jsonschema](https://github.com/tdegrunt/jsonschema)
* [request-validator](https://github.com/bugventure/request-validator)
* [skeemas](https://github.com/Prestaul/skeemas)
* [tv4](https://github.com/geraintluff/tv4)
* [z-schema](https://github.com/zaggino/z-schema)
* [jsen](https://github.com/bugventure/jsen)
* [ajv](https://github.com/epoberezkin/ajv)
* [djv](https://github.com/korzio/djv)

### Node.js

For node.js developers, the suite is also available as an
[npm](https://www.npmjs.com/package/@json-schema-org/tests) package.

Node-specific support is maintained in a [separate
repository](https://github.com/json-schema-org/json-schema-test-suite-npm)
which also welcomes your contributions!

### .NET

* [Newtonsoft.Json.Schema](https://github.com/JamesNK/Newtonsoft.Json.Schema)
* [Manatee.Json](https://github.com/gregsdennis/Manatee.Json)

### Perl

* [JSON::Schema::Draft201909](https://github.com/karenetheridge/JSON-Schema-Draft201909)
* [JSON::Schema::Tiny](https://github.com/karenetheridge/JSON-Schema-Tiny)
* [Test::JSON::Schema::Acceptance](https://github.com/karenetheridge/Test-JSON-Schema-Acceptance)

### PHP

* [opis/json-schema](https://github.com/opis/json-schema)
* [json-schema](https://github.com/justinrainbow/json-schema)
* [json-guard](https://github.com/thephpleague/json-guard)

### PostgreSQL

* [postgres-json-schema](https://github.com/gavinwahl/postgres-json-schema)
* [is\_jsonb\_valid](https://github.com/furstenheim/is_jsonb_valid)

### Python

* [jsonschema](https://github.com/Julian/jsonschema)
* [fastjsonschema](https://github.com/seznam/python-fastjsonschema)
* [hypothesis-jsonschema](https://github.com/Zac-HD/hypothesis-jsonschema)
* [jschon](https://github.com/marksparkza/jschon)

### Ruby

* [json-schema](https://github.com/hoxworth/json-schema)
* [json\_schemer](https://github.com/davishmcclurg/json_schemer)

### Rust

* [jsonschema](https://github.com/Stranger6667/jsonschema-rs)
* [valico](https://github.com/rustless/valico)

### Swift

* [JSONSchema](https://github.com/kylef/JSONSchema.swift)

If you use it as well, please fork and send a pull request adding yourself to
the list :).

## Contributing

If you see something missing or incorrect, a pull request is most welcome!

There are some sanity checks in place for testing the test suite. You can run
them with `bin/jsonschema_suite check` or `tox`. They will be run automatically
by [GitHub Actions](https://github.com/json-schema-org/JSON-Schema-Test-Suite/actions?query=workflow%3A%22Test+Suite+Sanity+Checking%22)
as well.
