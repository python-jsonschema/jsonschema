"""
Human-friendly validation error messages.

This module provides functions to transform ValidationError objects into more
readable and actionable error messages for end users.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Union, Type
import json
import re

from jsonschema.exceptions import ValidationError, _Error
from jsonschema import validators


ERROR_FORMATTERS: Dict[str, Callable[[ValidationError], str]] = {}


def register_formatter(validator_type: str):
    """Register a formatter function for a specific validator type."""
    def decorator(func: Callable[[ValidationError], str]):
        ERROR_FORMATTERS[validator_type] = func
        return func
    return decorator


def humanize_property_name(property_name: str) -> str:
    """
    Convert a property name to a more readable format.
    
    Examples:
        color -> Color
        colorWheel -> Color Wheel
        color_wheel -> Color Wheel
    
    Args:
        property_name: The property name to convert
        
    Returns:
        A more human-readable property name
    """
    # Extract the last part of the path if it's a JSON path
    if property_name.startswith('$'):
        parts = property_name.split('.')
        property_name = parts[-1]
    
    # Remove any non-alphanumeric characters from the beginning/end
    property_name = property_name.strip('$."\'[]')
    
    # Handle snake_case: convert _ to spaces
    if '_' in property_name:
        words = property_name.split('_')
        return ' '.join(word.capitalize() for word in words)
    
    # Handle camelCase: add space before capital letters
    elif re.search('[a-z][A-Z]', property_name):
        # Insert space before capital letters
        property_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', property_name)
        return property_name.capitalize()
    
    # Simple case: just capitalize the first letter
    else:
        return property_name.capitalize()


def get_last_property_name(json_path: str) -> str:
    """
    Extract the last property name from a JSON path.
    
    Examples:
        $.color -> color
        $.user.name -> name
        $[0].items -> items
    
    Args:
        json_path: A JSON path
        
    Returns:
        The last property name in the path
    """
    # Extract the last part of a JSON path
    if not json_path:
        return ""
    
    # Parse the JSON path to get the property name
    # Handle array indices and dot notation
    parts = re.findall(r'\.([^.\[\]]+)|\[(\d+)\]', json_path)
    
    # Get the last valid part (either from dot notation or array index)
    for dot_part, array_part in reversed(parts):
        if dot_part:
            return dot_part
        if array_part:
            return f"item {array_part}"
    
    return ""


def format_error(error: ValidationError, include_path: bool = True) -> str:
    """
    Format a ValidationError into a human-friendly message.
    
    Args:
        error: The ValidationError to format
        include_path: Whether to include the property name in the error message
        
    Returns:
        A human-friendly error message
    """
    property_str = ""
    if include_path and error.path:
        property_name = get_last_property_name(error.json_path)
        if property_name:
            readable_name = humanize_property_name(property_name)
            property_str = f" for {readable_name}"
    
    formatter = ERROR_FORMATTERS.get(error.validator)
    if formatter:
        message = formatter(error)
    else:
        message = error.message
    
    return f"{message}{property_str}"


def humanize_error(error: ValidationError) -> str:
    """
    Convert a validation error into a user-friendly message.
    
    This function analyzes the validation error and produces a message that
    explains what went wrong in plain language.
    
    Args:
        error: The ValidationError to humanize
        
    Returns:
        A human-friendly error message
    """
    # For errors with context (like oneOf, anyOf), use the most relevant sub-error
    if error.context:
        from jsonschema.exceptions import best_match
        best = best_match(error.context)
        if best:
            return format_error(best)
    
    return format_error(error)


class HumanValidationError(ValidationError):
    """
    A ValidationError with human-friendly error messages.
    
    This subclass provides more user-friendly error messages by default when 
    converted to a string.
    """
    
    def __str__(self) -> str:
        # Check if we have the required attributes to format the error message
        if not hasattr(self, '_type_checker') or self._type_checker is None:
            return self.message
        return humanize_error(self)


def enable_human_errors(validator_class: Type) -> Type:
    """
    Modify a validator class to use human-friendly error messages.
    
    Args:
        validator_class: The validator class to modify
        
    Returns:
        A new validator class that uses human-friendly error messages
    """
    # Store the original iter_errors and descend methods
    original_iter_errors = validator_class.iter_errors
    original_descend = validator_class.descend
    
    def human_iter_errors(self, instance, _schema=None):
        for error in original_iter_errors(self, instance, _schema):
            # Convert the error to a HumanValidationError
            human_error = HumanValidationError.create_from(error)
            # Copy important attributes
            if hasattr(error, '_type_checker'):
                human_error._type_checker = error._type_checker
            yield human_error
    
    def human_descend(self, instance, schema, path=None, schema_path=None, resolver=None):
        for error in original_descend(self, instance, schema, path, schema_path, resolver):
            # Convert the error to a HumanValidationError
            human_error = HumanValidationError.create_from(error)
            # Copy important attributes
            if hasattr(error, '_type_checker'):
                human_error._type_checker = error._type_checker
            yield human_error
    
    # Create a new validator class
    class HumanValidator(validator_class):
        iter_errors = human_iter_errors
        descend = human_descend
    
    # Use the same name as the original class with "Human" prefix
    HumanValidator.__name__ = f"Human{validator_class.__name__}"
    return HumanValidator


def create_human_validator(schema, *args, **kwargs):
    """
    Create a validator that uses human-friendly error messages.
    
    This is a convenience function that takes the same arguments as
    jsonschema.validators.validator_for(), but returns a validator
    that uses human-friendly error messages.
    
    Args:
        schema: The schema to validate against
        *args: Additional positional arguments to pass to the validator
        **kwargs: Additional keyword arguments to pass to the validator
        
    Returns:
        A validator that uses human-friendly error messages
    """
    validator_cls = validators.validator_for(schema)
    human_cls = enable_human_errors(validator_cls)
    return human_cls(schema, *args, **kwargs)


def apply_to_all_validators():
    """
    Patch all validator classes to use human-friendly error messages.
    
    This function modifies all registered validator classes in the jsonschema
    package to use human-friendly error messages by default.
    """
    for name, validator_class in validators.all_validators.items():
        human_cls = enable_human_errors(validator_class)
        # Replace the validator class in the registry
        validators.all_validators[name] = human_cls


# Formatters for specific validator types

@register_formatter("type")
def format_type_error(error: ValidationError) -> str:
    instance = error.instance
    expected_type = error.validator_value
    
    type_map = {
        "string": "text",
        "integer": "whole number",
        "number": "number",
        "array": "list",
        "object": "object",
        "boolean": "true or false value",
        "null": "null"
    }
    
    friendly_type = type_map.get(expected_type, expected_type)
    
    if isinstance(expected_type, list):
        friendly_types = [type_map.get(t, t) for t in expected_type]
        expected = " or ".join(friendly_types)
    else:
        expected = friendly_type
    
    return f"Expected {expected}, but got {json.dumps(instance)}"


@register_formatter("required")
def format_required_error(error: ValidationError) -> str:
    if isinstance(error.validator_value, list):
        # In a standard required error, the validator_value is the list of required fields
        # We need to determine which one is missing from the instance
        if error.instance is not None and isinstance(error.instance, dict):
            # Find missing fields
            missing_fields = [field for field in error.validator_value if field not in error.instance]
            if missing_fields:
                if len(missing_fields) == 1:
                    missing_field = humanize_property_name(missing_fields[0])
                    return f"Missing required field: {missing_field}"
                missing_str = ", ".join([humanize_property_name(field) for field in missing_fields])
                return f"Missing required fields: {missing_str}"
    
    # Fallback to showing the first value or the whole value
    if isinstance(error.validator_value, list) and error.validator_value:
        return f"Missing required field: {humanize_property_name(error.validator_value[0])}"
    return f"Missing required field: {humanize_property_name(error.validator_value)}"


@register_formatter("pattern")
def format_pattern_error(error: ValidationError) -> str:
    pattern = error.validator_value
    # Try to provide a more friendly pattern description
    pattern_desc = pattern
    
    # Common pattern explanations
    pattern_explanations = {
        r"^[a-zA-Z0-9]+$": "only letters and numbers",
        r"^[a-zA-Z]+$": "only letters",
        r"^[0-9]+$": "only numbers",
        r"^[a-zA-Z0-9_]+$": "only letters, numbers, and underscores",
        r"^[a-zA-Z0-9_-]+$": "only letters, numbers, underscores, and hyphens",
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$": "a valid email address",
    }
    
    if pattern in pattern_explanations:
        return f"The value must contain {pattern_explanations[pattern]}"
    
    return f"The value {json.dumps(error.instance)} doesn't match the required pattern"


@register_formatter("minimum")
def format_minimum_error(error: ValidationError) -> str:
    return f"The value must be at least {error.validator_value}, but was {error.instance}"


@register_formatter("maximum")
def format_maximum_error(error: ValidationError) -> str:
    return f"The value must be at most {error.validator_value}, but was {error.instance}"


@register_formatter("exclusiveMinimum")
def format_exclusive_minimum_error(error: ValidationError) -> str:
    return f"The value must be greater than {error.validator_value}, but was {error.instance}"


@register_formatter("exclusiveMaximum")
def format_exclusive_maximum_error(error: ValidationError) -> str:
    return f"The value must be less than {error.validator_value}, but was {error.instance}"


@register_formatter("minLength")
def format_min_length_error(error: ValidationError) -> str:
    if error.validator_value == 1:
        return f"The value cannot be empty"
    return f"The value must be at least {error.validator_value} characters long"


@register_formatter("maxLength")
def format_max_length_error(error: ValidationError) -> str:
    if error.validator_value == 0:
        return f"The value must be empty"
    return f"The value must be at most {error.validator_value} characters long"


@register_formatter("minItems")
def format_min_items_error(error: ValidationError) -> str:
    if error.validator_value == 1:
        return f"The list cannot be empty"
    return f"The list must contain at least {error.validator_value} items"


@register_formatter("maxItems")
def format_max_items_error(error: ValidationError) -> str:
    if error.validator_value == 0:
        return f"The list must be empty"
    return f"The list must contain at most {error.validator_value} items"


@register_formatter("uniqueItems")
def format_unique_items_error(error: ValidationError) -> str:
    return "All items in the list must be unique"


@register_formatter("enum")
def format_enum_error(error: ValidationError) -> str:
    valid_values = [json.dumps(v) for v in error.validator_value]
    if len(valid_values) == 1:
        return f"The value must be {valid_values[0]}"
    
    return f"The value must be one of: {', '.join(valid_values)}"


@register_formatter("format")
def format_format_error(error: ValidationError) -> str:
    format_type = error.validator_value
    format_descriptions = {
        "date": "a date in YYYY-MM-DD format",
        "time": "a time in HH:MM:SS format",
        "date-time": "a date and time in ISO 8601 format",
        "email": "a valid email address",
        "hostname": "a valid hostname",
        "ipv4": "a valid IPv4 address",
        "ipv6": "a valid IPv6 address",
        "uri": "a valid URI",
        "uuid": "a valid UUID",
    }
    
    description = format_descriptions.get(format_type, f"in {format_type} format")
    return f"The value must be {description}"


@register_formatter("multipleOf")
def format_multiple_of_error(error: ValidationError) -> str:
    return f"The value must be a multiple of {error.validator_value}"


@register_formatter("const")
def format_const_error(error: ValidationError) -> str:
    return f"The value must be {json.dumps(error.validator_value)}"


@register_formatter("additionalProperties")
def format_additional_properties_error(error: ValidationError) -> str:
    if not error.validator_value:
        if hasattr(error, "instance") and isinstance(error.instance, dict):
            # Try to identify the unexpected properties
            schema_props = error.schema.get("properties", {}).keys()
            pattern_props = error.schema.get("patternProperties", {}).keys()
            unexpected = []
            
            for prop in error.instance:
                if prop not in schema_props:
                    is_pattern_match = False
                    for pattern in pattern_props:
                        if re.match(pattern, prop):
                            is_pattern_match = True
                            break
                    if not is_pattern_match:
                        unexpected.append(humanize_property_name(prop))
            
            if unexpected:
                if len(unexpected) == 1:
                    return f"Unknown field: {unexpected[0]}"
                return f"Unknown fields: {', '.join(unexpected)}"
        
        return "Unknown field(s) detected"
    return error.message


@register_formatter("oneOf")
def format_one_of_error(error: ValidationError) -> str:
    if not error.context:
        return "The data must match exactly one of the required schemas"
    
    # Check if the error is because it matched more than one schema
    if len([e for e in error.context if not e.validator]) < len(error.validator_value):
        return "The data matched more than one of the required schemas"
    
    return "The data doesn't match any of the required schemas"


@register_formatter("anyOf")
def format_any_of_error(error: ValidationError) -> str:
    return "The data doesn't match any of the required schemas"


@register_formatter("allOf")
def format_all_of_error(error: ValidationError) -> str:
    if error.context:
        # Use best_match to find the most relevant sub-error
        from jsonschema.exceptions import best_match
        best = best_match(error.context)
        if best:
            return f"The data doesn't satisfy all required conditions: {humanize_error(best)}"
    
    return "The data doesn't satisfy all required conditions"


@register_formatter("not")
def format_not_error(error: ValidationError) -> str:
    return "The data should not match the specified schema"


@register_formatter("if")
def format_if_error(error: ValidationError) -> str:
    # The if/then/else errors are a bit complex - typically they appear
    # in conjunction with other errors
    return "The data doesn't meet the conditional requirements"


@register_formatter("then")
def format_then_error(error: ValidationError) -> str:
    return "The data doesn't meet the required conditions"


@register_formatter("else")
def format_else_error(error: ValidationError) -> str:
    return "The data doesn't meet the alternative conditions"


@register_formatter("dependencies")
def format_dependencies_error(error: ValidationError) -> str:
    if isinstance(error.validator_value, dict):
        for property_name, dependency in error.validator_value.items():
            if property_name in error.instance:
                if isinstance(dependency, list):
                    # Property dependencies
                    missing = [prop for prop in dependency if prop not in error.instance]
                    if missing:
                        dep_list = ", ".join([humanize_property_name(p) for p in missing])
                        return f"When {humanize_property_name(property_name)} is present, {dep_list} must also be present"
    
    return "The data doesn't satisfy property dependencies"


@register_formatter("dependentRequired")
def format_dependent_required_error(error: ValidationError) -> str:
    # Similar to dependencies but for Draft 2019-09 and later
    if isinstance(error.validator_value, dict):
        for property_name, required_props in error.validator_value.items():
            if property_name in error.instance:
                missing = [prop for prop in required_props if prop not in error.instance]
                if missing:
                    dep_list = ", ".join([humanize_property_name(p) for p in missing])
                    return f"When {humanize_property_name(property_name)} is present, {dep_list} must also be present"
    
    return "The data doesn't satisfy property dependencies"


@register_formatter("dependentSchemas")
def format_dependent_schemas_error(error: ValidationError) -> str:
    # For schema dependencies in Draft 2019-09 and later
    return "The data doesn't satisfy the conditional schema requirements"


@register_formatter("propertyNames")
def format_property_names_error(error: ValidationError) -> str:
    if error.context:
        # Try to extract property name that failed validation
        for err in error.context:
            if err.instance:
                return f"Invalid property name: '{err.instance}'"
    
    return "Some property names don't match the required format"


@register_formatter("contains")
def format_contains_error(error: ValidationError) -> str:
    return "The list doesn't contain any items matching the required format"


@register_formatter("minContains")
def format_min_contains_error(error: ValidationError) -> str:
    return f"The list must contain at least {error.validator_value} matching items"


@register_formatter("maxContains")
def format_max_contains_error(error: ValidationError) -> str:
    return f"The list must contain at most {error.validator_value} matching items"


@register_formatter("patternProperties")
def format_pattern_properties_error(error: ValidationError) -> str:
    return "Some properties don't match the required patterns"


@register_formatter("additionalItems")
def format_additional_items_error(error: ValidationError) -> str:
    if not error.validator_value:
        return "Additional items are not allowed in this list"
    return "Some items in the list don't match the required format"


@register_formatter("unevaluatedItems")
def format_unevaluated_items_error(error: ValidationError) -> str:
    return "The list contains unexpected items"


@register_formatter("unevaluatedProperties")
def format_unevaluated_properties_error(error: ValidationError) -> str:
    return "The object contains unexpected properties" 