from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, TypedDict, Union


class GroupByType(Enum):
    """The type of a group_by, i.e a dimension or an entity."""

    DIMENSION = "dimension"
    TIME_DIMENSION = "time_dimension"
    ENTITY = "entity"


@dataclass(frozen=True)
class GroupByParam:
    """Parameter for a group_by, i.e a dimension or an entity."""

    name: str
    type: GroupByType
    grain: Optional[str]


@dataclass(frozen=True)
class OrderByMetric:
    """Spec for ordering by a metric."""

    name: str
    descending: bool = False


@dataclass(frozen=True)
class OrderByGroupBy:
    """Spec for ordering by a group_by, i.e a dimension or an entity.

    Not specifying a grain will defer the grain choice to the server.
    """

    name: str
    grain: Optional[str]
    descending: bool = False


OrderBySpec = Union[OrderByMetric, OrderByGroupBy]


class QueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.query`.

    metrics/group_by and saved_query are mutually exclusive.
    """

    saved_query: str
    metrics: List[str]
    group_by: List[Union[GroupByParam, str]]
    limit: int
    order_by: List[Union[OrderBySpec, str]]
    where: List[str]
    read_cache: bool


@dataclass(frozen=True)
class AdhocQueryParametersStrict:
    """The parameters of an adhoc query, strictly validated."""

    metrics: Optional[List[str]]
    group_by: Optional[List[Union[GroupByParam, str]]]
    limit: Optional[int]
    order_by: Optional[List[OrderBySpec]]
    where: Optional[List[str]]
    read_cache: bool


@dataclass(frozen=True)
class SavedQueryQueryParametersStrict:
    """The parameters of a query that uses a saved query, strictly validated."""

    saved_query: str
    limit: Optional[int]
    order_by: Optional[List[OrderBySpec]]
    where: Optional[List[str]]
    read_cache: bool


def validate_order_by(
    known_metrics: List[str],
    known_group_bys: List[Union[str, GroupByParam]],
    clause: Union[OrderBySpec, str],
) -> OrderBySpec:
    """Validate an order by clause like `-metric_name`."""
    if isinstance(clause, OrderByMetric) or isinstance(clause, OrderByGroupBy):
        return clause

    descending = clause.startswith("-")
    if descending or clause.startswith("+"):
        clause = clause[1:]

    if clause in known_metrics:
        return OrderByMetric(name=clause, descending=descending)

    normalized_known_group_bys = [
        known_group_by.name if isinstance(known_group_by, GroupByParam) else known_group_by
        for known_group_by in known_group_bys
    ]
    if clause in normalized_known_group_bys or clause == "metric_time":
        return OrderByGroupBy(name=clause, descending=descending, grain=None)

    # TODO: make this error less strict when server supports order_by type inference.
    raise ValueError(
        f"Cannot determine if the specified order_by clause ({clause}) is a metric or a dimension/entity. "
        "If you're running an adhoc query, make sure the order_by is in `metrics` or `group_by`. "
        "If you're using saved queries, please explicitly specify what you want by using "
        "`dbtsl.OrderByMetric` or `dbtsl.OrderByGroupBy` instead of a string."
    )


def validate_query_parameters(
    params: QueryParameters,
) -> Union[AdhocQueryParametersStrict, SavedQueryQueryParametersStrict]:
    """Validate a dict that should be QueryParameters."""
    is_saved_query = "saved_query" in params
    is_adhoc_query = "metrics" in params or "group_by" in params
    if is_saved_query and is_adhoc_query:
        raise ValueError(
            "metrics/group_by and saved_query are mutually exclusive, "
            "since, by definition, saved queries already include "
            "metrics and group_by."
        )

    if not is_saved_query and not is_adhoc_query:
        raise ValueError("You must specify one of: saved_query, metrics/group_by.")

    order_by: Optional[List[OrderBySpec]] = None
    if "order_by" in params:
        known_metrics = params.get("metrics", [])
        known_group_bys = params.get("group_by", [])

        order_by = [validate_order_by(known_metrics, known_group_bys, clause) for clause in params["order_by"]]

    limit = params.get("limit")
    where = params.get("where")
    read_cache = params.get("read_cache", True)

    if is_saved_query:
        return SavedQueryQueryParametersStrict(
            saved_query=params["saved_query"],
            limit=limit,
            order_by=order_by,
            where=where,
            read_cache=read_cache,
        )

    return AdhocQueryParametersStrict(
        metrics=params.get("metrics"),
        group_by=params.get("group_by"),
        limit=limit,
        order_by=order_by,
        where=where,
        read_cache=read_cache,
    )


class DimensionValuesQueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.dimension_values`."""

    metrics: List[str]
    group_by: str
