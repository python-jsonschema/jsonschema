=================
Schema Validation
=================


.. currentmodule:: jsonschema


The Basics
----------

The simplest way to validate an instance under a given schema is to use the
:func:`validate` function.

.. autofunction:: validate

    Validate an ``instance`` under the given ``schema``.

        >>> validate([2, 3, 4], {"maxItems" : 2})
        Traceback (most recent call last):
            ...
        ValidationError: [2, 3, 4] is too long

    :func:`validate` will first verify that the provided schema is itself
    valid, since not doing so can lead to less obvious error messages and fail
    in less obvious or consistent ways. If you know you have a valid schema
    already or don't care, you might prefer using the ``validate`` method
    directly on a specific validator (e.g. :meth:`Draft3Validator.validate`).

    ``cls`` is a validator class that will be used to validate the instance.
    By default this is a draft 3 validator.  Any other provided positional and
    keyword arguments will be provided to this class when constructing a
    validator.

    :raises:
        :exc:`ValidationError` if the instance is invalid

        :exc:`SchemaError` if the schema itself is invalid


The Validator Interface
-----------------------

:mod:`jsonschema` defines an (informal) interface that all validators should
adhere to.

.. class:: IValidator(schema, types=(), resolver=None, format_checker=None)

    :argument dict schema: the schema that the validator will validate with. It
                           is assumed to be valid, and providing an invalid
                           schema can lead to undefined behavior. See
                           :meth:`IValidator.check_schema` to validate a schema
                           first.
    :argument types: Override or extend the list of known types when validating
                     the ``type`` property. Should map strings (type names) to
                     class objects that will be checked via ``isinstance``. See
                     :ref:`validating-types` for details.
    :type types: dict or iterable of 2-tuples
    :argument resolver: an object with a ``resolve()`` method that will be used
                        to resolve ``$ref`` properties (JSON references). If
                        unprovided, a :class:`RefResolver` is created and used.
    :argument format_checker: an object with a ``conform()`` method that will
                              be called to check and see if instances conform
                              to each ``format`` property present in the
                              schema. If unprovided, no validation will be done
                              for ``format``. :class:`FormatChecker` is a
                              concrete implementation of an object of this form
                              that can be used for common formats.

    .. attribute:: DEFAULT_TYPES

        The default mapping of JSON types to Python types used when validating
        ``type`` properties in JSON schemas.

    .. attribute:: META_SCHEMA

        An object representing the validator's meta schema (the schema that
        describes valid schemas in the given version).

    .. attribute:: schema

        The schema that was passed in when initializing the validator.


    .. classmethod:: check_schema(schema)

        Validate the given schema against the validator's :attr:`META_SCHEMA`.

        :raises: :exc:`SchemaError` if the schema is invalid

    .. method:: is_type(instance, type)

        Check if the instance is of the given (JSON Schema) type.

        :type type: str
        :rtype: bool
        :raises: :exc:`UnknownType` if ``type`` is not a known type.

        The special type ``"any"`` is valid for any given instance.

    .. method:: is_valid(instance)

        Check if the instance is valid under the current :attr:`schema`.

        :rtype: bool

            >>> schema = {"maxItems" : 2}
            >>> Draft3Validator(schema).is_valid([2, 3, 4])
            False

    .. method:: iter_errors(instance)

        Lazily yield each of the validation errors in the given instance.

        :rtype: an iterable of :exc:`ValidationError`\s

            >>> schema = {
            ...     "type" : "array",
            ...     "items" : {"enum" : [1, 2, 3]},
            ...     "maxItems" : 2,
            ... }
            >>> v = Draft3Validator(schema)
            >>> for error in sorted(v.iter_errors([2, 3, 4]), key=str):
            ...     print(error)
            4 is not one of [1, 2, 3]
            [2, 3, 4] is too long

    .. method:: validate(instance)

        Check if the instance is valid under the current :attr:`schema`.

        :raises: :exc:`ValidationError` if the instance is invalid

            >>> schema = {"maxItems" : 2}
            >>> Draft3Validator(schema).validate([2, 3, 4])
            Traceback (most recent call last):
                ...
            ValidationError: [2, 3, 4] is too long


All of the :ref:`versioned validators <versioned-validators>` that are included
with :mod:`jsonschema` adhere to the interface, and implementors of validators
that extend or complement the ones included should adhere to it as well. For
more information see :ref:`creating-validators`.


.. _validating-types:

Validating With Additional Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Occasionally it can be useful to provide additional or alternate types when
validating the JSON Schema's ``type`` property. Validators allow this by taking
a ``types`` argument on construction that specifies additional types, or which
can be used to specify a different set of Python types to map to a given JSON
type.

For instance, JSON defines a ``number`` type, which can be validated with a
schema such as ``{"type" : "number"}``. By default, this will validate
correctly for Python :class:`int`\s and :class:`float`\s. If you wanted to
additionally validate :class:`decimal.Decimal` objects, you'd use

.. code-block:: python

    Draft3Validator(
        schema={"type" : "number"},
        types={"number" : (int, float, decimal.Decimal)},
    )

The list of default Python types for each JSON type is available on each
validator in the :attr:`IValidator.DEFAULT_TYPES` attribute. Note that you
need to specify all types to match if you override one of the existing JSON
types, so you may want to access the set of default types to add it to the
ones being appended.


.. _versioned-validators:

Versioned Validators
--------------------

:mod:`jsonschema` ships with validators for various versions of the JSON Schema
specification. For details on the methods and attributes that each validator
provides see the :class:`IValidator` interface, which each validator
implements.

