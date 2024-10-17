from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

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
