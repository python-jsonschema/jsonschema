# JSON Schema Test Suite

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](https://github.com/json-schema-org/.github/blob/main/CODE_OF_CONDUCT.md)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Financial Contributors on Open Collective](https://opencollective.com/json-schema/all/badge.svg?label=financial+contributors)](https://opencollective.com/json-schema)

[![DOI](https://zenodo.org/badge/5952934.svg)](https://zenodo.org/badge/latestdoi/5952934)
[![Build Status](https://github.com/json-schema-org/JSON-Schema-Test-Suite/workflows/Test%20Suite%20Sanity%20Checking/badge.svg)](https://github.com/json-schema-org/JSON-Schema-Test-Suite/actions?query=workflow%3A%22Test+Suite+Sanity+Checking%22)

This repository contains a set of JSON objects that implementers of JSON Schema validation libraries can use to test their validators.

It is meant to be language agnostic and should require only a JSON parser.
The conversion of the JSON objects into tests within a specific language and test framework of choice is left to be done by the validator implementer.

The recommended workflow of this test suite is to clone the `main` branch of this repository as a `git submodule` or `git subtree`. The `main` branch is always stable.

## Coverage

All JSON Schema specification releases should be well covered by this suite, including drafts 2020-12, 2019-09, 07, 06, 04 and 03.
Drafts 04 and 03 are considered "frozen" in that less effort is put in to backport new tests to these versions.

Additional coverage is always welcome, particularly for bugs encountered in real-world implementations.
If you see anything missing or incorrect, please feel free to [file an issue](https://github.com/json-schema-org/JSON-Schema-Test-Suite/issues) or [submit a PR](https://github.com/json-schema-org/JSON-Schema-Test-Suite).

@gregsdennis has also started a separate [test suite](https://github.com/gregsdennis/json-schema-vocab-test-suites) that is modelled after this suite to cover third-party vocabularies.

## Introduction to the Test Suite Structure

The tests in this suite are contained in the `tests` directory at the root of this repository.
Inside that directory is a subdirectory for each released version of the specification.

The structure and contents of each file in these directories is described below.

In addition to the version-specific subdirectories, two additional directories are present:

1. `draft-next/`: containing tests for the next version of the specification whilst it is in development
2. `latest/`: a symbolic link which points to the directory which is the most recent release (which may be useful for implementations providing specific entry points for validating against the latest version of the specification)

Inside each version directory there are a number of `.json` files each containing a collection of related tests.
Often the grouping is by property under test, but not always.
In addition to the `.json` files, each version directory contains one or more special subdirectories whose purpose is [described below](#subdirectories-within-each-draft), and which contain additional `.json` files.

Each `.json` file consists of a single JSON array of test cases.

### Terminology

For clarity, we first define this document's usage of some testing terminology:

| term            | definition                                                                                                                                                        |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **test suite**  | the entirety of the contents of this repository, containing tests for multiple different releases of the JSON Schema specification                                |
| **test case**   | a single schema, along with a description and an array of *test*s                                                                                                 |
| **test**        | within a *test case*, a single test example, containing a description, instance and a boolean indicating whether the instance is valid under the test case schema |
| **test runner** | a program, external to this repository and authored by a user of this suite, which is executing each of the tests in the suite                                    |

An example illustrating this structure is immediately below, and a JSON Schema containing a formal definition of the contents of test cases can be found [alongside this README](./test-schema.json).

### Sample Test Case

Here is a single *test case*, containing one or more tests:

```json
{
    "description": "The test case description",
    "schema": { "type": "string" },
    "tests": [
        {
            "description": "a test with a valid instance",
            "data": "a string",
            "valid": true
        },
        {
            "description": "a test with an invalid instance",
            "data": 15,
            "valid": false
        }
    ]
}
```

### Subdirectories Within Each Draft

There is currently only one additional subdirectory that may exist within each draft test directory.

This is:

1. `optional/`: Contains tests that are considered optional.

Note, the `optional/` subdirectory today conflates many reasons why a test may be optional -- it may be because tests within a particular file are indeed not required by the specification but still potentially useful to an implementer, or it may be because tests within it only apply to programming languages with particular functionality (in
which case they are not truly optional in such a language).
In the future this directory structure will be made richer to reflect these differences more clearly.

## Using the Suite to Test a Validator Implementation

The test suite structure was described [above](#introduction-to-the-test-suite-structure).

If you are authoring a new validator implementation, or adding support for an additional version of the specification, this section describes:

1. How to implement a test runner which passes tests to your validator
2. Assumptions the suite makes about how the test runner will configure your validator
3. Invariants the test suite claims to hold for its tests

### How to Implement a Test Runner

Presented here is a possible implementation of a test runner.
The precise steps described do not need to be followed exactly, but the results of your own procedure should produce the same effects.

To test a specific version:

* For 2019-09 and later published drafts, implementations that are able to detect the draft of each schema via `$schema` SHOULD be configured to do so
* For draft-07 and earlier, draft-next, and implementations unable to detect via `$schema`, implementations MUST be configured to expect the draft matching the test directory name
* Load any remote references [described below](additional-assumptions) and configure your implementation to retrieve them via their URIs
* Walk the filesystem tree for that version's subdirectory and for each `.json` file found:

    * if the file is located in the root of the version directory:

        * for each test case present in the file:

            * load the schema from the `"schema"` property
            * load (or log) the test case description from the `"description"` property for debugging or outputting
            * for each test in the `"tests"` property:

                * load the instance to be tested from the `"data"` property
                * load (or log) the individual test description from the `"description"` property for debugging or outputting

                * use the schema loaded above to validate whether the instance is considered valid under your implementation

                * if the result from your implementation matches the value found in the `"valid"` property, your implementation correctly implements the specific example
                * if the result does not match, or your implementation errors or crashes, your implementation does not correctly implement the specific example

    * otherwise it is located in a special subdirectory as described above.
      Follow the additional assumptions and restrictions for the containing subdirectory, then run the test case as above.

If your implementation supports multiple versions, run the above procedure for each version supported, configuring your implementation as appropriate to call each version individually.

### Additional Assumptions

1. The suite, notably in its `refRemote.json` file in each draft, expects a number of remote references to be configured.
   These are JSON documents, identified by URI, which are used by the suite to test the behavior of the `$ref` keyword (and related keywords).
   Depending on your implementation, you may configure how to "register" these *either*:

    * by directly retrieving them off the filesystem from the `remotes/` directory, in which case you should load each schema with a retrieval URI of `http://localhost:1234` followed by the relative path from the remotes directory -- e.g. a `$ref` to `http://localhost:1234/foo/bar/baz.json` is expected to resolve to the contents of the file at `remotes/foo/bar/baz.json`

    * or alternatively, by executing `bin/jsonschema_suite remotes` using the executable in the `bin/` directory, which will output a JSON object containing all of the remotes combined, e.g.:

    ```

    $  bin/jsonschema_suite remotes
    ```
    ```json
    {
        "http://localhost:1234/baseUriChange/folderInteger.json": {
            "type": "integer"
        },
        "http://localhost:1234/baseUriChangeFolder/folderInteger.json": {
            "type": "integer"
        }
    }
    ```

2. Test cases found within [special subdirectories](#subdirectories-within-each-draft) may require additional configuration to run.
   In particular, tests within the `optional/format` subdirectory may require implementations to change the way they treat the `"format"`keyword (particularly on older drafts which did not have a notion of vocabularies).

### Invariants & Guarantees

The test suite guarantees a number of things about tests it defines.
Any deviation from the below is generally considered a bug.
If you suspect one, please [file an issue](https://github.com/json-schema-org/JSON-Schema-Test-Suite/issues/new):

1. All files containing test cases are valid JSON.
2. The contents of the `"schema"` property in a test case are always valid
   JSON Schemas under the corresponding specification.

   The rationale behind this is that we are testing instances in a test's `"data"` element, and not the schema itself.
   A number of tests *do* test the validity of a schema itself, but do so by representing the schema as an instance inside a test, with the associated meta-schema in the `"schema"` property (via the `"$ref"` keyword):

   ```json
   {
       "description": "Test the \"type\" schema keyword",
       "schema": {
           "$ref": "https://json-schema.org/draft/2019-09/schema"
        },
       "tests": [
           {
               "description": "Valid: string",
               "data": {
                   "type": "string"
               },
               "valid": true
           },
           {
               "description": "Invalid: null",
               "data": {
                   "type": null
               },
               "valid": false
           }
       ]
   }
   ```
   See below for some [known limitations](#known-limitations).

## Known Limitations

This suite expresses its assertions about the behavior of an implementation *within* JSON Schema itself.
Each test is the application of a schema to a particular instance.
This means that the suite of tests can test against any behavior a schema can describe, and conversely cannot test against any behavior which a schema is incapable of representing, even if the behavior is mandated by the specification.

For example, a schema can require that a string is a _URI-reference_ and even that it matches a certain pattern, but even though the specification contains [recommendations about URIs being normalized](https://json-schema.org/draft/2020-12/json-schema-core.html#name-the-id-keyword), a JSON schema cannot today represent this assertion within the core vocabularies of the specifications, so no test covers this behavior.

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
* [Valijson](https://github.com/tristanpenman/valijson)

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

For node.js developers, the suite is also available as an [npm](https://www.npmjs.com/package/@json-schema-org/tests) package.

Node-specific support is maintained in a [separate repository](https://github.com/json-schema-org/json-schema-test-suite-npm) which also welcomes your contributions!

### .NET

* [JsonSchema.Net](https://github.com/gregsdennis/json-everything)
* [Newtonsoft.Json.Schema](https://github.com/JamesNK/Newtonsoft.Json.Schema)

### Perl

* [Test::JSON::Schema::Acceptance](https://github.com/karenetheridge/Test-JSON-Schema-Acceptance) (a wrapper of this test suite)
* [JSON::Schema::Modern](https://github.com/karenetheridge/JSON-Schema-Modern)
* [JSON::Schema::Tiny](https://github.com/karenetheridge/JSON-Schema-Tiny)

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
* [python-experimental, OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator/blob/master/docs/generators/python-experimental.md)

### Ruby

* [json-schema](https://github.com/hoxworth/json-schema)
* [json\_schemer](https://github.com/davishmcclurg/json_schemer)

### Rust

* [jsonschema](https://github.com/Stranger6667/jsonschema-rs)
* [valico](https://github.com/rustless/valico)

### Scala

* [typed-json](https://github.com/frawa/typed-json)

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

This repository is maintained by the JSON Schema organization, and will be governed by the JSON Schema steering committee (once it exists).
