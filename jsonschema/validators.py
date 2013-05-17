from __future__ import division, unicode_literals

import collections
import contextlib
import json
import numbers
import pprint
import re
import textwrap

try:
    import requests
except ImportError:
    requests = None

from jsonschema import _utils
from jsonschema.compat import (
    PY3, Sequence, urljoin, urlsplit, urldefrag, unquote, urlopen,
    str_types, int_types, iteritems,
)
from jsonschema._format import FormatError


FLOAT_TOLERANCE = 10 ** -15
validators = {}


class _Unset(object):
    """
    An as-of-yet unset attribute.

    """

    def __repr__(self):
        return "<unset>"
_unset = _Unset()


class _Error(Exception):
    def __init__(
        self, message, validator=_unset, path=(), cause=None, context=(),
        validator_value=_unset, instance=_unset, schema=_unset, schema_path=(),
    ):
        self.message = message
        self.path = collections.deque(path)
        self.schema_path = collections.deque(schema_path)
        self.context = list(context)
        self.cause = self.__cause__ = cause
        self.validator = validator
        self.validator_value = validator_value
        self.instance = instance
        self.schema = schema

    @classmethod
    def create_from(cls, other):
        return cls(
            message=other.message,
            cause=other.cause,
            context=other.context,
            path=other.path,
            schema_path=other.schema_path,
            validator=other.validator,
            validator_value=other.validator_value,
            instance=other.instance,
            schema=other.schema,
        )

    def _set(self, **kwargs):
        for k, v in iteritems(kwargs):
            if getattr(self, k) is _unset:
                setattr(self, k, v)

    def __repr__(self):
        return "<%s: %r>" % (self.__class__.__name__, self.message)

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        if _unset in (
            self.validator, self.validator_value, self.instance, self.schema,
        ):
            return self.message

        path = _utils.format_as_index(self.path)
        schema_path = _utils.format_as_index(list(self.schema_path)[:-1])

        pschema = pprint.pformat(self.schema, width=72)
        pinstance = pprint.pformat(self.instance, width=72)
        return self.message + textwrap.dedent("""

            Failed validating %r in schema%s:
            %s

            On instance%s:
            %s
            """.rstrip()
        ) % (
            self.validator,
            schema_path,
            _utils.indent(pschema),
            path,
            _utils.indent(pinstance),
        )

    if PY3:
        __str__ = __unicode__


class SchemaError(_Error): pass
class ValidationError(_Error): pass
class RefResolutionError(Exception): pass
class UnknownType(Exception): pass


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


class ValidatorMixin(object):
    """
    Concrete implementation of :class:`IValidator`.

    Provides default implementations of each method. Validation of schema
    properties is dispatched to ``validate_property`` methods. E.g., to
    implement a validator for a ``maximum`` property, create a
    ``validate_maximum`` method. Validator methods should yield zero or more
    :exc:`ValidationError``\s to signal failed validation.

    """

    DEFAULT_TYPES = {
        "array" : list, "boolean" : bool, "integer" : int_types,
        "null" : type(None), "number" : numbers.Number, "object" : dict,
        "string" : str_types,
    }

    def __init__(self, schema, types=(), resolver=None, format_checker=None):
        self._types = dict(self.DEFAULT_TYPES)
        self._types.update(types)

        if resolver is None:
            resolver = RefResolver.from_schema(schema)

        self.resolver = resolver
        self.format_checker = format_checker
        self.schema = schema

    def is_type(self, instance, type):
        if type not in self._types:
            raise UnknownType(type)
        pytypes = self._types[type]

        # bool inherits from int, so ensure bools aren't reported as integers
        if isinstance(instance, bool):
            pytypes = _utils.flatten(pytypes)
            num = any(issubclass(pytype, numbers.Number) for pytype in pytypes)
            if num and bool not in pytypes:
                return False
        return isinstance(instance, pytypes)

    def is_valid(self, instance, _schema=None):
        error = next(self.iter_errors(instance, _schema), None)
        return error is None

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
                validator_attr = "validate_%s" % (k.lstrip("$"),)
                validator = getattr(self, validator_attr, None)

                if validator is None:
                    continue

                errors = validator(v, instance, _schema) or ()
                for error in errors:
                    # set details if they weren't already set by the called fn
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


