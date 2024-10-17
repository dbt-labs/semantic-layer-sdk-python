from dataclasses import dataclass
from typing import List, Optional, TypedDict, Union

from dbtsl.models.time import Grain


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
    grain: Optional[Grain]
    descending: bool = False


OrderBySpec = Union[OrderByMetric, OrderByGroupBy]


class QueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.query`.

    metrics/group_by and saved_query are mutually exclusive.
    """

    saved_query: str
    metrics: List[str]
    group_by: List[str]
    limit: int
    order_by: List[Union[OrderBySpec, str]]
    where: List[str]
    read_cache: bool


@dataclass(frozen=True)
class AdhocQueryParametersStrict:
    """The parameters of an adhoc query, strictly validated."""

    metrics: List[str]
    group_by: Optional[List[str]]
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
    known_metrics: List[str], known_group_bys: List[str], clause: Union[OrderBySpec, str]
) -> OrderBySpec:
    """Validate an order by clause like `-metric_name`."""
    if isinstance(clause, OrderByMetric) or isinstance(clause, OrderByGroupBy):
        return clause

    descending = clause.startswith("-")
    if descending or clause.startswith("+"):
        clause = clause[1:]

    if clause in known_metrics:
        return OrderByMetric(name=clause, descending=descending)

    if clause in known_group_bys or clause == "metric_time":
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

    shared_params = {
        "limit": params.get("limit"),
        "order_by": order_by,
        "where": params.get("where"),
        "read_cache": params.get("read_cache", True),
    }

    if is_saved_query:
        return SavedQueryQueryParametersStrict(
            saved_query=params["saved_query"],
            **shared_params,
        )

    if "metrics" not in params or len(params["metrics"]) == 0:
        raise ValueError("You need to specify at least one metric.")

    return AdhocQueryParametersStrict(
        metrics=params["metrics"],
        group_by=params.get("group_by"),
        **shared_params,
    )


class DimensionValuesQueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.dimension_values`."""

    metrics: List[str]
    group_by: str
