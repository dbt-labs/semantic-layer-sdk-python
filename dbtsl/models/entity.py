from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dbtsl.models.base import BaseModel, FlexibleEnumMeta, GraphQLFragmentMixin


class EntityType(Enum, metaclass=FlexibleEnumMeta):
    """All supported entity types."""

    UNKNOWN = "UNKNOWN"
    FOREIGN = "FOREIGN"
    NATURAL = "NATURAL"
    PRIMARY = "PRIMARY"
    UNIQUE = "UNIQUE"


@dataclass
class Entity(BaseModel, GraphQLFragmentMixin):
    """An entity."""

    name: str
    description: Optional[str]
    type: EntityType
    role: str
    expr: str