class _Draft34CommonMixin(object):
    """
    Contains the validator methods common to both JSON schema drafts.

    """

    def validate_patternProperties(self, patternProperties, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for pattern, subschema in iteritems(patternProperties):
            for k, v in iteritems(instance):
                if re.search(pattern, k):
                    for error in self.descend(
                            v, subschema, path=k, schema_path=pattern
                    ):
                        yield error

    def validate_additionalProperties(self, aP, instance, schema):
        if not self.is_type(instance, "object"):
            return

        extras = set(_utils.find_additional_properties(instance, schema))

        if self.is_type(aP, "object"):
            for extra in extras:
                for error in self.descend(instance[extra], aP, path=extra):
                    yield error
        elif not aP and extras:
            error = "Additional properties are not allowed (%s %s unexpected)"
            yield ValidationError(error % _utils.extras_msg(extras))

    def validate_items(self, items, instance, schema):
        if not self.is_type(instance, "array"):
            return

        if self.is_type(items, "object"):
            for index, item in enumerate(instance):
                for error in self.descend(item, items, path=index):
                    yield error
        else:
            for (index, item), subschema in zip(enumerate(instance), items):
                for error in self.descend(
                        item, subschema, path=index, schema_path=index
                ):
                    yield error

    def validate_additionalItems(self, aI, instance, schema):
        if (
            not self.is_type(instance, "array") or
            self.is_type(schema.get("items", {}), "object")
        ):
            return

        if self.is_type(aI, "object"):
            for index, item in enumerate(
                    instance[len(schema.get("items", [])):]):
                for error in self.descend(item, aI, path=index):
                    yield error
        elif not aI and len(instance) > len(schema.get("items", [])):
            error = "Additional items are not allowed (%s %s unexpected)"
            yield ValidationError(
                error %
                _utils.extras_msg(instance[len(schema.get("items", [])):])
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

    def _validate_multipleOf(self, dB, instance, schema):
        if not self.is_type(instance, "number"):
            return

        if isinstance(dB, float):
            mod = instance % dB
            failed = (mod > FLOAT_TOLERANCE) and (dB - mod) > FLOAT_TOLERANCE
        else:
            failed = instance % dB

        if failed:
            yield ValidationError(
                "%r is not a multiple of %r" % (instance, dB)
            )

    def validate_minItems(self, mI, instance, schema):
        if self.is_type(instance, "array") and len(instance) < mI:
            yield ValidationError("%r is too short" % (instance,))

    def validate_maxItems(self, mI, instance, schema):
        if self.is_type(instance, "array") and len(instance) > mI:
            yield ValidationError("%r is too long" % (instance,))

    def validate_uniqueItems(self, uI, instance, schema):
        if (
            uI and
            self.is_type(instance, "array") and
            not _utils.uniq(instance)
        ):
            yield ValidationError("%r has non-unique elements" % instance)

    def validate_pattern(self, patrn, instance, schema):
        if self.is_type(instance, "string") and not re.search(patrn, instance):
            yield ValidationError("%r does not match %r" % (instance, patrn))

    def validate_format(self, format, instance, schema):
        if (
            self.format_checker is not None and
            self.is_type(instance, "string")
        ):
            try:
                self.format_checker.check(instance, format)
            except FormatError as error:
                yield ValidationError(error.message, cause=error.cause)

    def validate_minLength(self, mL, instance, schema):
        if self.is_type(instance, "string") and len(instance) < mL:
            yield ValidationError("%r is too short" % (instance,))

    def validate_maxLength(self, mL, instance, schema):
        if self.is_type(instance, "string") and len(instance) > mL:
            yield ValidationError("%r is too long" % (instance,))

    def validate_dependencies(self, dependencies, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, dependency in iteritems(dependencies):
            if property not in instance:
                continue

            if self.is_type(dependency, "object"):
                for error in self.descend(
                        instance, dependency, schema_path=property
                ):
                    yield error
            else:
                dependencies = _utils.ensure_list(dependency)
                for dependency in dependencies:
                    if dependency not in instance:
                        yield ValidationError(
                            "%r is a dependency of %r" % (dependency, property)
                        )

    def validate_enum(self, enums, instance, schema):
        if instance not in enums:
            yield ValidationError("%r is not one of %r" % (instance, enums))

    def validate_ref(self, ref, instance, schema):
        with self.resolver.resolving(ref) as resolved:
            for error in self.descend(instance, resolved):
                yield error


@validates("draft3")
class Draft3Validator(ValidatorMixin, _Draft34CommonMixin, object):
    """
    A validator for JSON Schema draft 3.

    """

    def validate_type(self, types, instance, schema):
        types = _utils.ensure_list(types)

        all_errors = []
        for index, type in enumerate(types):
            if type == "any":
                return
            if self.is_type(type, "object"):
                errors = list(self.descend(instance, type, schema_path=index))
                if not errors:
                    return
                all_errors.extend(errors)
            elif self.is_type(type, "string"):
                if self.is_type(instance, type):
                    return
        else:
            yield ValidationError(
                _utils.types_msg(instance, types), context=all_errors,
            )

    def validate_properties(self, properties, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, subschema in iteritems(properties):
            if property in instance:
                for error in self.descend(
                    instance[property],
                    subschema,
                    path=property,
                    schema_path=property,
                ):
                    yield error
            elif subschema.get("required", False):
                error = ValidationError("%r is a required property" % property)
                error._set(
                    validator="required",
                    validator_value=subschema["required"],
                    instance=instance,
                    schema=schema,
                )
                error.path.appendleft(property)
                error.schema_path.extend([property, "required"])
                yield error

    def validate_disallow(self, disallow, instance, schema):
        for disallowed in _utils.ensure_list(disallow):
            if self.is_valid(instance, {"type" : [disallowed]}):
                yield ValidationError(
                    "%r is disallowed for %r" % (disallowed, instance)
                )

    def validate_extends(self, extends, instance, schema):
        if self.is_type(extends, "object"):
            for error in self.descend(instance, extends):
                yield error
            return
        for index, subschema in enumerate(extends):
            for error in self.descend(instance, subschema, schema_path=index):
                yield error

    validate_divisibleBy = _Draft34CommonMixin._validate_multipleOf

    META_SCHEMA = _utils.load_schema('draft3')


@validates("draft4")
class Draft4Validator(ValidatorMixin, _Draft34CommonMixin, object):
    """
    A validator for JSON Schema draft 4.

    """

    def validate_type(self, types, instance, schema):
        types = _utils.ensure_list(types)

        if not any(self.is_type(instance, type) for type in types):
            yield ValidationError(_utils.types_msg(instance, types))

    def validate_properties(self, properties, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, subschema in iteritems(properties):
            if property in instance:
                for error in self.descend(
                    instance[property],
                    subschema,
                    path=property,
                    schema_path=property,
                ):
                    yield error

    def validate_required(self, required, instance, schema):
        if not self.is_type(instance, "object"):
            return
        for property in required:
            if property not in instance:
                yield ValidationError("%r is a required property" % property)

    def validate_minProperties(self, mP, instance, schema):
        if self.is_type(instance, "object") and len(instance) < mP:
            yield ValidationError("%r is too short" % (instance,))

    def validate_maxProperties(self, mP, instance, schema):
        if not self.is_type(instance, "object"):
            return
        if self.is_type(instance, "object") and len(instance) > mP:
            yield ValidationError("%r is too short" % (instance,))

    def validate_allOf(self, allOf, instance, schema):
        for index, subschema in enumerate(allOf):
            for error in self.descend(instance, subschema, schema_path=index):
                yield error

    def validate_oneOf(self, oneOf, instance, schema):
        subschemas = enumerate(oneOf)
        all_errors = []
        for index, subschema in subschemas:
            errors = list(self.descend(instance, subschema, schema_path=index))
            if not errors:
                first_valid = subschema
                break
            all_errors.extend(errors)
        else:
            yield ValidationError(
                "%r is not valid under any of the given schemas" % (instance,),
                context=all_errors,
            )

        more_valid = [s for i, s in subschemas if self.is_valid(instance, s)]
        if more_valid:
            more_valid.append(first_valid)
            reprs = ", ".join(repr(schema) for schema in more_valid)
            yield ValidationError(
                "%r is valid under each of %s" % (instance, reprs)
            )

    def validate_anyOf(self, anyOf, instance, schema):
        all_errors = []
        for index, subschema in enumerate(anyOf):
            errors = list(self.descend(instance, subschema, schema_path=index))
            if not errors:
                break
            all_errors.extend(errors)
        else:
            yield ValidationError(
                "%r is not valid under any of the given schemas" % (instance,),
                context=all_errors,
            )

    def validate_not(self, not_schema, instance, schema):
        if self.is_valid(instance, not_schema):
            yield ValidationError(
                "%r is not allowed for %r" % (not_schema, instance)
            )

    validate_multipleOf = _Draft34CommonMixin._validate_multipleOf

    META_SCHEMA = _utils.load_schema('draft4')


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

    def __contains__(self, k):
        return k in self._contents

    def __getitem__(self, k):
        """
        Retrieve the child tree with key ``k``.

        If the key is not in the instance that this tree corresponds to and is
        not known by this tree, whatever error would be raised by
        ``instance.__getitem__`` will be propagated (usually this is some
        subclass of :class:`LookupError`.

        """

        if self._instance is not _unset and k not in self:
            self._instance[k]
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


def validate(instance, schema, cls=None, *args, **kwargs):
    if cls is None:
        cls = meta_schemas.get(schema.get("$schema", ""), Draft4Validator)
    cls.check_schema(schema)
    cls(schema, *args, **kwargs).validate(instance)
