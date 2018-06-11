import datetime
import re
import socket

from jsonschema.compat import str_types
from jsonschema.exceptions import FormatError


class FormatChecker(object):
    """
    A ``format`` property checker.

    JSON Schema does not mandate that the ``format`` property actually do any
    validation. If validation is desired however, instances of this class can
    be hooked into validators to enable format validation.

    `FormatChecker` objects always return ``True`` when asked about
    formats that they do not know how to validate.

    To check a custom format using a function that takes an instance and
    returns a ``bool``, use the `FormatChecker.checks` or
    `FormatChecker.cls_checks` decorators.

    Arguments:

        formats (~collections.Iterable):

            The known formats to validate. This argument can be used to
            limit which formats will be used during validation.

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

        Arguments:

            format (str):

                The format that the decorated function will check.

            raises (Exception):

                The exception(s) raised by the decorated function when an
                invalid instance is found.

                The exception object will be accessible as the
                `jsonschema.exceptions.ValidationError.cause` attribute of the
                resulting validation error.

        """

        def _checks(func):
            if not isinstance(format, str_types):
                raise FormatError('specified format %s is not a string'
                                  % format)
            if not callable(func):
                raise FormatError('specified function %s is not callable'
                                  % func)
            self.checkers[format] = (func, raises)
            return func
        return _checks

    cls_checks = classmethod(checks)

    def check(self, instance, format):
        """
        Check whether the instance conforms to the given format.

        Arguments:

            instance (*any primitive type*, i.e. str, number, bool):

                The instance to check

            format (str):

                The format that instance should conform to


        Raises:

            FormatError: if the instance does not conform to ``format``

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

        Arguments:

            instance (*any primitive type*, i.e. str, number, bool):

                The instance to check

            format (str):

                The format that instance should conform to

        Returns:

            bool: whether it conformed

        """

        try:
            self.check(instance, format)
        except FormatError:
            return False
        else:
            return True


_draft_checkers = {"draft3": [], "draft4": [], "draft6": []}


def _checks_drafts(
    name=None,
    draft3=None,
    draft4=None,
    draft6=None,
    raises=(),
):
    draft3 = draft3 or name
    draft4 = draft4 or name
    draft6 = draft6 or name

    def wrap(func):
        if draft3:
            _draft_checkers["draft3"].append(draft3)
            func = FormatChecker.cls_checks(draft3, raises)(func)
        if draft4:
            _draft_checkers["draft4"].append(draft4)
            func = FormatChecker.cls_checks(draft4, raises)(func)
        if draft6:
            _draft_checkers["draft6"].append(draft6)
            func = FormatChecker.cls_checks(draft6, raises)(func)
        return func
    return wrap


@_checks_drafts(name="email")
def is_email(instance):
    if not isinstance(instance, str_types):
        return True
    return "@" in instance


_ipv4_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


@_checks_drafts(draft3="ip-address", draft4="ipv4", draft6="ipv4")
def is_ipv4(instance):
    if not isinstance(instance, str_types):
        return True
    if not _ipv4_re.match(instance):
        return False
    return all(0 <= int(component) <= 255 for component in instance.split("."))


if hasattr(socket, "inet_pton"):
    @_checks_drafts(name="ipv6", raises=socket.error)
    def is_ipv6(instance):
        if not isinstance(instance, str_types):
            return True
        return socket.inet_pton(socket.AF_INET6, instance)


_host_name_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}$")


@_checks_drafts(draft3="host-name", draft4="hostname", draft6="hostname")
def is_host_name(instance):
    if not isinstance(instance, str_types):
        return True
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
    @_checks_drafts(name="uri", raises=ValueError)
    def is_uri(instance):
        if not isinstance(instance, str_types):
            return True
        return rfc3987.parse(instance, rule="URI")

    @_checks_drafts(draft6="uri-reference", raises=ValueError)
    def is_uri_reference(instance):
        if not isinstance(instance, str_types):
            return True
        return rfc3987.parse(instance, rule="URI_reference")


try:
    import strict_rfc3339
except ImportError:
    pass
else:
    @_checks_drafts(name="date-time")
    def is_datetime(instance):
        if not isinstance(instance, str_types):
            return True
        return strict_rfc3339.validate_rfc3339(instance)


@_checks_drafts(name="regex", raises=re.error)
def is_regex(instance):
    if not isinstance(instance, str_types):
        return True
    return re.compile(instance)


@_checks_drafts(draft3="date", raises=ValueError)
def is_date(instance):
    if not isinstance(instance, str_types):
        return True
    return datetime.datetime.strptime(instance, "%Y-%m-%d")


@_checks_drafts(draft3="time", raises=ValueError)
def is_time(instance):
    if not isinstance(instance, str_types):
        return True
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
        if (
            not isinstance(instance, str_types) or
            instance.lower() in webcolors.css21_names_to_hex
        ):
            return True
        return is_css_color_code(instance)

    def is_css3_color(instance):
        if instance.lower() in webcolors.css3_names_to_hex:
            return True
        return is_css_color_code(instance)


try:
    import jsonpointer
except ImportError:
    pass
else:
    @_checks_drafts(
        draft6="json-pointer", raises=jsonpointer.JsonPointerException,
    )
    def is_json_pointer(instance):
        if not isinstance(instance, str_types):
            return True
        return jsonpointer.JsonPointer(instance)


try:
    import uritemplate.exceptions
except ImportError:
    pass
else:
    @_checks_drafts(
        draft6="uri-template", raises=uritemplate.exceptions.InvalidTemplate,
    )
    def is_uri_template(
        instance,
        template_validator=uritemplate.Validator().force_balanced_braces(),
    ):
        template = uritemplate.URITemplate(instance)
        return template_validator.validate(template)


draft3_format_checker = FormatChecker(_draft_checkers["draft3"])
draft4_format_checker = FormatChecker(_draft_checkers["draft4"])
draft6_format_checker = FormatChecker(_draft_checkers["draft6"])
