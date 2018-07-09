import operator
import sys


try:
    from collections import MutableMapping, Sequence  # noqa
except ImportError:
    from collections.abc import MutableMapping, Sequence  # noqa

PY3 = sys.version_info[0] >= 3

if PY3:
    zip = zip
    from functools import lru_cache
    from io import StringIO
    from urllib.parse import unquote
    from urllib.request import urlopen
    str_types = str,
    int_types = int,
    iteritems = operator.methodcaller("items")
else:
    from itertools import izip as zip  # noqa
    from StringIO import StringIO
    from urllib import unquote  # noqa
    from urllib2 import urlopen  # noqa
    str_types = basestring
    int_types = int, long
    iteritems = operator.methodcaller("iteritems")

    from functools32 import lru_cache


# flake8: noqa
