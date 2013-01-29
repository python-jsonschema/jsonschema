"""
An implementation of JSON Schema for Python

The main functionality is provided by the validator classes for each of the
supported JSON Schema versions.

Most commonly, :func:`validate` is the quickest way to simply validate a given
instance under a schema, and will create a validator for you.

"""

from __future__ import division, unicode_literals

import collections
import json
import itertools
import operator
import re
import sys


__version__ = "1.0.0-dev"

PY3 = sys.version_info[0] >= 3

if PY3:
    from urllib import parse as urlparse
    from urllib.parse import unquote
    from urllib.request import urlopen
    basestring = unicode = str
    iteritems = operator.methodcaller("items")
else:
    from itertools import izip as zip
    from urllib import unquote
    from urllib2 import urlopen
    import urlparse
    iteritems = operator.methodcaller("iteritems")


FLOAT_TOLERANCE = 10 ** -15
validators = {}


def validates(version):
    """
    Register the decorated validator for a ``version`` of the specification.

    Registered validators and their meta schemas will be considered when
    parsing ``$schema`` properties' URIs.

    :argument str version: an identifier to use as the version's name
    :returns: a class decorator to decorate the validator with the version

    """

    def _validates(cls):
        validators[version] = cls
        return cls
    return _validates


class UnknownType(Exception):
    """
    An attempt was made to check if an instance was of an unknown type.

    """


class RefResolutionError(Exception):
    """
    A JSON reference failed to resolve.

    """


class SchemaError(Exception):
    """
    The provided schema is malformed.

    The same attributes are present as for :exc:`ValidationError`\s.

    """

    def __init__(self, message, validator=None, path=()):
        super(SchemaError, self).__init__(message, validator, path)
        self.message = message
        self.path = list(path)
        self.validator = validator

    def __str__(self):
        return self.message


class ValidationError(Exception):
    """
    The instance didn't properly validate under the provided schema.

    Relevant attributes are:
        * ``message`` : a human readable message explaining the error
        * ``path`` : a list containing the path to the offending element (or []
                     if the error happened globally) in *reverse* order (i.e.
                     deepest index first).

    """

    def __init__(self, message, validator=None, path=()):
        # Any validator that recurses (e.g. properties and items) must append
        # to the ValidationError's path to properly maintain where in the
        # instance the error occurred
        super(ValidationError, self).__init__(message, validator, path)
        self.message = message
        self.path = list(path)
        self.validator = validator

    def __str__(self):
        return self.message


