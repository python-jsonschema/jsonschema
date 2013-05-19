from __future__ import unicode_literals
try:
    from gettext import gettext as _  # python 3
except ImportError:
    _ = gettext.translation(my_program_name).ugettext  # python 2


class ErrorStrings:
    additional_properties_not_allowed = _(
        "Additional properties are not allowed (%s %s unexpected)")
    additional_items_not_allowed = _(
        "Additional items are not allowed (%s %s unexpected)")
    minimum_less_than = _("%r is less than the minimum of %r")
    minimum_less_than_or_equal = _(
        "%r is less than or equal to the minimum of %r")
    maximum_more_than = _("%r is more than the maximum of %r")
    maximum_more_than_or_equal = _(
        "%r is more than or equal to the maximum of %r")
    not_multiple_of = _("%r is not a multiple of %r")
    too_short = _("%r is too short")
    too_long = _("%r is too long")
    non_unique_items = _("%r has non-unique elements")
    does_not_match = _("%r does not match %r")
    is_dependency = _("%r is a dependency of %r")
    not_one_of = _("%r is not one of %r")
    required_property = _("%r is a required property")
    disallowed = _("%r is disallowed for %r")
    not_valid_in_any_schema = _(
        "%r is not valid under any of the given schemas")
    valid_in_all_schemas = _("%r is valid under each of %s")
    not_allowed = _("%r is not allowed for %r")
    unresolvable_json_pointer = _("Unresolvable JSON pointer: %r")
    not_a_type_of = _("%r is not of type %s")
    is_not_a = _("%r is not a %r")
