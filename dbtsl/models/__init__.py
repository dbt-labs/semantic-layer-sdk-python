"""The models used for the SDK.

NOTE: this will be deleted in the future and will be replaced by
generated code from our GraphQL schema.
"""

from .base import BaseModel
from .dimension import Dimension, DimensionType
from .entity import Entity, EntityType
from .measure import AggregationType, Measure
from .metric import Metric, MetricType

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
]
