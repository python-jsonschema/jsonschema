# Raise an exception from another exception 2.x.
import sys
def raise_exception_from(exception, original_exception):
    tb = sys.exc_info()[2]
    raise exception, None, tb
