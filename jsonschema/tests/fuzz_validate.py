import sys

from hypothesis import given
from hypothesis import strategies as st
import atheris

import jsonschema

PRIM = st.one_of(
    st.booleans(),
    st.integers(min_value=-(2 ** 63), max_value=2 ** 63 - 1),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
)
DICT = st.recursive(
    base=st.dictionaries(st.text(), PRIM),
    extend=lambda inner: st.dictionaries(st.text(), inner),
)


@given(obj1=DICT, obj2=DICT)
def test_schemas(obj1, obj2):
    try:
        jsonschema.validate(instance=obj1, schema=obj2)
    except jsonschema.exceptions.ValidationError:
        None
    except jsonschema.exceptions.SchemaError:
        None


def main():
    atheris.Setup(sys.argv,
                  test_schemas.hypothesis.fuzz_one_input,
                  enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
