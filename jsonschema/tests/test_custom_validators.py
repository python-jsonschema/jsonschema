import unittest
from jsonschema import ValidationError
from jsonschema.custom_validators import custom_validate


class TestCustomValidator(unittest.TestCase):

    def setUp(self):
        # Sample schema for various test cases
        self.schema = {
            "type": "object",
            "properties": {
                "Sodium": {
                    "type": "integer",
                    "description": "Sodium level in mg."
                },
                "Carbohydrate": {
                    "type": "string",
                    "enum": ["Low", "High"]
                },
                "FluidRestriction": {
                    "type": "integer",
                    "description": "Fluid restriction in cc/24 hours."
                },
                "Diet": {
                    "type": "object",
                    "properties": {
                        "HighProtein": {
                            "type": "integer"
                        },
                        "LowProtein": {
                            "type": "integer"
                        },
                        "DietType": {
                            "type": "string",
                            "enum": ["Vegetarian", "Non-Vegetarian", "Vegan"]
                        }
                    },
                    "additionalProperties": False
                }
            },
            "required": ["Sodium"],
            "additionalProperties": False
        }

    def test_valid_instance(self):
        instance = {
            "Sodium": 140,
            "Carbohydrate": "Low",
            "FluidRestriction": 1500,
            "Diet": {
                "HighProtein": 100,
                "DietType": "Vegan"
            }
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_missing_required_property(self):
        instance = {
            "Carbohydrate": "Low",
            "FluidRestriction": 1500
        }
        with self.assertRaises(ValidationError):
            custom_validate(instance, self.schema)

    def test_enum_with_nullable_valid(self):
        instance = {
            "Sodium": 140,
            "Carbohydrate": None  # Enum property is None
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_enum_with_nullable_invalid(self):
        instance = {
            "Sodium": 140,
            "Carbohydrate": "Medium"  # Not in the enum
        }
        with self.assertRaises(ValidationError):
            custom_validate(instance, self.schema)

    def test_enum_subproperty_with_nullable_valid(self):
        instance = {
            "Sodium": 140,
            "Diet": {
                "DietType": None  # Enum subproperty is None
            }
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_enum_subproperty_with_nullable_invalid(self):
        instance = {
            "Sodium": 140,
            "Diet": {
                "DietType": "Keto"  # Not in the enum for DietType
            }
        }
        with self.assertRaises(ValidationError):
            custom_validate(instance, self.schema)

    def test_ignore_none_for_missing_properties(self):
        instance = {
            "Sodium": 140,
            "Carbohydrate": None
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_reject_additional_properties(self):
        instance = {
            "Sodium": 140,
            "Carbohydrate": "Low",
            "ExtraField": "NotAllowed"  # Extra field not in the schema
        }
        with self.assertRaises(ValidationError):
            custom_validate(instance, self.schema)

    def test_allow_missing_non_required_fields(self):
        instance = {
            "Sodium": 140  # Only the required field is present
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_allow_none_type_handling(self):
        # Test with None as the entire instance (should pass)
        instance = None
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_nested_object_with_additional_properties(self):
        # Nested schema with additionalProperties = False
        nested_schema = {
            "type": "object",
            "properties": {
                "Diet": {
                    "type": "object",
                    "properties": {
                        "Sodium": {"type": "integer"},
                        "FluidRestriction": {"type": "integer"}
                    },
                    "additionalProperties": False
                }
            }
        }

        valid_instance = {
            "Diet": {
                "Sodium": 140,
                "FluidRestriction": 1500
            }
        }

        invalid_instance = {
            "Diet": {
                "Sodium": 140,
                "ExtraField": "NotAllowed"  # Additional field in nested object
            }
        }

        try:
            custom_validate(valid_instance, nested_schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly for valid instance!")

        with self.assertRaises(ValidationError):
            custom_validate(invalid_instance, nested_schema)

    def test_nested_object_none_valid(self):
        # Test with None as a nested object
        instance = {
            "Sodium": 140,
            "Diet": None  # Should be valid since Diet is not required
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_nested_object_missing_valid(self):
        # Test with missing nested object
        instance = {
            "Sodium": 140  # Diet object is missing but should be valid
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_exclude_any_field(self):
        # Test that any non-required field can be excluded without raising an error
        instance = {
            "Sodium": 140  # Only the required field is present
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

    def test_enum_field_nullable_and_missing(self):
        # Test that a nullable enum field can be missing or None
        instance = {
            "Sodium": 140  # Carbohydrate is missing
        }
        try:
            custom_validate(instance, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")

        instance_with_none = {
            "Sodium": 140,
            "Carbohydrate": None  # Carbohydrate is explicitly set to None
        }
        try:
            custom_validate(instance_with_none, self.schema)
        except ValidationError:
            self.fail("custom_validate raised ValidationError unexpectedly!")


if __name__ == "__main__":
    unittest.main() 