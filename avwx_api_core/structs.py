"""
Parameter dataclasses
"""

# pylint: disable=missing-class-docstring

from dataclasses import dataclass


@dataclass
class Params:
    format: str
    remove: list[str]
    filter: list[str]


DEFAULT_PARAMS = Params(format="json", remove=[], filter=[])
