from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dbtsl.models.base import BaseModel, GraphQLFragmentMixin


class EntityType(str, Enum):
    """All supported entity types."""

    FOREIGN = "FOREIGN"
    NATURAL = "NATURAL"
    PRIMARY = "PRIMARY"
    UNIQUE = "UNIQUE"


@dataclass(frozen=True)
class Entity(BaseModel, GraphQLFragmentMixin):
    """An entity."""

    name: str
    description: Optional[str]
    type: EntityType
    role: str
    expr: str