@validates("draft3")
class Draft3Validator(object):
    """
    A validator for JSON Schema draft 3.

    """

    DEFAULT_TYPES = {
        "array" : list, "boolean" : bool, "integer" : int, "null" : type(None),
        "number" : (int, float), "object" : dict, "string" : basestring,
    }

    def __init__(self, schema, types=(), resolver=None, format_checker=None):
        self._types = dict(self.DEFAULT_TYPES)
        self._types.update(types)

        if resolver is None:
            resolver = RefResolver.from_schema(schema)

        if format_checker is None:
            format_checker = FormatChecker()

        self.resolver = resolver
        self.format_checker = format_checker
        self.schema = schema

    def is_type(self, instance, type):
        if type == "any":
            return True
        elif type not in self._types:
            raise UnknownType(type)
        type = self._types[type]

        # bool inherits from int, so ensure bools aren't reported as integers
        if isinstance(instance, bool):
            type = _flatten(type)
            if int in type and bool not in type:
                return False
        return isinstance(instance, type)

    def is_valid(self, instance, _schema=None):
        error = next(self.iter_errors(instance, _schema), None)
        return error is None

    @classmethod
    def check_schema(cls, schema):
        for error in cls(cls.META_SCHEMA).iter_errors(schema):
            raise SchemaError(
                error.message, validator=error.validator, path=error.path,
            )

    def iter_errors(self, instance, _schema=None):
        if _schema is None:
            _schema = self.schema

        for k, v in iteritems(_schema):
            validator = getattr(self, "validate_%s" % (k.lstrip("$"),), None)

            if validator is None:
                continue

            errors = validator(v, instance, _schema) or ()
            for error in errors:
                # set the validator if it wasn't already set by the called fn
                if error.validator is None:
                    error.validator = k
                yield error

    def validate(self, *args, **kwargs):
        for error in self.iter_errors(*args, **kwargs):
            raise error

    def validate_type(self, types, instance, schema):
        types = _list(types)

        for type in types:
            if self.is_type(type, "object"):
                if self.is_valid(instance, type):
                    return
            elif self.is_type(type, "string"):
                if self.is_type(instance, type):
                    return
        else:
            yield ValidationError(_types_msg(instance, types))

    def validate_properties(self, properties, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, subschema in iteritems(properties):
            if property in instance:
                for error in self.iter_errors(instance[property], subschema):
                    error.path.append(property)
                    yield error
            elif subschema.get("required", False):
                yield ValidationError(
                    "%r is a required property" % (property,),
                    validator="required",
                    path=[property],
                )

    def validate_patternProperties(self, patternProperties, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for pattern, subschema in iteritems(patternProperties):
            for k, v in iteritems(instance):
                if re.match(pattern, k):
                    for error in self.iter_errors(v, subschema):
                        yield error

    def validate_additionalProperties(self, aP, instance, schema):
        if not self.is_type(instance, "object"):
            return

        extras = set(_find_additional_properties(instance, schema))

        if self.is_type(aP, "object"):
            for extra in extras:
                for error in self.iter_errors(instance[extra], aP):
                    yield error
        elif not aP and extras:
            error = "Additional properties are not allowed (%s %s unexpected)"
            yield ValidationError(error % _extras_msg(extras))

    def validate_dependencies(self, dependencies, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, dependency in iteritems(dependencies):
            if property not in instance:
                continue

            if self.is_type(dependency, "object"):
                for error in self.iter_errors(instance, dependency):
                    yield error
            else:
                dependencies = _list(dependency)
                for dependency in dependencies:
                    if dependency not in instance:
                        yield ValidationError(
                            "%r is a dependency of %r" % (dependency, property)
                        )

    def validate_items(self, items, instance, schema):
        if not self.is_type(instance, "array"):
            return

        if self.is_type(items, "object"):
            for index, item in enumerate(instance):
                for error in self.iter_errors(item, items):
                    error.path.append(index)
                    yield error
        else:
            for (index, item), subschema in zip(enumerate(instance), items):
                for error in self.iter_errors(item, subschema):
                    error.path.append(index)
                    yield error

    def validate_additionalItems(self, aI, instance, schema):
        if (
            not self.is_type(instance, "array") or
            not self.is_type(schema.get("items"), "array")
        ):
            return

        if self.is_type(aI, "object"):
            for item in instance[len(schema):]:
                for error in self.iter_errors(item, aI):
                    yield error
        elif not aI and len(instance) > len(schema.get("items", [])):
            error = "Additional items are not allowed (%s %s unexpected)"
            yield ValidationError(
                error % _extras_msg(instance[len(schema.get("items", [])):])
            )

    def validate_minimum(self, minimum, instance, schema):
        if not self.is_type(instance, "number"):
            return

        instance = float(instance)
        if schema.get("exclusiveMinimum", False):
            failed = instance <= minimum
            cmp = "less than or equal to"
        else:
            failed = instance < minimum
            cmp = "less than"

        if failed:
            yield ValidationError(
                "%r is %s the minimum of %r" % (instance, cmp, minimum)
            )

    def validate_maximum(self, maximum, instance, schema):
        if not self.is_type(instance, "number"):
            return

        instance = float(instance)
        if schema.get("exclusiveMaximum", False):
            failed = instance >= maximum
            cmp = "greater than or equal to"
        else:
            failed = instance > maximum
            cmp = "greater than"

        if failed:
            yield ValidationError(
                "%r is %s the maximum of %r" % (instance, cmp, maximum)
            )

    def validate_minItems(self, mI, instance, schema):
        if self.is_type(instance, "array") and len(instance) < mI:
            yield ValidationError("%r is too short" % (instance,))

    def validate_maxItems(self, mI, instance, schema):
        if self.is_type(instance, "array") and len(instance) > mI:
            yield ValidationError("%r is too long" % (instance,))

    def validate_uniqueItems(self, uI, instance, schema):
        if uI and self.is_type(instance, "array") and not _uniq(instance):
            yield ValidationError("%r has non-unique elements" % instance)

    def validate_pattern(self, patrn, instance, schema):
        if self.is_type(instance, "string") and not re.match(patrn, instance):
            yield ValidationError("%r does not match %r" % (instance, patrn))

    def validate_format(self, format, instance, schema):
        if (self.is_type(instance, "string")
            and self.format_checker.conforms(instance, format) is False
            # Note: conforms() returns None if it doesn't know how to validate
            # the given format.
        ):
            yield ValidationError(
                '%r does not match "%r" format' % (instance, format)
            )

    def validate_minLength(self, mL, instance, schema):
        if self.is_type(instance, "string") and len(instance) < mL:
            yield ValidationError("%r is too short" % (instance,))

    def validate_maxLength(self, mL, instance, schema):
        if self.is_type(instance, "string") and len(instance) > mL:
            yield ValidationError("%r is too long" % (instance,))

    def validate_enum(self, enums, instance, schema):
        if instance not in enums:
            yield ValidationError("%r is not one of %r" % (instance, enums))

    def validate_divisibleBy(self, dB, instance, schema):
        if not self.is_type(instance, "number"):
            return

        if isinstance(dB, float):
            mod = instance % dB
            failed = (mod > FLOAT_TOLERANCE) and (dB - mod) > FLOAT_TOLERANCE
        else:
            failed = instance % dB

        if failed:
            yield ValidationError("%r is not divisible by %r" % (instance, dB))

    def validate_disallow(self, disallow, instance, schema):
        for disallowed in _list(disallow):
            if self.is_valid(instance, {"type" : [disallowed]}):
                yield ValidationError(
                    "%r is disallowed for %r" % (disallowed, instance)
                )

    def validate_extends(self, extends, instance, schema):
        if self.is_type(extends, "object"):
            extends = [extends]
        for subschema in extends:
            for error in self.iter_errors(instance, subschema):
                yield error

    def validate_ref(self, ref, instance, schema):
        resolved = self.resolver.resolve(ref)
        for error in self.iter_errors(instance, resolved):
            yield error


Draft3Validator.META_SCHEMA = {
    "$schema" : "http://json-schema.org/draft-03/schema#",
    "id" : "http://json-schema.org/draft-03/schema#",
    "type" : "object",

    "properties" : {
        "type" : {
            "type" : ["string", "array"],
            "items" : {"type" : ["string", {"$ref" : "#"}]},
            "uniqueItems" : True,
            "default" : "any"
        },
        "properties" : {
            "type" : "object",
            "additionalProperties" : {"$ref" : "#", "type": "object"},
            "default" : {}
        },
        "patternProperties" : {
            "type" : "object",
            "additionalProperties" : {"$ref" : "#"},
            "default" : {}
        },
        "additionalProperties" : {
            "type" : [{"$ref" : "#"}, "boolean"], "default" : {}
        },
        "items" : {
            "type" : [{"$ref" : "#"}, "array"],
            "items" : {"$ref" : "#"},
            "default" : {}
        },
        "additionalItems" : {
            "type" : [{"$ref" : "#"}, "boolean"], "default" : {}
        },
        "required" : {"type" : "boolean", "default" : False},
        "dependencies" : {
            "type" : ["string", "array", "object"],
            "additionalProperties" : {
                "type" : ["string", "array", {"$ref" : "#"}],
                "items" : {"type" : "string"}
            },
            "default" : {}
        },
        "minimum" : {"type" : "number"},
        "maximum" : {"type" : "number"},
        "exclusiveMinimum" : {"type" : "boolean", "default" : False},
        "exclusiveMaximum" : {"type" : "boolean", "default" : False},
        "minItems" : {"type" : "integer", "minimum" : 0, "default" : 0},
        "maxItems" : {"type" : "integer", "minimum" : 0},
        "uniqueItems" : {"type" : "boolean", "default" : False},
        "pattern" : {"type" : "string", "format" : "regex"},
        "minLength" : {"type" : "integer", "minimum" : 0, "default" : 0},
        "maxLength" : {"type" : "integer"},
        "enum" : {"type" : "array", "minItems" : 1, "uniqueItems" : True},
        "default" : {"type" : "any"},
        "title" : {"type" : "string"},
        "description" : {"type" : "string"},
        "format" : {"type" : "string"},
        "maxDecimal" : {"type" : "number", "minimum" : 0},
        "divisibleBy" : {
            "type" : "number",
            "minimum" : 0,
            "exclusiveMinimum" : True,
            "default" : 1
        },
        "disallow" : {
            "type" : ["string", "array"],
            "items" : {"type" : ["string", {"$ref" : "#"}]},
            "uniqueItems" : True
        },
        "extends" : {
            "type" : [{"$ref" : "#"}, "array"],
            "items" : {"$ref" : "#"},
            "default" : {}
        },
        "id" : {"type" : "string", "format" : "uri"},
        "$ref" : {"type" : "string", "format" : "uri"},
        "$schema" : {"type" : "string", "format" : "uri"},
    },
    "dependencies" : {
        "exclusiveMinimum" : "minimum", "exclusiveMaximum" : "maximum"
    },
}


class FormatChecker(object):
    """
    Adds validation of "format" properties, which is optional for JSON schema
    validators.

    Subclass, and implement "is_<format_name>()" methods to yield
    ValidationError on failure.
    """
    
    def conforms(self, instance, format):
        method_name = 'is_' + re.sub('[^A-Za-z0-9]', '_', format)
        method = getattr(self, method_name, None)
        if method:
            return method(instance)
        return None


class DateTimeFormatChecker(FormatChecker):
    """
    Validates strings in "date", "time", "date-time" and "utc-milisec" format
    according to the JSON Schema Draft 3 specification.
    """

    def is_date_time(self, instance):
        """
        If instance matches a date and time in "YYYY-MM-DDThh:mm:ssZ" format,
        returns True, otherwise False.

        >>> is_date_time('1970-01-01T00:00:00.0')
        True
        >>> is_date_time('1970-01-01 00:00:00 GMT')
        False

        .. NOTE: Does not check that month, day, hour, minute and second
                 components have values in the correct ranges.

                 >>> is_date_time('0000-58-59T60:61:62')
                 True

        """
        pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$'
        return bool(re.match(pattern, instance))

    def is_date(self, instance):
        """
        If instance matches a date in "YYYY-MM-DD" format, returns True,
        otherwise False.

        >>> is_date('1970-12-31')
        True
        >>> is_date('12/31/1970')
        False

        .. NOTE: Does not check that month and day components have values in
                 the correct ranges.

                 >>> is_date('0000-13-32')
                 True

        """
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, instance))

    def is_time(self, instance):
        """
        If instance matches a time in "hh:mm:ss" format, returns True,
        otherwise False.

        >>> is_time('23:59:59')
        True
        >>> is_time('11:59:59 PM')
        False

        .. NOTE: Does not check that hour, minute and second components have
                 values in the correct ranges.

                 >>> is_time('59:60:61')
                 True

        """
        pattern = r'^\d{2}:\d{2}:\d{2}$'
        return bool(re.match(pattern, instance))


class InternetFormatChecker(DateTimeFormatChecker):
    """
    Checks Internet-related formats. Extends DateTimeFormatChecker
    """

    def is_uri(self, instance):
        """
        If instance matches a URI, returns True, otherwise False.

        >>> check = InternetFormatChecker()
        >>> check.is_uri('ftp://joe.bloggs@www2.example.com:8080/pub/os/')
        True
        >>> check.is_uri(r'\\WINDOWS\My Files')
        False

        """
        # URI regex from http://snipplr.com/view/6889/
        pattern = (r"^([A-Za-z0-9+.-]+):(?://(?:((?:[A-Za-z0-9-._~!$&'()*+,;=:"
                   r"]|%[0-9A-Fa-f]{2})*)@)?((?:[A-Za-z0-9-._~!$&'()*+,;=]|%[0"
                   r"-9A-Fa-f]{2})*)(?::(\d*))?(/(?:[A-Za-z0-9-._~!$&'()*+,;=:"
                   r"@/]|%[0-9A-Fa-f]{2})*)?|(/?(?:[A-Za-z0-9-._~!$&'()*+,;=:@"
                   r"]|%[0-9A-Fa-f]{2})+(?:[A-Za-z0-9-._~!$&'()*+,;=:@/]|%[0-9"
                   r"A-Fa-f]{2})*)?)(?:\?((?:[A-Za-z0-9-._~!$&'()*+,;=:/?@]|%["
                   r"0-9A-Fa-f]{2})*))?(?:#((?:[A-Za-z0-9-._~!$&'()*+,;=:/?@]|"
                   r"%[0-9A-Fa-f]{2})*))?$")
        return bool(re.match(pattern, instance))

    def is_email(self, instance):
        """
        If instance matches an e-mail address, returns True, otherwise False.

        Check is based on RFC 2822: http://tools.ietf.org/html/rfc2822

        >>> check = InternetFormatChecker()
        >>> check.is_email('joe.bloggs@example.com')
        True
        >>> check.is_email('joe.bloggs')
        False

        """
        pattern = (r"^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_"
                   r"`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b"
                   r"\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z"
                   r"0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0"
                   r"-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                   r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9"
                   r"]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x"
                   r"01-\x09\x0b\x0c\x0e-\x7f])+)\])$")
        return bool(re.match(pattern, instance))

    def is_ip_address(self, instance):
        """
        If instance matches an IP address, returns True, otherwise False.

        >>> check = InternetFormatChecker()
        >>> check.is_ip_address('192.168.0.1')
        True
        >>> check.is_ip_address('::1')
        False

        .. NOTE: Does not check that address components have values in the
                 correct ranges.

                 >>> check.is_ip_address('256.256.256.256')
                 True

        """
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(pattern, instance))

    def is_ipv6(self, instance):
        """
        If instance matches an IPv6 address, returns True, otherwise False.

        >>> check = InternetFormatChecker()
        >>> check.is_ipv6('::1')
        True
        >>> check.is_ipv6('192.168.0.1')
        False

        .. NOTE: Does not check that components have values in the correct
                 ranges, or the length of the address.

                 >>> check.is_ipv6('12345:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1')
                 True

        """
        pattern = r'^[:A-Fa-f0-9]{3,}$'
        return bool(re.match(pattern, instance))

    def is_host_name(self, instance):
        """
        If instance matches a host name, returns True, otherwise False.

        >>> check = InternetFormatChecker()
        >>> check.is_host_name('www.example.com')
        True
        >>> check.is_host_name('my laptop')
        False

        .. NOTE: Does not perform a DNS lookup. Allows host name components
                 with more than 63 characters.

                 >>> check.is_host_name('www.example.doesnotexist')
                 True
                 >>> check.is_host_name('a.vvvvvvvvvvvvvvvvveeeeeeeeeeeeeeeeerr'
                 ...              'rrrrrrrrrrrrrrryyyyyyyyyyyyyyyyy.long.name')
                 True

        """
        pattern = '^[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}$'
        return bool(re.match(pattern, instance))


