"""
Tests for human-friendly error messages.
"""
from unittest import TestCase

from jsonschema import validators, human_validate, humanize_error
from jsonschema.exceptions import ValidationError


class TestHumanFriendlyErrors(TestCase):
    """Test the human-friendly error message functionality."""

    def test_type_error(self):
        """Test for human-friendly type error messages."""
        instance = 5
        schema = {"type": "string"}
        
        # Get the default error message
        try:
            validators.validate(instance, schema)
        except ValidationError as e:
            default_message = str(e)
        
        # Get the human-friendly error message
        try:
            human_validate(instance, schema)
        except ValidationError as e:
            human_message = str(e)
        
        self.assertIn("5 is not of type 'string'", default_message)
        self.assertEqual("Expected text, but got 5", human_message)
    
    def test_required_error(self):
        """Test for human-friendly required error messages."""
        instance = {}
        schema = {"required": ["name"]}
        
        # Get the default error message
        try:
            validators.validate(instance, schema)
        except ValidationError as e:
            default_message = str(e)
        
        # Get the human-friendly error message
        try:
            human_validate(instance, schema)
        except ValidationError as e:
            human_message = str(e)
        
        self.assertIn("'name' is a required property", default_message)
        self.assertEqual("Missing required field: 'name'", human_message)
    
    def test_minimum_error(self):
        """Test for human-friendly minimum error messages."""
        instance = 5
        schema = {"minimum": 10}
        
        # Get the default error message
        try:
            validators.validate(instance, schema)
        except ValidationError as e:
            default_message = str(e)
        
        # Get the human-friendly error message
        try:
            human_validate(instance, schema)
        except ValidationError as e:
            human_message = str(e)
        
        self.assertIn("5 is less than the minimum of 10", default_message)
        self.assertEqual("The value must be at least 10, but was 5", human_message)
    
    def test_enum_error(self):
        """Test for human-friendly enum error messages."""
        instance = "red"
        schema = {"enum": ["blue", "green", "yellow"]}
        
        # Get the default error message
        try:
            validators.validate(instance, schema)
        except ValidationError as e:
            default_message = str(e)
        
        # Get the human-friendly error message
        try:
            human_validate(instance, schema)
        except ValidationError as e:
            human_message = str(e)
        
        self.assertIn("'red' is not one of ['blue', 'green', 'yellow']", default_message)
        self.assertEqual('The value must be one of: "blue", "green", "yellow"', human_message)
    
    def test_format_error(self):
        """Test for human-friendly format error messages."""
        instance = "not-an-email"
        schema = {"format": "email"}
        
        # Create a validator with format checking
        validator = validators.Draft202012Validator(schema, format_checker=validators.Draft202012Validator.FORMAT_CHECKER)
        human_validator = validators.Draft202012Validator(schema, format_checker=validators.Draft202012Validator.FORMAT_CHECKER)
        human_validator = validators.enable_human_errors(human_validator.__class__)(schema, format_checker=validators.Draft202012Validator.FORMAT_CHECKER)
        
        # Get the default error message
        default_errors = list(validator.iter_errors(instance))
        if default_errors:
            default_message = str(default_errors[0])
        else:
            default_message = ""
        
        # Get the human-friendly error message
        human_errors = list(human_validator.iter_errors(instance))
        if human_errors:
            human_message = str(human_errors[0])
        else:
            human_message = ""
        
        self.assertIn("is not a", default_message)
        self.assertIn("email", default_message)
        self.assertEqual("The value must be a valid email address", human_message)
    
    def test_humanize_error_function(self):
        """Test the humanize_error function directly."""
        instance = 5
        schema = {"type": "string"}
        
        try:
            validators.validate(instance, schema)
        except ValidationError as e:
            default_message = str(e)
            human_message = humanize_error(e)
        
        self.assertIn("5 is not of type 'string'", default_message)
        self.assertEqual("Expected text, but got 5", human_message) 