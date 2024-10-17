from dataclasses import InitVar, dataclass
from enum import Enum
from typing import List, Optional

from typing_extensions import override

from dbtsl.models.base import BaseModel, GraphQLFragmentMixin
from dbtsl.models.time import Grain


class DimensionType(str, Enum):
    """The type of a dimension."""

    CATEGORICAL = "CATEGORICAL"
    TIME = "TIME"


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
    queryable_granularities: List[Grain]

    queryable_time_granilarities: InitVar[List[str]]

    @override
    @classmethod
    def extra_gql_fields(cls) -> List[str]:
        return ["queryableTimeGranularities"]

    def __post_init__(self, queryable_time_granilarities: List[str]) -> None:
        """Initialize queryable_granularities from queryable_time_granilarities.

        In GraphQL, the standard time granularities are in `queryableGranularities`
        but the custom time granularities are in `queryableTimeGranularities`.

        Here' we're setting `queryable_time_granilarities` as an `InitVar`, and
        making `queryable_granularities` contain both standard and non standard
        `Grain`s.

        This method is what merges both of them.
        """
        self.queryable_granularities.extend(queryable_time_granilarities)
