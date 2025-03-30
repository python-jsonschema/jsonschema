"""
Examples of using human-friendly error messages.

This module contains examples of how to use the human-friendly error messages
in different scenarios.
"""
import json
from jsonschema import (
    validate, 
    human_validate,
    humanize_error, 
    enable_human_errors, 
    Draft202012Validator,
    HumanValidationError,
    create_human_validator,
    apply_to_all_validators,
)


def example_basic_usage():
    """Basic usage example of human_validate."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
            "email": {"type": "string", "format": "email"}
        },
        "required": ["name", "email"]
    }
    
    data = {
        "name": "John",
        "age": "twenty"  # Invalid type
    }
    
    # Standard validation (technical error)
    try:
        validate(data, schema)
    except Exception as e:
        print("Technical error:", e)
    
    # Human-friendly validation
    try:
        human_validate(data, schema)
    except Exception as e:
        print("User-friendly error:", e)


def example_convert_existing_errors():
    """Example of converting existing validation errors."""
    schema = {"type": "array", "minItems": 3}
    data = [1]
    
    try:
        validate(data, schema)
    except Exception as e:
        technical_error = e
        print("Technical error:", technical_error)
        
        # Convert to human-friendly message
        friendly_message = humanize_error(technical_error)
        print("User-friendly message:", friendly_message)


def example_create_human_validator():
    """Example of creating a human validator directly."""
    schema = {
        "type": "object",
        "properties": {
            "favoriteColor": {"enum": ["red", "green", "blue"]},
            "preferred_size": {"enum": ["small", "medium", "large"]}
        }
    }
    
    # Create a standard validator for comparison
    standard_validator = Draft202012Validator(schema)
    
    # Create a validator with human-friendly errors
    human_validator = create_human_validator(schema)
    
    # Validate some data
    data = {
        "favoriteColor": "yellow",
        "preferred_size": "extra large"
    }
    
    standard_errors = list(standard_validator.iter_errors(data))
    human_errors = list(human_validator.iter_errors(data))
    
    if standard_errors:
        print("Technical errors:")
        for error in standard_errors:
            print(f"- {error}")
    
    if human_errors:
        print("\nHuman-friendly errors:")
        for error in human_errors:
            print(f"- {error}")


def example_custom_error_handling():
    """Example of custom error handling with human-friendly errors."""
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 3, "maxLength": 20},
            "password": {"type": "string", "minLength": 8}
        },
        "required": ["username", "password"]
    }
    
    # Function to validate user credentials
    def validate_credentials(credentials):
        try:
            human_validate(credentials, schema)
            return {"valid": True, "message": "Credentials are valid"}
        except Exception as e:
            return {
                "valid": False, 
                "message": str(e),
                "field": get_field_from_error(e)
            }
    
    # Helper to extract field name from error
    def get_field_from_error(error):
        if hasattr(error, "path") and error.path:
            return list(error.path)[-1]
        return None
    
    # Test validation
    print(validate_credentials({"username": "ab", "password": "secret"}))
    print(validate_credentials({"username": "john"}))


def example_patch_all_validators():
    """Example of patching all validators to use human-friendly errors."""
    # Apply human-friendly errors to all validators
    apply_to_all_validators()
    
    schema = {"type": "string", "minLength": 5}
    
    # Now all validators will use human-friendly errors
    validator = Draft202012Validator(schema)
    
    for error in validator.iter_errors("abc"):
        print("Human-friendly error from patched validator:", error)


def example_error_tree():
    """Example of working with error trees and human-friendly errors."""
    from jsonschema.exceptions import ErrorTree
    
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 18}
                },
                "required": ["name", "age"]
            },
            "preferences": {
                "type": "object",
                "properties": {
                    "theme": {"enum": ["light", "dark"]}
                }
            }
        },
        "required": ["user"]
    }
    
    data = {
        "user": {
            "name": 123,  # Invalid type
            "age": 16     # Below minimum
        },
        "preferences": {
            "theme": "blue"  # Not in enum
        }
    }
    
    # Use human-friendly validator
    validator = create_human_validator(schema)
    errors = list(validator.iter_errors(data))
    
    # Create error tree
    error_tree = ErrorTree(errors)
    
    # Process errors by path
    def process_error_tree(tree, path="$"):
        messages = []
        
        # Add errors at current level
        for validator_type, error in tree.errors.items():
            messages.append(f"{path}: {error}")
        
        # Process child errors
        for property_name, child_tree in tree._contents.items():
            next_path = f"{path}.{property_name}" if path != "$" else f"$.{property_name}"
            messages.extend(process_error_tree(child_tree, next_path))
        
        return messages
    
    # Print structured error messages
    for message in process_error_tree(error_tree):
        print(message)


def example_property_name_formatting():
    """Example of how property names are formatted in error messages."""
    schema = {
        "type": "object",
        "properties": {
            "color": {"type": "string"},
            "colorWheel": {"type": "string"},
            "color_scheme": {"type": "string"},
            "user": {
                "type": "object",
                "properties": {
                    "firstName": {"type": "string"},
                    "last_name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 18}
                }
            }
        },
        "required": ["color", "colorWheel", "color_scheme", "user"]
    }
    
    data = {
        "color": 123,  # Wrong type
        "user": {
            "firstName": 456,  # Wrong type
            "last_name": 789,  # Wrong type
            "age": 16  # Below minimum
        }
    }
    
    # Create a human validator
    validator = create_human_validator(schema)
    errors = list(validator.iter_errors(data))
    
    print("Property name formatting examples:")
    for error in sorted(errors, key=lambda e: str(e)):
        print(f"- {error}")
    
    # Test missing required fields
    data2 = {}
    errors2 = list(validator.iter_errors(data2))
    
    print("\nMissing required fields:")
    for error in errors2:
        print(f"- {error}")


def example_comprehensive_validation():
    """Example demonstrating human-friendly messages for all types of validations."""
    # Create a schema with many different validation keywords
    schema = {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "minLength": 3,
                "maxLength": 20,
                "pattern": "^[a-zA-Z0-9_]+$"
            },
            "email": {
                "type": "string",
                "format": "email"
            },
            "age": {
                "type": "integer",
                "minimum": 18,
                "maximum": 100
            },
            "score": {
                "type": "number",
                "exclusiveMinimum": 0,
                "exclusiveMaximum": 100,
                "multipleOf": 0.5
            },
            "role": {
                "enum": ["admin", "user", "guest"]
            },
            "settings": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "theme": {"enum": ["light", "dark"]},
                    "notifications": {"type": "boolean"}
                }
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 5,
                "uniqueItems": True
            },
            "favorites": {
                "type": "array",
                "contains": {"type": "string", "minLength": 3}
            },
            "addresses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["street", "city", "zipCode"],
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "zipCode": {"type": "string", "pattern": "^\\d{5}$"}
                    }
                }
            },
            "subscription": {
                "type": "object",
                "oneOf": [
                    {
                        "properties": {
                            "type": {"const": "free"},
                            "expirationDate": {"not": {"type": "string"}}
                        },
                        "required": ["type"]
                    },
                    {
                        "properties": {
                            "type": {"const": "premium"},
                            "expirationDate": {"type": "string", "format": "date"}
                        },
                        "required": ["type", "expirationDate"]
                    }
                ]
            },
            "configuration": {
                "type": "object",
                "allOf": [
                    {
                        "properties": {
                            "debug": {"type": "boolean"},
                            "timeout": {"type": "integer", "minimum": 1000}
                        }
                    },
                    {
                        "properties": {
                            "options": {"type": "object"}
                        }
                    }
                ]
            },
            "contact": {
                "dependentRequired": {
                    "phone": ["phoneType"],
                    "email": ["emailType"]
                },
                "properties": {
                    "phone": {"type": "string"},
                    "phoneType": {"enum": ["home", "work", "mobile"]},
                    "email": {"type": "string"},
                    "emailType": {"enum": ["personal", "work"]}
                }
            },
            "preferences": {
                "if": {
                    "properties": {"notifications": {"const": True}},
                    "required": ["notifications"]
                },
                "then": {
                    "required": ["notificationEmail"]
                },
                "properties": {
                    "notifications": {"type": "boolean"},
                    "notificationEmail": {"type": "string", "format": "email"}
                }
            }
        },
        "required": ["username", "email", "age", "role"],
        "patternProperties": {
            "^custom_": {"type": "string"}
        }
    }
    
    # Create a data object with various validation errors
    data = {
        "username": "user@123",  # Pattern error
        "email": "not-an-email",  # Format error
        "age": 16,  # Minimum error
        "score": 0,  # ExclusiveMinimum error
        "role": "superuser",  # Enum error
        "settings": {
            "theme": "blue",  # Enum error
            "fontSize": 14  # AdditionalProperties error
        },
        "tags": ["tag1", "tag1", "tag2"],  # UniqueItems error
        "favorites": [1, 2],  # Contains error
        "addresses": [
            {"street": "123 Main St", "zipCode": "1234"}  # Required error and pattern error
        ],
        "subscription": {
            "type": "premium"  # Missing required expirationDate
        },
        "configuration": {
            "debug": "yes",  # Type error
            "timeout": 500  # Minimum error
        },
        "contact": {
            "phone": "555-1234"  # Missing dependent required phoneType
        },
        "preferences": {
            "notifications": True  # Missing required notificationEmail due to if/then
        },
        "custom_1": 123  # Type error in patternProperties
    }
    
    # Create standard and human-friendly validators
    standard_validator = Draft202012Validator(schema)
    human_validator = create_human_validator(schema)
    
    # Collect standard errors
    standard_errors = list(standard_validator.iter_errors(data))
    
    # Collect human-friendly errors
    human_errors = list(human_validator.iter_errors(data))
    
    # Select some examples to show the difference
    example_pairs = []
    
    # Get a mapping from error paths to errors
    path_to_standard = {}
    for error in standard_errors:
        key = (error.validator, tuple(error.path))
        path_to_standard[key] = error
    
    # Match human errors with standard errors
    for human_error in human_errors:
        key = (human_error.validator, tuple(human_error.path))
        if key in path_to_standard:
            example_pairs.append((path_to_standard[key], human_error))
    
    # Show comparison of technical vs. human-friendly errors
    print("Comparison of technical vs. human-friendly errors:\n")
    for i, (technical, human) in enumerate(example_pairs[:10], 1):  # Show first 10 examples
        print(f"Example {i} - {technical.validator} validation:")
        print(f"  Technical: {technical}")
        print(f"  Human-friendly: {human}\n")
    
    # Show all human-friendly errors
    print("\nAll human-friendly validation errors:")
    for i, error in enumerate(sorted(human_errors, key=lambda e: str(e)), 1):
        print(f"{i}. {error}")


if __name__ == "__main__":
    print("=== Basic Usage ===")
    example_basic_usage()
    print("\n=== Converting Existing Errors ===")
    example_convert_existing_errors()
    print("\n=== Creating Human Validators ===")
    example_create_human_validator()
    print("\n=== Custom Error Handling ===")
    example_custom_error_handling()
    print("\n=== Patching All Validators ===")
    example_patch_all_validators()
    print("\n=== Error Tree ===")
    example_error_tree()
    print("\n=== Property Name Formatting ===")
    example_property_name_formatting()
    print("\n=== Comprehensive Validation Example ===")
    example_comprehensive_validation() 