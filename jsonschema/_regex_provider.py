import re

from jsonschema.protocols import RegexProvider


class PythonRegexProvider(RegexProvider):
    raises = (re.error,)
    compile = staticmethod(re.compile)  # type: ignore[assignment]
    search = staticmethod(re.search)  # type: ignore[assignment]
