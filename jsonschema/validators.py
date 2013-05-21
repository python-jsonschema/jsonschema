from __future__ import division, unicode_literals

import collections
import contextlib
import json
import numbers
import warnings

try:
    import requests
except ImportError:
    requests = None

from jsonschema import _utils, _validators
from jsonschema.compat import (
    PY3, Sequence, urljoin, urlsplit, urldefrag, unquote, urlopen,
    str_types, int_types, iteritems,
)
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
        if "id" in cls.META_SCHEMA:
            meta_schemas[cls.META_SCHEMA["id"]] = cls
        return cls
    return _validates


def create(meta_schema, validators=(), version=None, default_types=None):  # noqa
    if default_types is None:
        default_types = {
            "array" : list, "boolean" : bool, "integer" : int_types,
            "null" : type(None), "number" : numbers.Number, "object" : dict,
            "string" : str_types,
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

            with self.resolver.in_scope(_schema.get("id", "")):
                ref = _schema.get("$ref")
                if ref is not None:
                    validators = [("$ref", ref)]
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
                        if k != "$ref":
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
                raise UnknownType(type)
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

        name = "{0}Validator".format(version.title().replace(" ", ""))
        if not PY3 and isinstance(name, unicode):
            name = name.encode("utf-8")
        Validator.__name__ = name

    return Validator


def extend(validator, validators, version=None):
    all_validators = validator.VALIDATORS
    all_validators.update(validators)
    return create(
        meta_schema=validator.META_SCHEMA,
        validators=all_validators,
        version=version,
        default_types=validator.DEFAULT_TYPES,
    )


class ValidatorMixin(create(meta_schema={})):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "ValidatorMixin is deprecated. "
            "Use jsonschema.validators.create instead.",
            DeprecationWarning,
        )
        super(ValidatorMixin, self).__init__(*args, **kwargs)

        class _VALIDATORS(dict):
            def __missing__(this, key, dflt=None):
                return getattr(self, "validate_" + str(key).lstrip("$"), dflt)
            get = __missing__

        self.VALIDATORS = _VALIDATORS()


Draft3Validator = create(
    meta_schema=_utils.load_schema("draft3"),
    validators={
        "$ref" : _validators.ref,
        "additionalItems" : _validators.additionalItems,
        "additionalProperties" : _validators.additionalProperties,
        "dependencies" : _validators.dependencies,
        "disallow" : _validators.disallow_draft3,
        "divisibleBy" : _validators.multipleOf,
        "enum" : _validators.enum,
        "extends" : _validators.extends_draft3,
        "format" : _validators.format,
        "items" : _validators.items,
        "maxItems" : _validators.maxItems,
        "maxLength" : _validators.maxLength,
        "maximum" : _validators.maximum,
        "minItems" : _validators.minItems,
        "minLength" : _validators.minLength,
        "minimum" : _validators.minimum,
        "multipleOf" : _validators.multipleOf,
        "pattern" : _validators.pattern,
        "patternProperties" : _validators.patternProperties,
        "properties" : _validators.properties_draft3,
        "type" : _validators.type_draft3,
        "uniqueItems" : _validators.uniqueItems,
    },
    version="draft3",
)

Draft4Validator = create(
    meta_schema=_utils.load_schema("draft4"),
    validators={
        "$ref" : _validators.ref,
        "additionalItems" : _validators.additionalItems,
        "additionalProperties" : _validators.additionalProperties,
        "allOf" : _validators.allOf_draft4,
        "anyOf" : _validators.anyOf_draft4,
        "dependencies" : _validators.dependencies,
        "enum" : _validators.enum,
        "format" : _validators.format,
        "items" : _validators.items,
        "maxItems" : _validators.maxItems,
        "maxLength" : _validators.maxLength,
        "maxProperties" : _validators.maxProperties_draft4,
        "maximum" : _validators.maximum,
        "minItems" : _validators.minItems,
        "minLength" : _validators.minLength,
        "minProperties" : _validators.minProperties_draft4,
        "minimum" : _validators.minimum,
        "multipleOf" : _validators.multipleOf,
        "not" : _validators.not_draft4,
        "oneOf" : _validators.oneOf_draft4,
        "pattern" : _validators.pattern,
        "patternProperties" : _validators.patternProperties,
        "properties" : _validators.properties_draft4,
        "required" : _validators.required_draft4,
        "type" : _validators.type_draft4,
        "uniqueItems" : _validators.uniqueItems,
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

        return cls(schema.get("id", ""), schema, *args, **kwargs)

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

        fragment = fragment.lstrip("/")
        parts = unquote(fragment).split("/") if fragment else []

        for part in parts:
            part = part.replace("~1", "/").replace("~0", "~")

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
            scheme in ["http", "https"] and
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


class ErrorTree(object):
    """
    ErrorTrees make it easier to check which validations failed.

    """

    _instance = _unset

    def __init__(self, errors=()):
        self.errors = {}
        self._contents = collections.defaultdict(self.__class__)

        for error in errors:
            container = self
            for element in error.path:
                container = container[element]
            container.errors[error.validator] = error

            self._instance = error.instance

    def __contains__(self, index):
        """
        Check whether ``instance[index]`` has any errors.

        """

        return index in self._contents

    def __getitem__(self, index):
        """
        Retrieve the child tree one level down at the given ``index``.

        If the index is not in the instance that this tree corresponds to and
        is not known by this tree, whatever error would be raised by
        ``instance.__getitem__`` will be propagated (usually this is some
        subclass of :class:`LookupError`.

        """

        if self._instance is not _unset and index not in self:
            self._instance[index]
        return self._contents[index]

    def __setitem__(self, index, value):
        self._contents[index] = value

    def __iter__(self):
        """
        Iterate (non-recursively) over the indices in the instance with errors.

        """

        return iter(self._contents)

    def __len__(self):
        """
        Same as :attr:`total_errors`.

        """

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


def validate(instance, schema, cls=None, *args, **kwargs):
    if cls is None:
        cls = meta_schemas.get(schema.get("$schema", ""), Draft4Validator)
    cls.check_schema(schema)
    cls(schema, *args, **kwargs).validate(instance)
