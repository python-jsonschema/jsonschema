import os

from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), "README.rst")) as readme:
    long_description = readme.read()

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

extras_require = {
    "format" : ["rfc3987", "strict-rfc3339", "webcolors"],
    ":python_version=='2.7'": ["functools32"],
}

setup(
    name="jsonschema",
    packages=["jsonschema", "jsonschema.tests"],
    package_data={"jsonschema": ["schemas/*.json"]},
    setup_requires=["vcversioner>=2.16.0.0"],
    extras_require=extras_require,
    author="Julian Berman",
    author_email="Julian@GrayVines.com",
    classifiers=classifiers,
    description="An implementation of JSON Schema validation for Python",
    license="MIT",
    long_description=long_description,
    url="http://github.com/Julian/jsonschema",
    entry_points={"console_scripts": ["jsonschema = jsonschema.cli:main"]},
    vcversioner={"version_module_paths" : ["jsonschema/_version.py"]},
)
