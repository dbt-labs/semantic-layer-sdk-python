from dataclasses import dataclass
from enum import Enum

from mashumaro import DataClassDictMixin


class DimensionType(str, Enum):
    """The type of a dimension."""

    CATEGORICAL = "CATEGORICAL"
    TIME = "TIME"


@dataclass(frozen=True)
class Dimension(DataClassDictMixin):
    """A metric dimension."""

    name: str
    description: str
    type: DimensionType
