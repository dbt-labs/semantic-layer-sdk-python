from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dbtsl.models.base import BaseModel, FlexibleEnumMeta, GraphQLFragmentMixin


class AggregationType(Enum, metaclass=FlexibleEnumMeta):
    """All supported aggregation functions."""

    UNKNOWN = "UNKNOWN"
    SUM = "SUM"
    MIN = "MIN"
    MAX = "MAX"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    SUM_BOOLEAN = "SUM_BOOLEAN"
    AVERAGE = "AVERAGE"
    PERCENTILE = "PERCENTILE"
    MEDIAN = "MEDIAN"
    COUNT = "COUNT"


@dataclass
class Measure(BaseModel, GraphQLFragmentMixin):
    """A measure."""

    name: str
    agg_time_dimension: Optional[str]
    agg: AggregationType
    expr: str
