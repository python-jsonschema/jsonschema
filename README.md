JSON Schema Test Suite
======================

This repository contains a set of JSON objects that implementors of JSON Schema
validation libraries can use to test their validators.

It is meant to be language agnostic and should require only a JSON parser.

The conversion of the JSON objects into your test framework of choice (say,
an `xUnit`) is still the job of the validator implementor.

Structure of a Test
-------------------

If you're going to use this suite, you need to know how tests are laid out. The
tests are contained in the `tests` directory at the root of this repository.

Inside that directory is a subdirectory for each draft or version of the
schema. We'll use `draft3` as an example.

If you look inside the draft directory, there are a number of `.json` files,
which logically group a set of test cases together.

Inside each `.json` file is a single array containing objects. It's easiest to
illustrate the structure of these with an example:

    {
        "description": "the description of the test case",
        "schema": "the schema that should be validated against",
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
            },
        ]
    }

So a description, a schema, and some tests, where tests is an array containing
one or more objects with descriptions, data, and a boolean indicating whether
they should be valid or invalid.

Coverage
--------

The coverage of this suite is actively growing. The first order of business is
to have a full-coverage draft 3 test suite.

Ultimately, when it's done, the idea is to attempt to have it included on [the
JSON Schema website](http://www.json-schema.org).

Contributing
------------

I need help! If you'd like to contribute, please fork this repository. I'd love
to have your pull requests sent over.

Right now, the way I'm compiling the tests is by porting over a test suite
that I'd written for a Python validator. The tests (in a messy format) can be
found [here](https://github.com/Julian/jsonschema/blob/master/tests.py#L100).

There are also other JSON Schema test suites for various other validators, and
it would certainly be nice to merge all of them as well. In particular, [this
validator](https://github.com/fge/json-schema-validator/tree/master/src/test/resources/keyword)
contains a set of tests already written in JSON which will be useful.
