from distutils.core import setup

from jsonschema import __version__


setup(
    name="jsonschema",
    version=__version__,
    py_modules=["jsonschema"],
    author="Julian Berman",
    author_email="Julian@GrayVines.com",
    description="An implementation of JSON-Schema validation for Python",
    license="MIT/X",
    url="http://github.com/Julian/jsonschema",
)
