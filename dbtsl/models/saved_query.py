from dataclasses import dataclass
from typing import Optional

from dbtsl.models.base import BaseModel, GraphQLFragmentMixin


@dataclass(frozen=True)
class SavedQuery(BaseModel, GraphQLFragmentMixin):
    """A saved query."""

    name: str
    description: Optional[str]
    label: Optional[str]
