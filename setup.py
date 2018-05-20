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
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

setup(
    name="jsonschema",
    classifiers=classifiers,
    description="An implementation of JSON Schema validation for Python",
    license="MIT",
    long_description=long_description,
    url="http://github.com/Julian/jsonschema",

    author="Julian Berman",
    author_email="Julian@GrayVines.com",

    setup_requires=["setuptools_scm"],
    use_scm_version=True,

    install_requires=[
        "attrs>=17.4.0",
        "pyrsistent>=0.14.0",
        "six>=1.11.0",
        "functools32;python_version<'3'",
    ],
    extras_require={
        "format": [
            "jsonpointer>1.13",
            "rfc3987",
            "strict-rfc3339",
            "webcolors",
        ],
    },

    packages=["jsonschema", "jsonschema.tests"],
    package_data={"jsonschema": ["schemas/*.json"]},

    entry_points={"console_scripts": ["jsonschema = jsonschema.cli:main"]},
)
