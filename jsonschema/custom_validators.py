"""
Custom validator implementation that allows None values for any property and has special handling
for enum values and additionalProperties validation.
"""
from __future__ import annotations

from typing import Any, Dict, Iterator, Callable, List, Tuple, Union

from jsonschema import ValidationError, Draft7Validator, validators
from jsonschema.validators import extend


def extend_with_default(validator_class):
    """
    Creates a custom validator that:
    1. Allows None for any type, especially objects
    2. Allows None for any enum property by default
    3. Adds special handling for additionalProperties validation
    4. Skips validation for missing or None properties
    """
    validate_properties = validator_class.VALIDATORS["properties"]
    validate_type = validator_class.VALIDATORS["type"]
    validate_enum = validator_class.VALIDATORS.get("enum")
    validate_additional_properties = validator_class.VALIDATORS.get("additionalProperties")

    def set_defaults(validator, properties, instance, schema):
        # Skip validation if instance is None
        if instance is None:
            return

        for property, subschema in properties.items():
            # If the property is missing in the instance, skip validation for it
            if property not in instance or instance.get(property) is None:
                continue
            for error in validate_properties(
                validator,
                properties,
                instance,
                schema,
            ):
                yield error

    def ignore_none(validator, types, instance, schema):
        # Allow None for any type, especially objects
        if instance is None:
            return
        for error in validate_type(validator, types, instance, schema):
            yield error

    def enum_with_nullable(validator, enums, instance, schema):
        # Allow None for any enum property by default
        if instance is None:
            return
        if instance not in enums:
            yield ValidationError(f"{instance} is not one of {enums}")

    def validate_additional(validator, additional_properties, instance, schema):
        # Ensure that instance is not None before iterating
        if instance is None:
            return
        # Raise an error if additional properties are not allowed in the schema
        if not additional_properties:
            for property in instance:
                if property not in schema.get("properties", {}):
                    yield ValidationError(f"Additional property '{property}' is not allowed.")

    return validators.extend(
        validator_class,
        {
            "properties": set_defaults,
            "type": ignore_none,
            "enum": enum_with_nullable,
            "additionalProperties": validate_additional,
        },
    )


CustomValidator = extend_with_default(Draft7Validator)


def custom_validate(instance: Any, schema: Dict[str, Any]) -> None:
    """
    Validate an instance against a schema using the custom validator that 
    allows None values for any property and has special handling for enum values
    and additionalProperties validation.
    
    Args:
        instance: The instance to validate
        schema: The schema to validate against
    
    Raises:
        ValidationError: If the instance is invalid
    """
    CustomValidator(schema).validate(instance) 