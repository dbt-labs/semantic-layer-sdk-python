from dataclasses import dataclass
from enum import Enum

from dbtsl.models.base import BaseModel, GraphQLFragmentMixin


class DimensionType(str, Enum):
    """The type of a dimension."""

    CATEGORICAL = "CATEGORICAL"
    TIME = "TIME"


@dataclass(frozen=True)
class Dimension(BaseModel, GraphQLFragmentMixin):
    """A metric dimension."""

    name: str
    description: str
    type: DimensionType
