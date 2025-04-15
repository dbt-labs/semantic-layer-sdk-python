from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
from typing import List, Optional

from dbtsl.models.base import NOT_LAZY_META as NOT_LAZY
from dbtsl.models.base import BaseModel, FlexibleEnumMeta, GraphQLFragmentMixin
from dbtsl.models.time import DatePart, TimeGranularity


class ExportDestinationType(Enum, metaclass=FlexibleEnumMeta):
    """All kinds of export destinations."""

    UNKNOWN = "UNKNOWN"
    TABLE = "TABLE"
    VIEW = "VIEW"


@dataclass
class ExportConfig(BaseModel, GraphQLFragmentMixin):
    """A saved query export config."""

    alias: Optional[str]
    schema: Optional[str]
    export_as: ExportDestinationType


@dataclass
class Export(BaseModel, GraphQLFragmentMixin):
    """A saved query export."""

    name: str
    config: ExportConfig


@dataclass
class SavedQueryMetricParam(BaseModel, GraphQLFragmentMixin):
    """The metric param of a saved query."""

    name: str


GRAIN_DEPRECATION = (
    "Since the introduction of custom time granularities, `SavedQueryGroupByParam.grain` is deprecated. "
    "Use `time_granularity` instead."
)


@dataclass
class SavedQueryGroupByParam(BaseModel, GraphQLFragmentMixin):
    """The groupBy param of a saved query."""

    name: str
    grain: Optional[TimeGranularity] = dc_field(metadata={BaseModel.DEPRECATED: GRAIN_DEPRECATION})
    time_granularity: Optional[str]
    date_part: Optional[DatePart]


@dataclass
class SavedQueryWhereParam(BaseModel, GraphQLFragmentMixin):
    """The where param of a saved query."""

    @classmethod
    def gql_model_name(cls) -> str:  # noqa: D102
        return "WhereFilter"

    where_sql_template: str


@dataclass
class SavedQueryQueryParams(BaseModel, GraphQLFragmentMixin):
    """The parameters of a saved query."""

    metrics: List[SavedQueryMetricParam] = dc_field(metadata=NOT_LAZY)
    group_by: List[SavedQueryGroupByParam] = dc_field(metadata=NOT_LAZY)
    where: Optional[SavedQueryWhereParam] = dc_field(metadata=NOT_LAZY)


@dataclass
class SavedQuery(BaseModel, GraphQLFragmentMixin):
    """A saved query."""

    name: str
    description: Optional[str]
    label: Optional[str]
    query_params: SavedQueryQueryParams
    exports: List[Export] = dc_field(metadata=NOT_LAZY)
