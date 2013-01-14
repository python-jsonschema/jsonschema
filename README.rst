==========
jsonschema
==========

``jsonschema`` is an implementation of `JSON Schema <http://json-schema.org>`_
for Python (supporting 2.6+ including Python 3).

.. code-block:: python

    >>> from jsonschema import validate

    >>> # A sample schema, like what we'd get from json.load()
    >>> schema = {
    ...     "type" : "object",
    ...     "properties" : {
    ...         "price" : {"type" : "number"},
    ...         "name" : {"type" : "string"},
    ...     },
    ... }

    >>> # If no exception is raised by validate(), the instance is valid.
    >>> validate({"name" : "Eggs", "price" : 34.99}, schema)

    >>> validate(
    ...     {"name" : "Eggs", "price" : "Invalid"}, schema
    ... )                                   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: 'Invalid' is not of type 'number'


Features
--------

* `Full support <https://python-jsonschema.readthedocs.org/en/latest/#jsonschema.Draft3Validator>`_
  for `Draft 3 <http://tools.ietf.org/html/draft-zyp-json-schema-03>`_ of the
  schema

* `Lazy validation <https://python-jsonschema.readthedocs.org/en/latest/validate.html#jsonschema.IValidator.iter_errors>`_
  that can iteratively report *all* validation errors.

* Small and extensible

* `Programmatic querying <https://python-jsonschema.readthedocs.org/en/latest/errors.html#module-jsonschema>`_
  of which properties or items failed validation.


Release Notes
-------------

``v0.8.0`` introduces full support for JSON references via the ``RefResolver``
object. It also removes all of the deprecated code from ``v0.7``.

Other notable fixes are a fix for improper support of ``uniqueItems`` for
``True`` and ``False`` (#34) and ``any`` for unknown types (#47).

Notably, there now exists some documentation (woo hoo!). It can be found at:

    http://python-jsonschema.readthedocs.org

There are still a few incomplete sections, but it's mostly there. Patches
welcome for weak points.


Running the Test Suite
----------------------

``jsonschema`` uses the wonderful `Tox <http://tox.readthedocs.org>`_ for its
test suite. (It really is wonderful, if for some reason you haven't heard of
it, you really should use it for your projects).

Assuming you have ``tox`` installed (perhaps via ``pip install tox`` or your
package manager), just run ``tox`` in the directory of your source checkout to
run ``jsonschema``'s test suite on all of the versions of Python ``jsonschema``
supports. Note that you'll need to have all of those versions installed in
order to run the tests on each of them, otherwise ``tox`` will skip (and fail)
the tests on that version.


Contributing
------------

I'm Julian Berman.

``jsonschema`` is on `GitHub <http://github.com/Julian/jsonschema>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.
