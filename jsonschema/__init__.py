"""
An implementation of JSON Schema for Python

The main functionality is provided by the validator classes for each of the
supported JSON Schema versions.

Most commonly, :func:`validate` is the quickest way to simply validate a given
instance under a schema, and will create a validator for you.

"""

__version__ = "1.4.0-dev"

from jsonschema._format import (
    FormatChecker, FormatError, draft3_format_checker, draft4_format_checker,
)
from jsonschema.validators import (
    RefResolutionError, SchemaError, ValidationError, UnknownType, 
    ErrorTree, Draft3Validator, Draft4Validator, RefResolver, ValidatorMixin,
    validate, validates,
)
