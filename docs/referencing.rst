=========================
JSON (Schema) Referencing
=========================

The JSON Schema :kw:`$ref` and :kw:`$dynamicRef` keywords allow schema authors to combine multiple schemas (or subschemas) together for reuse or deduplication.

The `referencing <referencing:index>` library was written in order to provide a simple, well-behaved and well-tested implementation of this kind of reference resolution [1]_.
It has its `own documentation which is worth reviewing <referencing:intro>`, but this page serves as an introduction which is tailored specifically to JSON Schema, and even more specifically to how to configure `referencing <referencing:index>` for use with `Validator` objects in order to customize the behavior of the :kw:`$ref` keyword and friends in your schemas.

Configuring `jsonschema` for custom referencing behavior is essentially a two step process:

    * Create a `referencing.Registry` object that behaves the way you wish

    * Pass the `referencing.Registry` to your `Validator` when instantiating it

The examples below essentially follow these two steps.

.. [1] One that in fact is independent of this `jsonschema` library itself, and may some day be used by other tools or implementations.


Introduction to the `referencing <referencing:index>` API
---------------------------------------------------------

There are 3 main objects to be aware of in the `referencing` API:

    * `referencing.Registry`, which represents a specific immutable set of JSON Schemas (either in-memory or retrievable)
    * `referencing.Specification`, which represents a specific *version* of the JSON Schema specification, which can have differing referencing behavior.
      JSON Schema-specific specifications live in the `referencing.jsonschema` module and are named like `referencing.jsonschema.DRAFT202012`.
    * `referencing.Resource`, which represents a specific JSON Schema (often a Python `dict`) *along* with a specific `referencing.Specification` it is to be interpreted under.

As a concrete example, the simple schema ``{"type": "integer"}`` may be interpreted as a schema under either Draft 2020-12 or Draft 4 of the JSON Schema specification (amongst others); in draft 2020-12, the float ``2.0`` must be considered an integer, whereas in draft 4, it potentially is not.
If you mean the former (i.e. to associate this schema with draft 2020-12), you'd use ``referencing.Resource(contents={"type": "integer"}, specification=referencing.jsonschema.DRAFT202012)``, whereas for the latter you'd use `referencing.jsonschema.DRAFT4`.

.. seealso:: the JSON Schema :kw:`$schema` keyword

    Which should generally be used to remove all ambiguity and identify *internally* to the schema what version it is written for.

A schema may be identified via one or more URIs, either because they contain an :kw:`$id` keyword (in suitable versions of the JSON Schema specification) which indicates their canonical URI, or simply because you wish to externally associate a URI with the schema, regardless of whether it contains an ``$id`` keyword.
You could add the aforementioned simple schema to a `referencing.Registry` by creating an empty registry and then identifying it via some URI:

.. testcode::

    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    schema = Resource(contents={"type": "integer"}, specification=DRAFT202012)
    registry = Registry().with_resource(uri="http://example.com/my/schema", resource=schema)
    print(registry)

.. testoutput::

   <Registry (1 uncrawled resource)>

.. note::

    `referencing.Registry` is an entirely immutable object.
    All of its methods which add schemas (resources) to itself return *new* registry objects containing the added schemas.

You could also confirm your schema is in the registry if you'd like, via `referencing.Registry.contents`, which will show you the contents of a resource at a given URI:

.. testcode::

   print(registry.contents("http://example.com/my/schema"))

.. testoutput::

   {'type': 'integer'}

For further details, see the `referencing documentation <referencing:intro>`.

Common Scenarios
----------------

.. _in-memory-schemas:

Making Additional In-Memory Schemas Available
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most common scenario one is likely to encounter is the desire to include a small number of additional in-memory schemas, making them available for use during validation.

For instance, imagine the below schema for non-negative integers:

.. code:: json

    {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "type": "integer",
      "minimum": 0
    }

We may wish to have other schemas we write be able to make use of this schema, and refer to it as ``http://example.com/nonneg-int-schema`` and/or as ``urn:nonneg-integer-schema``.

To do so we make use of APIs from the referencing library to create a `referencing.Registry` which maps the URIs above to this schema:

.. code:: python

    from referencing import Registry, Resource
    schema = Resource.from_contents(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "integer",
            "minimum": 0,
        },
    )
    registry = Registry().with_resources(
        [
            ("http://example.com/nonneg-int-schema", schema),
            ("urn:nonneg-integer-schema", schema),
        ],
    )

What's above is likely mostly self-explanatory, other than the presence of the `referencing.Resource.from_contents` function.
Its purpose is to convert a piece of "opaque" JSON (or really a Python `dict` containing deserialized JSON) into an object which indicates what *version* of JSON Schema the schema is meant to be interpreted under.
Calling it will inspect a :kw:`$schema` keyword present in the given schema and use that to associate the JSON with an appropriate `specification <referencing.Specification>`.
If your schemas do not contain ``$schema`` dialect identifiers, and you intend for them to be interpreted always under a specific dialect -- say Draft 2020-12 of JSON Schema -- you may instead use e.g.:

