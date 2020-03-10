import sys
from contextlib import contextmanager

from jsonschema.compat import NativeIO


def bug(issue=None):
    message = "A known bug."
    if issue is not None:
        message += " See issue #{issue}.".format(issue=issue)
    return message


@contextmanager
def captured_output():
    new_out, new_err = NativeIO(), NativeIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err