class RefResolver(object):
    """
    Resolve JSON References.

    :argument str base_uri: URI of the referring document
    :argument referrer: the actual referring document
    :argument dict store: a mapping from URIs to documents to cache

    """

    def __init__(self, base_uri, referrer, store=()):
        self.base_uri = base_uri
        self.referrer = referrer
        self.store = dict(store, **_meta_schemas())

    @classmethod
    def from_schema(cls, schema, *args, **kwargs):
        """
        Construct a resolver from a JSON schema object.

        :argument schema schema: the referring schema
        :rtype: :class:`RefResolver`

        """

        return cls(schema.get("id", ""), schema, *args, **kwargs)

    def resolve(self, ref):
        """
        Resolve a JSON ``ref``.

        :argument str ref: reference to resolve
        :returns: the referrant document

        """

        base_uri = self.base_uri
        uri, fragment = urlparse.urldefrag(urlparse.urljoin(base_uri, ref))

        if uri in self.store:
            document = self.store[uri]
        elif not uri or uri == self.base_uri:
            document = self.referrer
        else:
            document = self.resolve_remote(uri)

        return self.resolve_fragment(document, fragment.lstrip("/"))

    def resolve_fragment(self, document, fragment):
        """
        Resolve a ``fragment`` within the referenced ``document``.

        :argument document: the referrant document
        :argument str fragment: a URI fragment to resolve within it

        """

        parts = unquote(fragment).split("/") if fragment else []

        for part in parts:
            part = part.replace("~1", "/").replace("~0", "~")

            if part not in document:
                raise RefResolutionError(
                    "Unresolvable JSON pointer: %r" % fragment
                )

            document = document[part]

        return document

    def resolve_remote(self, uri):
        """
        Resolve a remote ``uri``.

        Does not check the store first.

        :argument str uri: the URI to resolve
        :returns: the retrieved document

        """

        return json.load(urlopen(uri))


