JSON Schema Test Suite [![Build Status](https://travis-ci.org/json-schema/JSON-Schema-Test-Suite.png?branch=develop)](https://travis-ci.org/json-schema/JSON-Schema-Test-Suite)
======================

This repository contains a set of JSON objects that implementors of JSON Schema
validation libraries can use to test their validators.

It is meant to be language agnostic and should require only a JSON parser.

The conversion of the JSON objects into tests within your test framework of
choice is still the job of the validator implementor.

Structure of a Test
-------------------

If you're going to use this suite, you need to know how tests are laid out. The
tests are contained in the `tests` directory at the root of this repository.

Inside that directory is a subdirectory for each draft or version of the
schema. We'll use `draft3` as an example.

If you look inside the draft directory, there are a number of `.json` files,
which logically group a set of test cases together. Often the grouping is by
property under test, but not always, especially within optional test files
(discussed below).

Inside each `.json` file is a single array containing objects. It's easiest to
illustrate the structure of these with an example:

```json
    {
        "description": "the description of the test case",
        "schema": {"the schema that should" : "be validated against"},
        "tests": [
            {
                "description": "a specific test of a valid instance",
                "data": "the instance",
                "valid": true
            },
            {
                "description": "another specific test this time, invalid",
                "data": 15,
                "valid": false
            }
        ]
    }
```

So a description, a schema, and some tests, where tests is an array containing
one or more objects with descriptions, data, and a boolean indicating whether
they should be valid or invalid.

Coverage
--------

Currently, draft 3 should have essentially full coverage for the core schema.

The beginnings of draft 4 are underway.

Who Uses the Test Suite
-----------------------

This suite is being used by:

  * [json-schema-validator (Java)](https://github.com/fge/json-schema-validator)
  * [jsonschema (python)](https://github.com/Julian/jsonschema)
  * [aeson-schema (haskell)](https://github.com/timjb/aeson-schema)
  * [direct-schema (javascript)](https://github.com/IreneKnapp/direct-schema)
  * [jsonschema (javascript)](https://github.com/tdegrunt/jsonschema)
  * [JaySchema (javascript)](https://github.com/natesilva/jayschema)

If you use it as well, please fork and send a pull request adding yourself to
the list :).

Contributing
------------

If you see something missing or incorrect, a pull request is most welcome!
