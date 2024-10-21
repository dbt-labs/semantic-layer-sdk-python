from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from dbtsl.models.base import BaseModel, GraphQLFragmentMixin
from dbtsl.models.time import TimeGranularity


class DimensionType(str, Enum):
    """The type of a dimension."""

    CATEGORICAL = "CATEGORICAL"
    TIME = "TIME"


QUERYABLE_GRANULARITIES_DEPRECATION = (
    "Since the introduction of custom time granularities, `Dimension.queryable_granularities` is deprecated. "
    "Use `queryable_time_granularities` instead."
)


@dataclass(frozen=True)
class Dimension(BaseModel, GraphQLFragmentMixin):
    """A metric dimension."""

    name: str
    qualified_name: str
    description: Optional[str]
    type: DimensionType
    label: Optional[str]
    is_partition: bool
    expr: Optional[str]
    queryable_granularities: List[TimeGranularity] = field(
        metadata={BaseModel.DEPRECATED: QUERYABLE_GRANULARITIES_DEPRECATION}
    )
    queryable_time_granularities: List[str]
