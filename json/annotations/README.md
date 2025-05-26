# Annotations Tests Suite

The Annotations Test Suite tests which annotations should appear (or not appear)
on which values of an instance. These tests are agnostic of any output format.

## Supported Dialects

Although the annotation terminology of didn't appear in the spec until 2019-09,
the concept is compatible with every version of JSON Schema. Test Cases in this
Test Suite are designed to be compatible with as many releases of JSON Schema as
possible. They do not include `$schema` or `$id`/`id` keywords so
implementations can run the same Test Suite for each dialect they support.

Since this Test Suite can be used for a variety of dialects, there are a couple
of options that can be used by Test Runners to filter out Test Cases that don't
apply to the dialect under test.

## Test Case Components

### description

A short description of what behavior the Test Case is covering.

### compatibility

The `compatibility` option allows you to set which dialects the Test Case is
compatible with. Test Runners can use this value to filter out Test Cases that
don't apply the to dialect currently under test. The terminology for annotations
didn't appear in the spec until 2019-09, but the concept is compatible with
older releases as well. When setting `compatibility`, test authors should take
into account dialects before 2019-09 for implementations that chose to support
annotations for older dialects.

Dialects are indicated by the number corresponding to their release. Date-based
releases use just the year. If this option isn't present, it means the Test Case
is compatible with any dialect.

If this option is present with a number, the number indicates the minimum
release the Test Case is compatible with. This example indicates that the Test
Case is compatible with draft-07 and up.

**Example**: `"compatibility": "7"`

You can use a `<=` operator to indicate that the Test Case is compatible with
releases less then or equal to the given release. This example indicates that
the Test Case is compatible with 2019-09 and under.

**Example**: `"compatibility": "<=2019"`

You can use comma-separated values to indicate multiple constraints if needed.
This example indicates that the Test Case is compatible with releases between
draft-06 and 2019-09.

**Example**: `"compatibility": "6,<=2019"`

For convenience, you can use the `=` operator to indicate a Test Case is only
compatible with a single release. This example indicates that the Test Case is
compatible only with 2020-12.

**Example**: `"compatibility": "=2020"`

### schema

The schema that will serve as the subject for the tests. Whenever possible, this
schema shouldn't include `$schema` or `id`/`$id` because Test Cases should be
designed to work with as many releases as possible.

### externalSchemas

This allows you to define additional schemas that `schema` makes references to.
The value is an object where the keys are retrieval URIs and values are schemas.
Most external schemas aren't self identifying (using `id`/`$id`) and rely on the
retrieval URI for identification. This is done to increase the number of
dialects that the test is compatible with.  Because `id` changed to `$id` in
draft-06, if you use `$id`, the test becomes incompatible with draft-03/4 and in
most cases, that's not necessary.

### tests

A collection of Tests to run to verify the Test Case.

## Test Components

### instance

The JSON instance to be annotated.

### assertions

A collection of assertions that must be true for the test to pass.

## Assertions Components

### location

The instance location.

### keyword

The annotating keyword.

### expected

A collection of `keyword` annotations expected on the instance at `location`.
`expected` is an object where the keys are schema locations and the values are
the annotation that schema location contributed for the given `keyword`.

There can be more than one expected annotation because multiple schema locations
could contribute annotations for a single keyword.

An empty object is an assertion that the annotation must not appear at the
`location` for the `keyword`.

As a convention for this Test Suite, the `expected` array should be sorted such
that the most recently encountered value for an annotation given top-down
evaluation of the schema comes before previously encountered values.
