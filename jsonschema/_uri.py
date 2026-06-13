"""
URI-related utility classes.

Extracted from _utils.py for single responsibility:
one module = one concern (URI normalization and lookup).
"""
from urllib.parse import urlsplit
from collections.abc import MutableMapping


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

    def __len__(self):  # pragma: no cover -- untested, but to be removed
        return len(self.store)

    def __repr__(self):  # pragma: no cover -- untested, but to be removed
        return repr(self.store)
