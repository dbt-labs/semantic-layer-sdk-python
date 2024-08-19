from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from dbtsl.models.base import BaseModel, GraphQLFragmentMixin
from dbtsl.models.time import DatePart, TimeGranularity


class ExportDestinationType(str, Enum):
    """All kinds of export destinations."""

    TABLE = "TABLE"
    VIEW = "VIEW"


@dataclass(frozen=True)
class ExportConfig(BaseModel, GraphQLFragmentMixin):
    """A saved query export config."""

    alias: Optional[str]
    schema: Optional[str]
    export_as: ExportDestinationType


@dataclass(frozen=True)
class Export(BaseModel, GraphQLFragmentMixin):
    """A saved query export."""

    name: str
    config: ExportConfig


@dataclass(frozen=True)
class SavedQueryMetricParam(BaseModel, GraphQLFragmentMixin):
    """The metric param of a saved query."""

    name: str


@dataclass(frozen=True)
class SavedQueryGroupByParam(BaseModel, GraphQLFragmentMixin):
    """The groupBy param of a saved query."""

    name: str
    grain: Optional[TimeGranularity]
    date_part: Optional[DatePart]


@dataclass(frozen=True)
class SavedQueryWhereParam(BaseModel, GraphQLFragmentMixin):
    """The where param of a saved query."""

    @classmethod
    def gql_model_name(cls) -> str:  # noqa: D102
        return "WhereFilter"

    where_sql_template: str


@dataclass(frozen=True)
class SavedQueryQueryParams(BaseModel, GraphQLFragmentMixin):
    """The parameters of a saved query."""

    metrics: List[SavedQueryMetricParam]
    group_by: List[SavedQueryGroupByParam]
    where: Optional[SavedQueryWhereParam]


@dataclass(frozen=True)
class SavedQuery(BaseModel, GraphQLFragmentMixin):
    """A saved query."""

    name: str
    description: Optional[str]
    label: Optional[str]
    query_params: SavedQueryQueryParams
    exports: List[Export]
