import collections
import itertools
import pprint
import textwrap

from jsonschema import _utils
from jsonschema.compat import PY3, iteritems


WEAK_MATCHES = frozenset(["anyOf", "oneOf"])
STRONG_MATCHES = frozenset()

_unset = _utils.Unset()


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

    @classmethod
    def create_from(cls, other):
        return cls(**other._contents())

    def _set(self, **kwargs):
        for k, v in iteritems(kwargs):
            if getattr(self, k) is _unset:
                setattr(self, k, v)

    def _contents(self):
        return dict(
            (attr, getattr(self, attr)) for attr in (
                "message", "cause", "context", "path", "schema_path",
                "validator", "validator_value", "instance", "schema"
            )
        )


class ValidationError(_Error):
    pass


class SchemaError(_Error):
    pass


class RefResolutionError(Exception):
    pass


class UnknownType(Exception):
    def __init__(self, type, instance, schema):
        self.type = type
        self.instance = instance
        self.schema = schema

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        pschema = pprint.pformat(self.schema, width=72)
        pinstance = pprint.pformat(self.instance, width=72)
        return textwrap.dedent("""
            Unknown type %r for validator with schema:
            %s

            While checking instance:
            %s
            """.rstrip()
        ) % (self.type, _utils.indent(pschema), _utils.indent(pinstance))

    if PY3:
        __str__ = __unicode__



class FormatError(Exception):
    def __init__(self, message, cause=None):
        super(FormatError, self).__init__(message, cause)
        self.message = message
        self.cause = self.__cause__ = cause

    def __str__(self):
        return self.message.encode("utf-8")

    def __unicode__(self):
        return self.message

    if PY3:
        __str__ = __unicode__


def by_relevance(weak=WEAK_MATCHES, strong=STRONG_MATCHES):
    def relevance(error):
        validator = error.validator
        return -len(error.path), validator not in weak, validator in strong
    return relevance


def best_match(errors, key=by_relevance()):
    errors = iter(errors)
    best = next(errors, None)
    if best is None:
        return
    best = max(itertools.chain([best], errors), key=key)

    while best.context:
        best = min(best.context, key=key)
    return best
