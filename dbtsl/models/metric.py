from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, List, Optional, Union

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


@dataclass
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

    def _load_dimensions(self) -> Union[List[Dimension], Awaitable[List[Dimension]]]:
        return self._client.dimensions(metrics=[self.name])

    def _load_measures(self) -> Union[List[Measure], Awaitable[List[Measure]]]:
        return self._client.measures(metrics=[self.name])

    def _load_entities(self) -> Union[List[Entity], Awaitable[List[Entity]]]:
        return self._client.entities(metrics=[self.name])


class SyncMetric(Metric, ABC):
    """A metric with type annotations for sync lazy loading methods.

    At runtime this is just a regular Metric. Don't use this directly.
    """

    def load_dimensions(self) -> List[Dimension]:
        """Lazy load dimensions for this metric."""
        raise NotImplementedError()

    def load_measures(self) -> List[Measure]:
        """Lazy load measures for this metric."""
        raise NotImplementedError()

    def load_entities(self) -> List[Entity]:
        """Lazy load entities for this metric."""
        raise NotImplementedError()


class AsyncMetric(Metric, ABC):
    """A metric with type annotations for async lazy loading methods.

    At runtime this is just a regular Metric. Don't use this directly.
    """

    async def load_dimensions(self) -> List[Dimension]:
        """Lazy load dimensions for this metric."""
        raise NotImplementedError()

    async def load_measures(self) -> List[Measure]:
        """Lazy load measures for this metric."""
        raise NotImplementedError()

    async def load_entities(self) -> List[Entity]:
        """Lazy load entities for this metric."""
        raise NotImplementedError()
