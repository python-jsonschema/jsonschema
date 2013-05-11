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
    from urllib import parse as urlparse
    from urllib.parse import unquote
    from urllib.request import urlopen
    basestring = unicode = str
    long = int
    iteritems = operator.methodcaller("items")
else:
    from itertools import izip as zip  # noqa
    import urlparse  # noqa
    from urllib import unquote  # noqa
    from urllib2 import urlopen  # noqa
    basestring = basestring
    unicode = unicode
    long = long
    iteritems = operator.methodcaller("iteritems")