class ErrorTree(object):
    """
    ErrorTrees make it easier to check which validations failed.

    """

    def __init__(self, errors=()):
        self.errors = {}
        self._contents = collections.defaultdict(self.__class__)

        for error in errors:
            container = self
            for element in reversed(error.path):
                container = container[element]
            container.errors[error.validator] = error

    def __contains__(self, k):
        return k in self._contents

    def __getitem__(self, k):
        """
        Retrieve the child tree with key ``k``.

        """

        return self._contents[k]

    def __setitem__(self, k, v):
        self._contents[k] = v

    def __iter__(self):
        return iter(self._contents)

    def __len__(self):
        return self.total_errors

    def __repr__(self):
        return "<%s (%s total errors)>" % (self.__class__.__name__, len(self))

    @property
    def total_errors(self):
        """
        The total number of errors in the entire tree, including children.

        """

        child_errors = sum(len(tree) for _, tree in iteritems(self._contents))
        return len(self.errors) + child_errors


def _meta_schemas():
    """
    Collect the urls and meta schemas from each known validator.

    """

    meta_schemas = (v.META_SCHEMA for v in validators.values())
    return dict((urlparse.urldefrag(m["id"])[0], m) for m in meta_schemas)


def _find_additional_properties(instance, schema):
    """
    Return the set of additional properties for the given ``instance``.

    Weeds out properties that should have been validated by ``properties`` and
    / or ``patternProperties``.

    Assumes ``instance`` is dict-like already.

    """

    properties = schema.get("properties", {})
    patterns = "|".join(schema.get("patternProperties", {}))
    for property in instance:
        if property not in properties:
            if patterns and re.search(patterns, property):
                continue
            yield property


