"""The models used for the SDK.

NOTE: this will be deleted in the future and will be replaced by
generated code from our GraphQL schema.
"""

from .base import BaseModel, GraphQLFragmentMixin
from .dimension import Dimension, DimensionType
from .entity import Entity, EntityType
from .environment import EnvironmentInfo, SqlDialect, SqlEngine
from .measure import AggregationType, Measure
from .metric import AsyncMetric, Metric, MetricType, SyncMetric
from .query import QueryResult
from .saved_query import (
    Export,
    ExportConfig,
    ExportDestinationType,
    SavedQuery,
    SavedQueryGroupByParam,
    SavedQueryMetricParam,
    SavedQueryQueryParams,
    SavedQueryWhereParam,
)
from .time import DatePart, TimeGranularity

# Only importing this so it registers aliases
_ = QueryResult

BaseModel._register_subclasses()  # pyright: ignore[reportPrivateUsage]
GraphQLFragmentMixin._register_subclasses()  # pyright: ignore[reportPrivateUsage]

__all__ = [
    "AggregationType",
    "AsyncMetric",
    "DatePart",
    "Dimension",
    "DimensionType",
    "Entity",
    "EntityType",
    "EnvironmentInfo",
    "Export",
    "ExportConfig",
    "ExportDestinationType",
    "Measure",
    "Metric",
    "MetricType",
    "SavedQuery",
    "SavedQuery",
    "SavedQueryGroupByParam",
    "SavedQueryMetricParam",
    "SavedQueryQueryParams",
    "SavedQueryWhereParam",
    "SqlDialect",
    "SqlEngine",
    "SyncMetric",
    "TimeGranularity",
]
