"""The models used for the SDK.

NOTE: this will be deleted in the future and will be replaced by
generated code from our GraphQL schema.
"""

from .base import BaseModel
from .dimension import Dimension, DimensionType
from .entity import Entity, EntityType
from .measure import AggregationType, Measure
from .metric import Metric, MetricType
from .query import QueryResult
from .time_granularity import TimeGranularity

# Only importing this so it registers aliases
_ = QueryResult

BaseModel._apply_aliases()

__all__ = [
    "AggregationType",
    "Dimension",
    "DimensionType",
    "Entity",
    "EntityType",
    "Measure",
    "Metric",
    "MetricType",
    "TimeGranularity",
]