def _extras_msg(extras):
    """
    Create an error message for extra items or properties.

    """

    if len(extras) == 1:
        verb = "was"
    else:
        verb = "were"
    return ", ".join(repr(extra) for extra in extras), verb


def _types_msg(instance, types):
    """
    Create an error message for a failure to match the given types.

    If the ``instance`` is an object and contains a ``name`` property, it will
    be considered to be a description of that object and used as its type.

    Otherwise the message is simply the reprs of the given ``types``.

    """

    reprs = []
    for type in types:
        try:
            reprs.append(repr(type["name"]))
        except Exception:
            reprs.append(repr(type))
    return "%r is not of type %s" % (instance, ", ".join(reprs))


def _flatten(suitable_for_isinstance):
    """
    isinstance() can accept a bunch of really annoying different types:
        * a single type
        * a tuple of types
        * an arbitrary nested tree of tuples

    Return a flattened tuple of the given argument.

    """

    types = set()

    if not isinstance(suitable_for_isinstance, tuple):
        suitable_for_isinstance = (suitable_for_isinstance,)
    for thing in suitable_for_isinstance:
        if isinstance(thing, tuple):
            types.update(_flatten(thing))
        else:
            types.add(thing)
    return tuple(types)


def _list(thing):
    """
    Wrap ``thing`` in a list if it's a single str.

    Otherwise, return it unchanged.

    """

    if isinstance(thing, basestring):
        return [thing]
    return thing


