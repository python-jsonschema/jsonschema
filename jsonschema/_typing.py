"""
Type aliases and utilities to help manage `typing` usage and type annotations.
"""

from collections.abc import Mapping, Sequence
import typing

Schema = Mapping[str, typing.Any]

JsonObject = Mapping[str, typing.Any]

JsonValue = typing.Union[
    JsonObject, Sequence[typing.Any], str, int, float, bool, None
]
