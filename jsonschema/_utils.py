"""
General-purpose utilities for JSON Schema validation.

This module contains equality comparison, uniqueness checking, and
schema introspection utilities used across the jsonschema package.

Moved to dedicated modules for single responsibility:
- URIDict → _uri.py (URI normalization concern)
- find_evaluated_* → _evaluated.py (evaluated item/property tracking)
- is_valid → _evaluated.py (closely related to evaluated tracking)
"""
from collections.abc import Mapping, Sequence
import re

# Re-export from new modules for backward compatibility

# Module-level sentinels so recursive `_uniq_key` calls produce comparable
# keys for nested True/False (function-default sentinels would also work, but
# this makes the intent explicit).
_TRUE = object()
_FALSE = object()
_UNSUPPORTED = object()


class Unset:
    """
    An as-of-yet unset attribute or unprovided default parameter.
    """

    def __repr__(self):  # pragma: no cover
        return "<unset>"


def format_as_index(container, indices):
    """
    Construct a single string containing indexing operations for the indices.

    For example for a container ``bar``, [1, 2, "foo"] -> bar[1][2]["foo"]

    Arguments:

        container (str):

            A word to use for the thing being indexed

        indices (sequence):

            The indices to format.

    """
    if not indices:
        return container
    return f"{container}[{']['.join(repr(index) for index in indices)}]"


def find_additional_properties(instance, schema):
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


def extras_msg(extras):
    """
    Create an error message for extra items or properties.
    """
    verb = "was" if len(extras) == 1 else "were"
    return ", ".join(repr(extra) for extra in extras), verb


def ensure_list(thing):
    """
    Wrap ``thing`` in a list if it's a single str.

    Otherwise, return it unchanged.
    """
    if isinstance(thing, str):
        return [thing]
    return thing


def _mapping_equal(one, two):
    """
    Check if two mappings are equal using the semantics of `equal`.
    """
    if len(one) != len(two):
        return False
    return all(
        key in two and equal(value, two[key])
        for key, value in one.items()
    )


def _sequence_equal(one, two):
    """
    Check if two sequences are equal using the semantics of `equal`.
    """
    if len(one) != len(two):
        return False
    return all(equal(i, j) for i, j in zip(one, two))


def equal(one, two):
    """
    Check if two things are equal evading some Python type hierarchy semantics.

    Specifically in JSON Schema, evade `bool` inheriting from `int`,
    recursing into sequences to do the same.
    """
    if one is two:
        return True
    if isinstance(one, str) or isinstance(two, str):
        return one == two
    if isinstance(one, Sequence) and isinstance(two, Sequence):
        return _sequence_equal(one, two)
    if isinstance(one, Mapping) and isinstance(two, Mapping):
        return _mapping_equal(one, two)
    return unbool(one) == unbool(two)


def unbool(element, true=object(), false=object()):
    """
    A hack to make True and 1 and False and 0 unique for ``uniq``.
    """
    if element is True:
        return true
    elif element is False:
        return false
    return element


def _uniq_key(element):
    """
    Convert an element into a hashable key compatible with `equal`.

    Returns `_UNSUPPORTED` when an element cannot be canonically hashed.
    """
    # NaN never equals itself, so it can't be deduplicated via hashing.
    # Some custom container equality implementations can also raise here
    # (e.g. mappings containing unhashable keys), in which case we fall back
    # to brute force as well.
    try:
        if element != element:  # noqa: PLR0124 -- NaN detection
            return _UNSUPPORTED
    except TypeError:
        return _UNSUPPORTED

    element = unbool(element, true=_TRUE, false=_FALSE)

    # Tagged tuples ("scalar"/"sequence"/"mapping", ...) prevent hash
    # collisions between values of different shapes.
    if isinstance(element, Sequence) and not isinstance(element, str):
        values = []
        for each in element:
            key = _uniq_key(each)
            if key is _UNSUPPORTED:
                return _UNSUPPORTED
            values.append(key)
        return "sequence", tuple(values)

    if isinstance(element, Mapping):
        items = []
        for key, value in element.items():
            value_key = _uniq_key(value)
            if value_key is _UNSUPPORTED:
                return _UNSUPPORTED
            items.append((key, value_key))
        try:
            return "mapping", frozenset(items)
        except TypeError:
            # Unhashable mapping key — fall back to brute force.
            return _UNSUPPORTED

    try:
        hash(element)
    except TypeError:
        return _UNSUPPORTED

    return "scalar", element


def uniq(container):
    """
    Check if all of a container's elements are unique.

    Tries to use a structural hash compatible with `equal`, falling back to
    brute force when necessary.
    """
    seen_keys = set()
    unsupported = []

    for element in container:
        key = _uniq_key(element)

        if key is _UNSUPPORTED:
            for previous in unsupported:
                if equal(previous, element):
                    return False
            unsupported.append(element)
            continue

        if key in seen_keys:
            return False

        seen_keys.add(key)

    return True