def _delist(thing):
    """
    Unwrap ``thing`` to a single element if its a single str in a list.

    Otherwise, return it unchanged.

    """

    if (
        isinstance(thing, list) and
        len(thing) == 1
        and isinstance(thing[0], basestring)
    ):
        return thing[0]
    return thing


def _unbool(element, true=object(), false=object()):
    """
    A hack to make True and 1 and False and 0 unique for _uniq.

    """

    if element is True:
        return true
    elif element is False:
        return false
    return element


def _uniq(container):
    """
    Check if all of a container's elements are unique.

    Successively tries first to rely that the elements are hashable, then
    falls back on them being sortable, and finally falls back on brute
    force.

    """

    try:
        return len(set(_unbool(i) for i in container)) == len(container)
    except TypeError:
        try:
            sort = sorted(_unbool(i) for i in container)
            sliced = itertools.islice(sort, 1, None)
            for i, j in zip(sort, sliced):
                if i == j:
                    return False
        except (NotImplementedError, TypeError):
            seen = []
            for e in container:
                e = _unbool(e)
                if e in seen:
                    return False
                seen.append(e)
    return True


def validate(instance, schema, cls=Draft3Validator, *args, **kwargs):
    """
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

    """


    cls.check_schema(schema)
    cls(schema, *args, **kwargs).validate(instance)
