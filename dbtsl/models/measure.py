from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from mashumaro import DataClassDictMixin, field_options


class AggregationType(str, Enum):
    """All supported aggregation functions."""

    SUM = "SUM"
    MIN = "MIN"
    MAX = "MAX"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    SUM_BOOLEAN = "SUM_BOOLEAN"
    AVERAGE = "AVERAGE"
    PERCENTILE = "PERCENTILE"
    MEDIAN = "MEDIAN"
    COUNT = "COUNT"


@dataclass(frozen=True)
class Measure(DataClassDictMixin):
    """A measure."""

    name: str
    agg_time_dimension: Optional[str] = field(metadata=field_options(alias="aggTimeDimension"))
    agg: AggregationType
    expr: str
