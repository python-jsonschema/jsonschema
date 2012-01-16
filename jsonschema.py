"""
An implementation of JSON Schema for Python

The main functionality is provided by the :class:`Validator` class, with the
:function:`validate` function being the most common way to quickly create a
:class:`Validator` object and validate an instance with a given schema.

The :class:`Validator` class generally attempts to be as strict as possible
under the JSON Schema specification. See its docstring for details.

What's Missing
--------------

* ``uniqueItems``
* ``format``
* ``extends``
* ``$ref``
* ``$schema``

"""

from __future__ import division, with_statement

import re
import types
import warnings


__version__ = "0.2"

try:  # pragma: no cover, 2.5 support
    next
except NameError:  # pragma: no cover
    _none = object()

    def next(iterator, default=_none):
        try:
            return iterator.next()
        except StopIteration:
            if default is not _none:
                return default
            raise


class SchemaError(Exception):
    """
    The provided schema is malformed.

    """


class ValidationError(Exception):
    """
    The instance didn't properly validate with the provided schema.

    """

    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop("errors", [])
        super(ValidationError, self).__init__(*args, **kwargs)


class Validator(object):
    """
    A JSON Schema validator.

    """

    _SKIPPED = set([                                              # handled in:
        u"dependencies", u"required",                             # properties
        u"exclusiveMinimum", u"exclusiveMaximum",                 # min/max
        u"default", u"description", u"links", u"name", u"title",  # none needed
    ])

    _TYPES = {
        u"array" : list, u"boolean" : bool, u"integer" : int,
        u"null" : types.NoneType, u"object" : dict,
    }

    def __init__(
        self, stop_on_error=True, unknown_type="error",
        unknown_property="error", string_types=basestring,
        number_types=(int, float)
    ):
        """
        Initialize a Validator.

        If ``stop_on_error`` is ``True`` (default), immediately stop validation
        when an error occurs. Otherwise, wait until validation is completed,
        then display all validation errors at once.

        ``unknown_type`` and ``unknown_property`` control what to do when an
        unknown type (resp. property) is encountered. By default an error is
        raised (``"error"``). Other valid inputs are ``"warn"``, raising a
        warning, and ``"skip"`` to ignore.

        ``string_types`` and ``number_types`` control which Python types are
        considered to be JSON ``String``s and ``Number``s respectively. By
        default, ``basestring`` (which means, ``str`` + ``unicode``) is used
        for ``string_types``, and ``int`` and ``float`` are the number_types.
        To override this behavior (e.g. for ``decimal.Decimal``), provide a
        type or tuple of types to use (*including* the default types if so
        desired).

        """

        self.stop_on_error = stop_on_error
        self._unknown_type = unknown_type
        self._unknown_property = unknown_property

        self._types = dict(
            self._TYPES, string=string_types, number=number_types
        )
        self._types[u"any"] = tuple(self._types.values())

    def _is_type(self, instance, type):
        """
        Check if an ``instance`` is of the provided ``type``.

        """

        py_type = self._types.get(type)

        if py_type is None:
            return self._schema_error(
                self._unknown_type, u"%r is not a known type" % (type,)
            )

        # the only thing we're careful about here is evading bool inheriting
        # from int, so let's be even dirtier than usual

        elif (
            # it's not a bool, so no worries
            not isinstance(instance, bool) or

            # it is a bool, but we're checking for a bool, so no worries
            (
                py_type is bool or
                isinstance(py_type, tuple) and bool in py_type
            )

        ):
            return isinstance(instance, py_type)

    def _error(self, msg):
        """
        Something failed to validate. ``msg`` will have details.

        """

        if self.stop_on_error:
            raise ValidationError(msg)
        else:
            self._errors.append(msg)

    def _schema_error(self, level, msg):
        if level == "skip":
            return
        elif level == "warn":
            warnings.warn(msg)
        else:
            raise SchemaError(msg)

    def is_valid(self, instance, schema):
        """
        Check if the ``instance`` is valid under the ``schema``.

        Returns a bool containing whether validation succeeded.

        """

        # HACK: Temporarily patches self._errors, just in case we're not
        #       stopping on errors, so that errors raised during the validity
        #       check don't pollute self._errors as part of a subroutine

        current_errors = self._errors

        try:
            self.validate(instance, schema)
        except ValidationError:
            return False
        else:
            if self._errors:
                return False
            return True
        finally:
            self._errors = current_errors

    def _validate(self, instance, schema):
        """
        Validate an ``instance`` under the given ``schema``.

        """

        for k, v in schema.iteritems():
            if k in self._SKIPPED:
                continue

            validator = getattr(self, u"validate_%s" % (k,), None)

            if validator is None:
                self._schema_error(
                    self._unknown_property,
                    u"%r is not a known schema property" % (k,)
                )
                return

            validator(v, instance, schema)

    def validate(self, instance, schema):
        self._errors = []
        self._validate(instance, schema)
        if self._errors:
            raise ValidationError(
                u"Validation failed with errors (see .errors for details)",
                errors=list(self._errors)
            )

    def validate_type(self, types, instance, schema):
        types = _list(types)

        for type in types:
            # Ouch. Brain hurts. Two paths here, either we have a schema, then
            # check if the instance is valid under it
            if ((
                self._is_type(type, "object") and
                self._is_type(instance, "object") and
                self.is_valid(instance, type)

            # Or we have a type as a string, just check if the instance is that
            # type. Also, HACK: we can reach the `or` here if skip_types is
            # something other than error. If so, bail out.

            ) or (
                self._is_type(type, "string") and
                (self._is_type(instance, type) or type not in self._types)
            )):
                return
        else:
            self._error(u"%r is not of type %r" % (instance, _delist(types)))

    def validate_properties(self, properties, instance, schema):
        for property, subschema in properties.iteritems():
            if property in instance:
                dependencies = _list(subschema.get(u"dependencies", []))
                if self._is_type(dependencies, "object"):
                    self._validate(instance, dependencies)
                else:
                    missing = (d for d in dependencies if d not in instance)
                    first = next(missing, None)
                    if first is not None:
                        self._error(
                            u"%r is a dependency of %r" % (first, property)
                        )

                self._validate(instance[property], subschema)
            elif subschema.get(u"required", False):
                self._error(u"%r is a required property" % (property,))

    def validate_patternProperties(self, patternProperties, instance, schema):
        for pattern, subschema in patternProperties.iteritems():
            for k, v in instance.iteritems():
                if re.match(pattern, k):
                    self._validate(v, subschema)

    def validate_additionalProperties(self, aP, instance, schema):
        # no viewkeys in <2.7, and pypy seems to fail on vk - vk anyhow, so...
        extras = set(instance) - set(schema.get(u"properties", {}))

        if self._is_type(aP, "object"):
            for extra in extras:
                self._validate(instance[extra], aP)
        elif not aP and extras:
            self._error(u"Additional properties are not allowed")

    def validate_items(self, items, instance, schema):
        if self._is_type(items, "object"):
            for item in instance:
                self._validate(item, items)
        else:
            for item, subschema in zip(instance, items):
                self._validate(item, subschema)

    def validate_additionalItems(self, aI, instance, schema):
        if self._is_type(aI, "object"):
            for item in instance[len(schema):]:
                self._validate(item, aI)
        elif not aI and len(instance) > len(schema):
            self._error(u"Additional items are not allowed")

    def validate_minimum(self, minimum, instance, schema):
        if schema.get(u"exclusiveMinimum", False):
            failed = instance <= minimum
            cmp = u"less than or equal to"
        else:
            failed = instance < minimum
            cmp = u"less than"

        if failed:
            self._error(
                u"%r is %s the minimum of %r" % (instance, cmp, minimum)
            )

    def validate_maximum(self, maximum, instance, schema):
        if schema.get(u"exclusiveMaximum", False):
            failed = instance >= maximum
            cmp = u"greater than or equal to"
        else:
            failed = instance > maximum
            cmp = u"greater than"

        if failed:
            self._error(
                u"%r is %s the maximum of %r" % (instance, cmp, maximum)
            )

    def validate_minItems(self, mI, instance, schema):
        if self._is_type(instance, "array") and len(instance) < mI:
            self._error(u"%r is too short" % (instance,))

    def validate_maxItems(self, mI, instance, schema):
        if self._is_type(instance, "array") and len(instance) > mI:
            self._error(u"%r is too long" % (instance,))

    def validate_pattern(self, patrn, instance, schema):
        if self._is_type(instance, "string") and not re.match(patrn, instance):
            self._error(u"%r does not match %r" % (instance, patrn))

    def validate_minLength(self, mL, instance, schema):
        if self._is_type(instance, "string") and len(instance) < mL:
            self._error(u"%r is too short" % (instance,))

    def validate_maxLength(self, mL, instance, schema):
        if self._is_type(instance, "string") and len(instance) > mL:
            self._error(u"%r is too long" % (instance,))

    def validate_enum(self, enums, instance, schema):
        if instance not in enums:
            self._error(u"%r is not one of %r" % (instance, enums))

    def validate_divisibleBy(self, dB, instance, schema):
        if isinstance(dB, float):
            failed = dB - instance % dB > .0000000001
        else:
            failed = instance % dB

        if failed:
            self._error(u"%r is not divisible by %r" % (instance, dB))

    def validate_disallow(self, disallow, instance, schema):
        disallow = _list(disallow)

        if any(self.is_valid(instance, {"type" : [d]}) for d in disallow):
            self._error(
                u"%r is disallowed for %r" % (_delist(disallow), instance)
            )


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


def validate(instance, schema, cls=Validator, *args, **kwargs):
    """
    Validate an ``instance`` under the given ``schema``.

    By default, the :class:`Validator` class from this module is used to
    perform the validation. To use another validator, pass it into the ``cls``
    argument.

    Any other provided positional and keyword arguments will be provided to the
    ``cls``. See the :class:`Validator` class' docstring for details on the
    arguments it accepts.

    """

    validator = cls(*args, **kwargs)
    validator.validate(instance, schema)
