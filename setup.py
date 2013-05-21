from distutils.core import setup

from jsonschema import __version__


with open("README.rst") as readme:
    long_description = readme.read()


classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.1",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]


setup(
    name="jsonschema",
    version=__version__,
    packages=["jsonschema", "jsonschema.tests"],
    package_data={'jsonschema': ['schemas/*.json']},
    author="Julian Berman",
    author_email="Julian@GrayVines.com",
    classifiers=classifiers,
    description="An implementation of JSON Schema validation for Python",
    license="MIT",
    long_description=long_description,
    url="http://github.com/Julian/jsonschema",
)
