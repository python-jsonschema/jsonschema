from __future__ import unicode_literals
import sys
import operator

try:
    from collections import MutableMapping, Sequence  # noqa
except ImportError:
    from collections.abc import MutableMapping, Sequence  # noqa

PY3 = sys.version_info[0] >= 3

if PY3:
    zip = zip
    from urllib.parse import (
        unquote, urljoin, urlunsplit, SplitResult, urlsplit as _urlsplit
    )
    from urllib.request import urlopen
    str_types = str,
    int_types = int,
    iteritems = operator.methodcaller("items")
else:
    from itertools import izip as zip  # noqa
    from urlparse import (
        urljoin, urlunsplit, SplitResult, urlsplit as _urlsplit # noqa
    )
    from urllib import unquote  # noqa
    from urllib2 import urlopen  # noqa
    str_types = basestring
    int_types = int, long
    iteritems = operator.methodcaller("iteritems")


# On python < 3.3 fragments are not handled properly with unknown schemes
def urlsplit(url):
    scheme, netloc, path, query, fragment = _urlsplit(url)
    if "#" in path:
        path, fragment = path.split("#", 1)
    return SplitResult(scheme, netloc, path, query, fragment)


def urldefrag(url):
    if "#" in url:
        s, n, p, q, frag = urlsplit(url)
        defrag = urlunsplit((s, n, p, q, ''))
    else:
        defrag = url
        frag = ''
    return defrag, frag


# flake8: noqa
