from __future__ import division

import contextlib
import json
import numbers

try:
    import requests
except ImportError:
    requests = None

from jsonschema import _utils, _validators
from jsonschema.compat import (
    Sequence, urljoin, urlsplit, urldefrag, unquote, urlopen,
    str_types, int_types, iteritems,
)
from jsonschema.exceptions import ErrorTree  # Backwards compatibility  # noqa
from jsonschema.exceptions import RefResolutionError, SchemaError, UnknownType


_unset = _utils.Unset()

validators = {}
meta_schemas = _utils.URIDict()


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
        if u"id" in cls.META_SCHEMA:
            meta_schemas[cls.META_SCHEMA[u"id"]] = cls
        return cls
    return _validates


def create(meta_schema, validators=(), version=None, default_types=None):  # noqa
    if default_types is None:
        default_types = {
            u"array" : list, u"boolean" : bool, u"integer" : int_types,
            u"null" : type(None), u"number" : numbers.Number, u"object" : dict,
            u"string" : str_types,
        }

    class Validator(object):
        VALIDATORS = dict(validators)
        META_SCHEMA = dict(meta_schema)
        DEFAULT_TYPES = dict(default_types)

        def __init__(
            self, schema, types=(), resolver=None, format_checker=None,
        ):
            self._types = dict(self.DEFAULT_TYPES)
            self._types.update(types)

            if resolver is None:
                resolver = RefResolver.from_schema(schema)

            self.resolver = resolver
            self.format_checker = format_checker
            self.schema = schema

        @classmethod
        def check_schema(cls, schema):
            for error in cls(cls.META_SCHEMA).iter_errors(schema):
                raise SchemaError.create_from(error)

        def iter_errors(self, instance, _schema=None):
            if _schema is None:
                _schema = self.schema

            with self.resolver.in_scope(_schema.get(u"id", u"")):
                ref = _schema.get(u"$ref")
                if ref is not None:
                    validators = [(u"$ref", ref)]
                else:
                    validators = iteritems(_schema)

                for k, v in validators:
                    validator = self.VALIDATORS.get(k)
                    if validator is None:
                        continue

                    errors = validator(self, v, instance, _schema) or ()
                    for error in errors:
                        # set details if not already set by the called fn
                        error._set(
                            validator=k,
                            validator_value=v,
                            instance=instance,
                            schema=_schema,
                        )
                        if k != u"$ref":
                            error.schema_path.appendleft(k)
                        yield error

        def descend(self, instance, schema, path=None, schema_path=None):
            for error in self.iter_errors(instance, schema):
                if path is not None:
                    error.path.appendleft(path)
                if schema_path is not None:
                    error.schema_path.appendleft(schema_path)
                yield error

        def validate(self, *args, **kwargs):
            for error in self.iter_errors(*args, **kwargs):
                raise error

        def is_type(self, instance, type):
            if type not in self._types:
                raise UnknownType(type, instance, self.schema)
            pytypes = self._types[type]

            # bool inherits from int, so ensure bools aren't reported as ints
            if isinstance(instance, bool):
                pytypes = _utils.flatten(pytypes)
                is_number = any(
                    issubclass(pytype, numbers.Number) for pytype in pytypes
                )
                if is_number and bool not in pytypes:
                    return False
            return isinstance(instance, pytypes)

        def is_valid(self, instance, _schema=None):
            error = next(self.iter_errors(instance, _schema), None)
            return error is None

    if version is not None:
        Validator = validates(version)(Validator)
        Validator.__name__ = version.title().replace(" ", "") + "Validator"

    return Validator


def extend(validator, validators, version=None):
    all_validators = dict(validator.VALIDATORS)
    all_validators.update(validators)
    return create(
        meta_schema=validator.META_SCHEMA,
        validators=all_validators,
        version=version,
        default_types=validator.DEFAULT_TYPES,
    )


