from dataclasses import InitVar, dataclass
from enum import Enum
from typing import List, Optional

from typing_extensions import override

from dbtsl.models.base import BaseModel, GraphQLFragmentMixin
from dbtsl.models.dimension import Dimension
from dbtsl.models.entity import Entity
from dbtsl.models.measure import Measure
from dbtsl.models.time import Grain


class MetricType(str, Enum):
    """The type of a Metric."""

    SIMPLE = "SIMPLE"
    RATIO = "RATIO"
    CUMULATIVE = "CUMULATIVE"
    DERIVED = "DERIVED"
    CONVERSION = "CONVERSION"


@dataclass(frozen=True)
class Metric(BaseModel, GraphQLFragmentMixin):
    """A metric."""

    name: str
    description: Optional[str]
    type: MetricType
    dimensions: List[Dimension]
    measures: List[Measure]
    entities: List[Entity]
    queryable_granularities: List[Grain]
    label: str
    requires_metric_time: bool

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