.. autoclass:: Draft3Validator


Validating Formats
------------------

JSON Schema defines the ``format`` property which can be used to check if
primitive types (``str``\s, ``number``\s, ``bool``\s) conform to well-defined
formats. By default, no validation is enforced, but optionally, validation can
be enabled by hooking in a format-checking object into an :class:`IValidator`.

.. doctest::

    >>> validate("tomorrow", {"format" : "date"})
    >>> validate(
    ...     "tomorrow", {"format" : "date"}, format_checker=FormatChecker(),
    ... )
    Traceback (most recent call last):
        ...
    ValidationError: "tomorrow" is not a "date"

.. autoclass:: FormatChecker
    :members:
    :exclude-members: cls_checks

    .. attribute:: checkers

        A mapping of currently known formats to functions that validate them.
        New checkers can be added and removed either per-instance or globally
        for all checkers using the :meth:`FormatChecker.checks` or
        :meth:`FormatChecker.cls_checks` decorators respectively.

    .. method:: cls_checks(format)

        Register a decorated function as *globally* validating a new format.

        Any instance created after this function is called will pick up the
        supplied checker.

        :argument str format: the format that the decorated function will check



There are a number of default checkers that :class:`FormatChecker`\s know how
to validate. Their names can be viewed by inspecting the
:attr:`FormatChecker.checkers` attribute.

.. testsetup::

    from pprint import pprint

.. testcode::

    pprint(sorted(FormatChecker.checkers))

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

    [...'color',
     ...'date',
     ...'date-time',
     ...'email',
     ...'host-name',
     ...'ip-address',
     ...'ipv6',
     ...'regex',
     ...'time',
     ...'uri']


The actual functions that do the validation are also exposed, in case there is
any use for them. They are listed below, along with any limitations they come
with.


.. autofunction:: is_date

    Check if the instance is a date in ``YYYY-MM-DD`` format.

        >>> is_date("1970-12-31")
        True
        >>> is_date("12/31/1970")
        False
        >>> is_date("0000-13-32")
        False

.. autofunction:: is_time

    Check if the instance is a time in ``hh:mm:ss`` format.

        >>> is_time("23:59:59")
        True
        >>> is_time("11:59:59 PM")
        False
        >>> is_time("59:60:61")
        False

.. autofunction:: is_regex

    Check if the instance is a well-formed regular expression.

        >>> is_regex("^(bob)?cat$")
        True
        >>> is_ipv6("^(bob?cat$")
        False

.. autofunction:: is_uri

    Check if the instance is a valid URI.

    Also supports relative URIs.

        >>> is_uri("ftp://joe.bloggs@www2.example.com:8080/pub/os/")
        True
        >>> is_uri("http://www2.example.com:8000/pub/#os?user=joe.bloggs")
        True
        >>> is_uri(r"\\\\WINDOWS\My Files")
        False
        >>> is_uri("#/properties/foo")
        True

.. autofunction:: is_email

    Check if the instance is a valid e-mail address.

    Checking is based on `RFC 2822`_

        >>> is_email("joe.bloggs@example.com")
        True
        >>> is_email("joe.bloggs")
        False

    .. _RFC 2822: http://tools.ietf.org/html/rfc2822

.. autofunction:: is_host_name

    Check if the instance is a valid host name.

        >>> is_host_name("www.example.com")
        True
        >>> is_host_name("my laptop")
        False
        >>> is_host_name(
        ...     "a.vvvvvvvvvvvvvvvvveeeeeeeeeeeeeeeeerrrrrrrrrrrrrrrrryyyyyyyy"
        ...     "yyyyyyyyy.long.host.name"
        ... )
        False

    .. note:: Does not perform a DNS lookup.

        >>> is_host_name("www.example.doesnotexist")
        True

.. autofunction:: is_ip_address

    Check if the instance is a valid IP address.

        >>> is_ip_address("192.168.0.1")
        True
        >>> is_ip_address("::1")
        False
        >>> is_ip_address("256.256.256.256")
        False

On OSes with the ``socket.inet_pton`` function, an additional checker for
``ipv6`` will be enabled:

.. function:: is_ipv6(instance)

    Check if the instance is a valid IPv6 address.

        >>> is_ipv6("::1")
        True
        >>> is_ipv6("192.168.0.1")
        False
        >>> is_ipv6("1:1:1:1:1:1:1:1:1")
        False


If the isodate_ library is present, a date-time checker will also be present.

.. function:: is_date_time(instance)

    Check if the instance is in ISO 8601 ``YYYY-MM-DDThh:mm:ssZ`` format.

        >>> is_date_time("1970-01-01T00:00:00.0Z")
        True
        >>> is_date_time("0000-58-59T60:61:62")
        False


Additionally, if the webcolors_ library is present, some checkers related to
CSS will be enabled:

.. function:: is_css21_color(instance)

    Check if the instance is a valid CSS 2.1 color name or code.

        >>> is_css21_color("fuchsia")
        True
        >>> is_css21_color("pink")
        False
        >>> is_css_color_code("#CC8899")
        True

.. function:: is_css3_color(instance)

    Check if the instance is a valid CSS 3 color name or code.

        >>> is_css3_color("pink")
        True
        >>> is_css3_color("puce")
        False
        >>> is_css_color_code("#CC8899")
        True

.. _isodate: http://pypi.python.org/pypi/isodate/
.. _webcolors: http://pypi.python.org/pypi/webcolors/
