import datetime
import re
import socket

from jsonschema.exceptions import FormatError


class FormatChecker(object):
    """
    A ``format`` property checker.

    JSON Schema does not mandate that the ``format`` property actually do any
    validation. If validation is desired however, instances of this class can
    be hooked into validators to enable format validation.

    :class:`FormatChecker` objects always return ``True`` when asked about
    formats that they do not know how to validate.

    To check a custom format using a function that takes an instance and
    returns a ``bool``, use the :meth:`FormatChecker.checks` or
    :meth:`FormatChecker.cls_checks` decorators.

    :argument iterable formats: the known formats to validate. This argument
                                can be used to limit which formats will be used
                                during validation.

    """

    checkers = {}

    def __init__(self, formats=None):
        if formats is None:
            self.checkers = self.checkers.copy()
        else:
            self.checkers = dict((k, self.checkers[k]) for k in formats)

    def checks(self, format, raises=()):
        """
        Register a decorated function as validating a new format.

        :argument str format: the format that the decorated function will check
        :argument Exception raises: the exception(s) raised by the decorated
            function when an invalid instance is found. The exception object
            will be accessible as the :attr:`ValidationError.cause` attribute
            of the resulting validation error.

        """

        def _checks(func):
            self.checkers[format] = (func, raises)
            return func
        return _checks

    cls_checks = classmethod(checks)

    def check(self, instance, format):
        """
        Check whether the instance conforms to the given format.

        :argument instance: the instance to check
        :type: any primitive type (str, number, bool)
        :argument str format: the format that instance should conform to
        :raises: :exc:`FormatError` if instance does not conform to format

        """

        if format not in self.checkers:
            return

        func, raises = self.checkers[format]
        result, cause = None, None
        try:
            result = func(instance)
        except raises as e:
            cause = e
        if not result:
            raise FormatError(
                "%r is not a %r" % (instance, format), cause=cause,
            )

    def conforms(self, instance, format):
        """
        Check whether the instance conforms to the given format.

        :argument instance: the instance to check
        :type: any primitive type (str, number, bool)
        :argument str format: the format that instance should conform to
        :rtype: bool

        """

        try:
            self.check(instance, format)
        except FormatError:
            return False
        else:
            return True


_draft_checkers = {"draft3": [], "draft4": []}


def _checks_drafts(both=None, draft3=None, draft4=None, raises=()):
    draft3 = draft3 or both
    draft4 = draft4 or both

    def wrap(func):
        if draft3:
            _draft_checkers["draft3"].append(draft3)
            func = FormatChecker.cls_checks(draft3, raises)(func)
        if draft4:
            _draft_checkers["draft4"].append(draft4)
            func = FormatChecker.cls_checks(draft4, raises)(func)
        return func
    return wrap


@_checks_drafts("email")
def is_email(instance):
    return "@" in instance


_checks_drafts(draft3="ip-address", draft4="ipv4", raises=socket.error)(
    socket.inet_aton
)


if hasattr(socket, "inet_pton"):
    @_checks_drafts("ipv6", raises=socket.error)
    def is_ipv6(instance):
        return socket.inet_pton(socket.AF_INET6, instance)


_host_name_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}$")

@_checks_drafts(draft3="host-name", draft4="hostname")
def is_host_name(instance):
    if not _host_name_re.match(instance):
        return False
    components = instance.split(".")
    for component in components:
        if len(component) > 63:
            return False
    return True


try:
    import rfc3987
except ImportError:
    pass
else:
    @_checks_drafts("uri", raises=ValueError)
    def is_uri(instance):
        return rfc3987.parse(instance, rule="URI_reference")


try:
    import strict_rfc3339
except ImportError:
    try:
        import isodate
    except ImportError:
        pass
    else:
        _err = (ValueError, isodate.ISO8601Error)
        _checks_drafts("date-time", raises=_err)(isodate.parse_datetime)
else:
        _checks_drafts("date-time")(strict_rfc3339.validate_rfc3339)


_checks_drafts("regex", raises=re.error)(re.compile)


@_checks_drafts(draft3="date", raises=ValueError)
def is_date(instance):
    return datetime.datetime.strptime(instance, "%Y-%m-%d")


@_checks_drafts(draft3="time", raises=ValueError)
def is_time(instance):
    return datetime.datetime.strptime(instance, "%H:%M:%S")


try:
    import webcolors
except ImportError:
    pass
else:
    def is_css_color_code(instance):
        return webcolors.normalize_hex(instance)


    @_checks_drafts(draft3="color", raises=(ValueError, TypeError))
    def is_css21_color(instance):
        if instance.lower() in webcolors.css21_names_to_hex:
            return True
        return is_css_color_code(instance)


    def is_css3_color(instance):
        if instance.lower() in webcolors.css3_names_to_hex:
            return True
        return is_css_color_code(instance)


draft3_format_checker = FormatChecker(_draft_checkers["draft3"])
draft4_format_checker = FormatChecker(_draft_checkers["draft4"])
