import os.path
from setuptools import setup
import sys

# Load __version__ info globals without importing anything
with open(
    os.path.join(os.path.dirname(__file__), 'jsonschema', 'version.py')
) as fh:
    exec(fh.read())

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
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

install_requires = []

if sys.version_info < (3, 2):
    install_requires.append('repoze.lru >= 0.6')

setup(
    name="jsonschema",
    version=__version__,
    packages=["jsonschema", "jsonschema.tests"],
    package_data={"jsonschema": ["schemas/*.json"]},
    author="Julian Berman",
    author_email="Julian@GrayVines.com",
    classifiers=classifiers,
    description="An implementation of JSON Schema validation for Python",
    license="MIT",
    long_description=long_description,
    url="http://github.com/Julian/jsonschema",
    entry_points={"console_scripts": ["jsonschema = jsonschema.cli:main"]},
    install_requires=install_requires,
)
