from jsonschema.compat import PY36

if PY36:
    from .async_validators import *
