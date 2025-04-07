from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from dbtsl.models.base import NOT_LAZY_META as NOT_LAZY
from dbtsl.models.base import BaseModel, FlexibleEnumMeta, GraphQLFragmentMixin
from dbtsl.models.dimension import Dimension
from dbtsl.models.entity import Entity
from dbtsl.models.measure import Measure
from dbtsl.models.time import TimeGranularity


class MetricType(Enum, metaclass=FlexibleEnumMeta):
    """The type of a Metric."""

    UNKNOWN = "UNKNOWN"
    SIMPLE = "SIMPLE"
    RATIO = "RATIO"
    CUMULATIVE = "CUMULATIVE"
    DERIVED = "DERIVED"
    CONVERSION = "CONVERSION"


QUERYABLE_GRANULARITIES_DEPRECATION = (
    "Since the introduction of custom time granularities, `Metric.queryable_granularities` is deprecated. "
    "Use `queryable_time_granularities` instead."
)


@dataclass(frozen=True)
class Metric(BaseModel, GraphQLFragmentMixin):
    """A metric."""

    name: str
    description: Optional[str]
    type: MetricType
    queryable_granularities: List[TimeGranularity] = field(
        metadata={
            BaseModel.DEPRECATED: QUERYABLE_GRANULARITIES_DEPRECATION,
        }
    )
    queryable_time_granularities: List[str] = field(metadata=NOT_LAZY)
    label: str
    requires_metric_time: bool

    dimensions: List[Dimension] = field(default_factory=list)
    measures: List[Measure] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
