from collections.abc import MutableMapping
from urllib.parse import urlsplit
import collections
import itertools
import json
import pkgutil
import re


class URIDict(MutableMapping):
    """
    Dictionary which uses normalized URIs as keys.
    """

    def normalize(self, uri):
        return urlsplit(uri).geturl()

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.store.update(*args, **kwargs)

    def __getitem__(self, uri):
        return self.store[self.normalize(uri)]

    def __setitem__(self, uri, value):
        self.store[self.normalize(uri)] = value

    def __delitem__(self, uri):
        del self.store[self.normalize(uri)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return repr(self.store)


class Unset(object):
    """
    An as-of-yet unset attribute or unprovided default parameter.
    """

    def __repr__(self):
        return "<unset>"


def load_schema(name):
    """
    Load a schema from ./schemas/``name``.json and return it.
    """

    data = pkgutil.get_data("jsonschema", "schemas/{0}.json".format(name))
    return json.loads(data.decode("utf-8"))


def format_as_index(indices):
    """
    Construct a single string containing indexing operations for the indices.

    For example, [1, 2, "foo"] -> [1][2]["foo"]

    Arguments:

        indices (sequence):

            The indices to format.
    """

    if not indices:
        return ""
    return "[%s]" % "][".join(repr(index) for index in indices)


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

    if len(extras) == 1:
        verb = "was"
    else:
        verb = "were"
    return ", ".join(repr(extra) for extra in extras), verb


def types_msg(instance, types):
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


def flatten(suitable_for_isinstance):
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
            types.update(flatten(thing))
        else:
            types.add(thing)
    return tuple(types)


def ensure_list(thing):
    """
    Wrap ``thing`` in a list if it's a single str.

    Otherwise, return it unchanged.
    """

    if isinstance(thing, str):
        return [thing]
    return thing


def dict_equal(one, two):
    """
    Check if two dicts are the same using `equal`
    """
    if len(one.keys()) != len(two.keys()):
        return False

    for key in one:
        if key not in two:
            return False
        if not equal(one[key], two[key]):
            return False

    return True


def list_equal(one, two):
    """
    Check if two lists are the same using `equal`
    """
    if len(one) != len(two):
        return False

    for i in range(0, len(one)):
        if not equal(one[i], two[i]):
            return False

    return True


def is_sequence(instance):
    """
    Checks if an instance is a sequence but not a string
    """
    return isinstance(
        instance, collections.Sequence
    ) and not isinstance(
        instance, str
    )


def is_mapping(instance):
    """
    Checks if an instance is a mapping
    """
    return isinstance(instance, collections.Mapping)


def equal(one, two):
    """
    Check if two things are equal, but evade booleans and ints being equal.
    """
    if is_sequence(one) and is_sequence(two):
        return list_equal(one, two)

    if is_mapping(one) and is_mapping(two):
        return dict_equal(one, two)

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


def uniq(container):
    """
    Check if all of a container's elements are unique.

    Successively tries first to rely that the elements are being sortable
    and finally falls back on brute force.
    """
    try:
        sort = sorted(unbool(i) for i in container)
        sliced = itertools.islice(sort, 1, None)

        for i, j in zip(sort, sliced):
            return not list_equal(i, j)

    except (NotImplementedError, TypeError):
        seen = []
        for e in container:
            e = unbool(e)

            for i in seen:
                if equal(i, e):
                    return False

            seen.append(e)
    return True