.. code:: python

    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT2020212
    schema = DRAFT202012.create_resource({"type": "integer", "minimum": 0})
    registry = Registry().with_resources(
        [
            ("http://example.com/nonneg-int-schema", schema),
            ("urn:nonneg-integer-schema", schema),
        ],
    )

which has the same functional effect.

You can now pass this registry to your `Validator`, which allows a schema passed to it to make use of the aforementioned URIs to refer to our non-negative integer schema.
Here for instance is an example which validates that instances are JSON objects with non-negative integral values:

.. code:: python

    from jsonschema import Draft202012Validator
    validator = Draft202012Validator(
        {
            "type": "object",
            "additionalProperties": {"$ref": "urn:nonneg-integer-schema"},
        },
        registry=registry,  # the critical argument, our registry from above
    )
    validator.validate({"foo": 37})
    validator.validate({"foo": -37})  # Uh oh!

.. _ref-filesystem:

Resolving References from the File System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Another common request from schema authors is to be able to map URIs to the file system, perhaps while developing a set of schemas in different local files.
The referencing library supports doing so dynamically by configuring a callable which can be used to retrieve any schema which is *not* already pre-loaded in the manner described `above <in-memory-schemas>`.

Here we resolve any schema beginning with ``http://localhost`` to a directory ``/tmp/schemas`` on the local filesystem (note of course that this will not work if run directly unless you have populated that directory with some schemas):

.. code:: python

    from pathlib import Path
    import json

    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource

    SCHEMAS = Path("/tmp/schemas")

    def retrieve_from_filesystem(uri: str):
        if not uri.startswith("http://localhost/"):
            raise NoSuchResource(ref=uri)
        path = SCHEMAS / Path(uri.removeprefix("http://localhost/"))
        contents = json.loads(path.read_text())
        return Resource.from_contents(contents)

    registry = Registry(retrieve=retrieve_from_filesystem)

Such a registry can then be used with `Validator` objects in the same way shown above, and any such references to URIs which are not already in-memory will be retrieved from the configured directory.

We can mix the two examples above if we wish for some in-memory schemas to be available in addition to the filesystem schemas, e.g.:

.. code:: python

    from referencing.jsonschema import DRAFT7
    registry = Registry(retrieve=retrieve_from_filesystem).with_resource(
        "urn:non-empty-array", DRAFT7.create_resource({"type": "array", "minItems": 1}),
    )

where we've made use of the similar `referencing.Registry.with_resource` function to add a single additional resource.

Resolving References to Schemas Written in YAML
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generalizing slightly, the retrieval function provided need not even assume that it is retrieving JSON.
As long as you deserialize what you have retrieved into Python objects, you may equally be retrieving references to YAML documents or any other format.

Here for instance we retrieve YAML documents in a way similar to the `above <ref-filesystem>` using PyYAML:

.. code:: python

    from pathlib import Path
    import yaml

    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource

    SCHEMAS = Path("/tmp/yaml-schemas")

    def retrieve_yaml(uri: str):
        if not uri.startswith("http://localhost/"):
            raise NoSuchResource(ref=uri)
        path = SCHEMAS / Path(uri.removeprefix("http://localhost/"))
        contents = yaml.safe_load(path.read_text())
        return Resource.from_contents(contents)

    registry = Registry(retrieve=retrieve_yaml)

.. note::

    Not all YAML fits within the JSON data model.

    JSON Schema is defined specifically for JSON, and has well-defined behavior strictly for Python objects which could have possibly existed as JSON.

    If you stick to the subset of YAML for which this is the case then you shouldn't have issue, but if you pass schemas (or instances) around whose structure could never have possibly existed as JSON (e.g. a mapping whose keys are not strings), all bets are off.

One could similarly imagine a retrieval function which switches on whether to call ``yaml.safe_load`` or ``json.loads`` by file extension (or some more reliable mechanism) and thereby support retrieving references of various different file formats.

.. _http:

Automatically Retrieving Resources Over HTTP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the general case, the JSON Schema specifications tend to `discourage <https://json-schema.org/draft/2020-12/json-schema-core.html#name-loading-a-referenced-schema>`_ implementations (like this one) from automatically retrieving references over the network, or even assuming such a thing is feasible (as schemas may be identified by URIs which are strictly identifiers, and not necessarily downloadable from the URI even when such a thing is sensical).

However, if you as a schema author are in a situation where you indeed do wish to do so for convenience (and understand the implications of doing so), you may do so by making use of the ``retrieve`` argument to `referencing.Registry`.

Here is how one would configure a registry to automatically retrieve schemas from the `JSON Schema Store <https://www.schemastore.org>`_ on the fly using the `httpx <https://www.python-httpx.org/>`_:

.. code:: python

    from referencing import Registry, Resource
    import httpx

    def retrieve_via_httpx(uri: str):
        response = httpx.get(uri)
        return Resource.from_contents(response.json())

    registry = Registry(retrieve=retrieve_via_httpx)

Given such a registry, we can now, for instance, validate instances against schemas from the schema store by passing the ``registry`` we configured to our `Validator` as in previous examples:

.. code:: python

    from jsonschema import Draft202012Validator
    Draft202012Validator(
        {"$ref": "https://json.schemastore.org/pyproject.json"},
        registry=registry,
    ).validate({"project": {"name": 12}})

which should in this case indicate the example data is invalid:

.. code:: python

    Traceback (most recent call last):
    File "example.py", line 14, in <module>
        ).validate({"project": {"name": 12}})
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "jsonschema/validators.py", line 345, in validate
        raise error
    jsonschema.exceptions.ValidationError: 12 is not of type 'string'

    Failed validating 'type' in schema['properties']['project']['properties']['name']:
        {'pattern': '^([a-zA-Z\\d]|[a-zA-Z\\d][\\w.-]*[a-zA-Z\\d])$',
        'title': 'Project name',
        'type': 'string'}

    On instance['project']['name']:
        12

Retrieving resources from a SQLite database or some other network-accessible resource should be more or less similar, replacing the HTTP client with one for your database of course.

.. warning::

    Be sure you understand the security implications of the reference resolution you configure.
    And if you accept untrusted schemas, doubly sure!

    You wouldn't want a user causing your machine to go off and retrieve giant files off the network by passing it a ``$ref`` to some huge blob, or exploiting similar vulnerabilities in your setup.


Migrating From ``RefResolver``
------------------------------

Older versions of `jsonschema` used a different object -- `_RefResolver` -- for reference resolution, which you a schema author may already be configuring for your own use.

`_RefResolver` is now fully deprecated and replaced by the use of `referencing.Registry` as shown in examples above.

If you are not already constructing your own `_RefResolver`, this change should be transparent to you (or even recognizably improved, as the point of the migration was to improve the quality of the referencing implementation and enable some new functionality).

.. table:: Rough equivalence between `_RefResolver` and `referencing.Registry` APIs
   :widths: auto

   ===========================================================  =====================================================================================================================
                             Old API                                                                                      New API
   ===========================================================  =====================================================================================================================
   ``RefResolver.from_schema({"$id": "urn:example:foo", ...}``  ``Registry().with_resource(uri="urn:example:foo", resource=Resource.from_contents({"$id": "urn:example:foo", ...}))``
   Overriding ``RefResolver.resolve_from_url``                  Passing a callable to `referencing.Registry`\ 's ``retrieve`` argument
   ``DraftNValidator(..., resolver=_RefResolver(...))``  ``     DraftNValidator(..., registry=Registry().with_resources(...))``
   ===========================================================  =====================================================================================================================


Here are some more specifics on how to migrate to the newer APIs:

The ``store`` argument
~~~~~~~~~~~~~~~~~~~~~~

`_RefResolver`\ 's ``store`` argument was essentially the equivalent of `referencing.Registry`\ 's in-memory schema storage.

If you currently pass a set of schemas via e.g.:

.. code:: python

    from jsonschema import Draft202012Validator, RefResolver
    resolver = RefResolver.from_schema(
        schema={"title": "my schema"},
        store={"http://example.com": {"type": "integer"}},
    )
    validator = Draft202012Validator(
        {"$ref": "http://example.com"},
        resolver=resolver,
    )
    validator.validate("foo")

you should be able to simply move to something like:

.. code:: python

    from referencing import Registry
    from referencing.jsonschema import DRAFT202012

    from jsonschema import Draft202012Validator

    registry = Registry().with_resource(
        "http://example.com",
        DRAFT202012.create_resource({"type": "integer"}),
    )
    validator = Draft202012Validator(
        {"$ref": "http://example.com"},
        registry=registry,
    )
    validator.validate("foo")

Handlers
~~~~~~~~

The ``handlers`` functionality from `_RefResolver` was a way to support additional HTTP schemes for schema retrieval.

Here you should move to a custom ``retrieve`` function which does whatever you'd like.
E.g. in pseudocode:

.. code:: python

    from urllib.parse import urlsplit

    def retrieve(uri: str):
        parsed = urlsplit(uri)
        if parsed.scheme == "file":
            ...
        elif parsed.scheme == "custom":
            ...

    registry = Registry(retrieve=retrieve)


Other Key Functional Differences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Whilst `_RefResolver` *did* automatically retrieve remote references (against the recommendation of the spec, and in a way which therefore could lead to questionable security concerns when combined with untrusted schemas), `referencing.Registry` does *not* do so.
If you rely on this behavior, you should follow the `above example of retrieving resources over HTTP <http>`.