Draft3Validator = create(
    meta_schema=_utils.load_schema("draft3"),
    validators={
        u"$ref" : _validators.ref,
        u"additionalItems" : _validators.additionalItems,
        u"additionalProperties" : _validators.additionalProperties,
        u"dependencies" : _validators.dependencies,
        u"disallow" : _validators.disallow_draft3,
        u"divisibleBy" : _validators.multipleOf,
        u"enum" : _validators.enum,
        u"extends" : _validators.extends_draft3,
        u"format" : _validators.format,
        u"items" : _validators.items,
        u"maxItems" : _validators.maxItems,
        u"maxLength" : _validators.maxLength,
        u"maximum" : _validators.maximum,
        u"minItems" : _validators.minItems,
        u"minLength" : _validators.minLength,
        u"minimum" : _validators.minimum,
        u"multipleOf" : _validators.multipleOf,
        u"pattern" : _validators.pattern,
        u"patternProperties" : _validators.patternProperties,
        u"properties" : _validators.properties_draft3,
        u"type" : _validators.type_draft3,
        u"uniqueItems" : _validators.uniqueItems,
    },
    version="draft3",
)

Draft4Validator = create(
    meta_schema=_utils.load_schema("draft4"),
    validators={
        u"$ref" : _validators.ref,
        u"additionalItems" : _validators.additionalItems,
        u"additionalProperties" : _validators.additionalProperties,
        u"allOf" : _validators.allOf_draft4,
        u"anyOf" : _validators.anyOf_draft4,
        u"dependencies" : _validators.dependencies,
        u"enum" : _validators.enum,
        u"format" : _validators.format,
        u"items" : _validators.items,
        u"maxItems" : _validators.maxItems,
        u"maxLength" : _validators.maxLength,
        u"maxProperties" : _validators.maxProperties_draft4,
        u"maximum" : _validators.maximum,
        u"minItems" : _validators.minItems,
        u"minLength" : _validators.minLength,
        u"minProperties" : _validators.minProperties_draft4,
        u"minimum" : _validators.minimum,
        u"multipleOf" : _validators.multipleOf,
        u"not" : _validators.not_draft4,
        u"oneOf" : _validators.oneOf_draft4,
        u"pattern" : _validators.pattern,
        u"patternProperties" : _validators.patternProperties,
        u"properties" : _validators.properties_draft4,
        u"required" : _validators.required_draft4,
        u"type" : _validators.type_draft4,
        u"uniqueItems" : _validators.uniqueItems,
    },
    version="draft4",
)


