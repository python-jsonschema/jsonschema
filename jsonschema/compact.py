"""
Temporarily putting this file back in

2021-09-30
"""
import logging
import operator
import sys

logger = logging.getLogger(__name__)

logger.warning("This file will be removed with the next release")

PY3 = sys.version_info[0] >= 3

if PY3:
    iteritems = operator.methodcaller("items")
else:
    iteritems = operator.methodcaller("iteritems")
