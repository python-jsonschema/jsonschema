from jsonschema.exceptions import ValidationError


class Required(ValidationError):
    def __init__(self, property_name):
        ValidationError.__init__(
            self,
            message=f"{property_name!r} is a required property",
        )

        self.property_name = property_name