class RefResolver(object):
    """
    Resolve JSON References.

    :argument str base_uri: URI of the referring document
    :argument referrer: the actual referring document
    :argument dict store: a mapping from URIs to documents to cache
    :argument bool cache_remote: whether remote refs should be cached after
        first resolution
    :argument dict handlers: a mapping from URI schemes to functions that
        should be used to retrieve them

    """

    def __init__(
        self, base_uri, referrer, store=(), cache_remote=True, handlers=(),
    ):
        self.base_uri = base_uri
        self.resolution_scope = base_uri
        # This attribute is not used, it is for backwards compatibility
        self.referrer = referrer
        self.cache_remote = cache_remote
        self.handlers = dict(handlers)

        self.store = _utils.URIDict(
            (id, validator.META_SCHEMA)
            for id, validator in iteritems(meta_schemas)
        )
        self.store.update(store)
        self.store[base_uri] = referrer

    @classmethod
    def from_schema(cls, schema, *args, **kwargs):
        """
        Construct a resolver from a JSON schema object.

        :argument schema schema: the referring schema
        :rtype: :class:`RefResolver`

        """

        return cls(schema.get(u"id", u""), schema, *args, **kwargs)

    @contextlib.contextmanager
    def in_scope(self, scope):
        old_scope = self.resolution_scope
        self.resolution_scope = urljoin(old_scope, scope)
        try:
            yield
        finally:
            self.resolution_scope = old_scope

    @contextlib.contextmanager
    def resolving(self, ref):
        """
        Context manager which resolves a JSON ``ref`` and enters the
        resolution scope of this ref.

        :argument str ref: reference to resolve

        """

        if ref == '#':
            yield self.store[self.base_uri]
        else:
            full_uri = urljoin(self.resolution_scope, ref)
            uri, fragment = urldefrag(full_uri)
            if not uri:
                uri = self.base_uri

            if uri in self.store:
                document = self.store[uri]
            else:
                try:
                    document = self.resolve_remote(uri)
                except Exception as exc:
                    raise RefResolutionError(exc)

            old_base_uri, self.base_uri = self.base_uri, uri
            try:
                with self.in_scope(uri):
                    yield self.resolve_fragment(document, fragment)
            finally:
                self.base_uri = old_base_uri

    def resolve_fragment(self, document, fragment):
        """
        Resolve a ``fragment`` within the referenced ``document``.

        :argument document: the referrant document
        :argument str fragment: a URI fragment to resolve within it

        """

        fragment = fragment.lstrip(u"/")
        parts = unquote(fragment).split(u"/") if fragment else []

        for part in parts:
            part = part.replace(u"~1", u"/").replace(u"~0", u"~")

            if isinstance(document, Sequence):
                # Array indexes should be turned into integers
                try:
                    part = int(part)
                except ValueError:
                    pass
            try:
                document = document[part]
            except (TypeError, LookupError):
                raise RefResolutionError(
                    "Unresolvable JSON pointer: %r" % fragment
                )

        return document

    def resolve_remote(self, uri):
        """
        Resolve a remote ``uri``.

        Does not check the store first, but stores the retrieved document in
        the store if :attr:`RefResolver.cache_remote` is True.

        .. note::

            If the requests_ library is present, ``jsonschema`` will use it to
            request the remote ``uri``, so that the correct encoding is
            detected and used.

            If it isn't, or if the scheme of the ``uri`` is not ``http`` or
            ``https``, UTF-8 is assumed.

        :argument str uri: the URI to resolve
        :returns: the retrieved document

        .. _requests: http://pypi.python.org/pypi/requests/

        """

        scheme = urlsplit(uri).scheme

        if scheme in self.handlers:
            result = self.handlers[scheme](uri)
        elif (
            scheme in [u"http", u"https"] and
            requests and
            getattr(requests.Response, "json", None) is not None
        ):
            # Requests has support for detecting the correct encoding of
            # json over http
            if callable(requests.Response.json):
                result = requests.get(uri).json()
            else:
                result = requests.get(uri).json
        else:
            # Otherwise, pass off to urllib and assume utf-8
            result = json.loads(urlopen(uri).read().decode("utf-8"))

        if self.cache_remote:
            self.store[uri] = result
        return result


def validator_for(schema, default=_unset):
    if default is _unset:
        default = Draft4Validator
    return meta_schemas.get(schema.get(u"$schema", u""), default)


def validate(instance, schema, cls=None, *args, **kwargs):
    """
    Validate an instance under the given schema.

        >>> validate([2, 3, 4], {"maxItems" : 2})
        Traceback (most recent call last):
            ...
        ValidationError: [2, 3, 4] is too long

    :func:`validate` will first verify that the provided schema is itself
    valid, since not doing so can lead to less obvious error messages and fail
    in less obvious or consistent ways. If you know you have a valid schema
    already or don't care, you might prefer using the
    :meth:`~IValidator.validate` method directly on a specific validator
    (e.g. :meth:`Draft4Validator.validate`).


    :argument instance: the instance to validate
    :argument schema: the schema to validate with
    :argument cls: an :class:`IValidator` class that will be used to validate
                   the instance.

    If the ``cls`` argument is not provided, two things will happen in
    accordance with the specification. First, if the schema has a
    :validator:`$schema` property containing a known meta-schema [#]_ then the
    proper validator will be used.  The specification recommends that all
    schemas contain :validator:`$schema` properties for this reason. If no
    :validator:`$schema` property is found, the default validator class is
    :class:`Draft4Validator`.

    Any other provided positional and keyword arguments will be passed on when
    instantiating the ``cls``.

    :raises:
        :exc:`ValidationError` if the instance is invalid

        :exc:`SchemaError` if the schema itself is invalid

    .. rubric:: Footnotes
    .. [#] known by a validator registered with :func:`validates`
    """
    if cls is None:
        cls = validator_for(schema)
    cls.check_schema(schema)
    cls(schema, *args, **kwargs).validate(instance)
