from typing import List, TypedDict


class QueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.query`.

    metrics/group_by and saved_query are mutually exclusive.
    """

    saved_query: str
    metrics: List[str]
    group_by: List[str]
    limit: int
    order_by: List[str]
    where: List[str]
    read_cache: bool


def validate_query_parameters(params: QueryParameters) -> None:
    """Validate a dict that should be QueryParameters."""
    is_saved_query = "saved_query" in params
    is_adhoc_query = "metrics" in params or "group_by" in params
    if is_saved_query and is_adhoc_query:
        raise ValueError(
            "metrics/group_by and saved_query are mutually exclusive, "
            "since, by definition, saved queries already include "
            "metrics and group_by."
        )

    if "metrics" in params and len(params["metrics"]) == 0:
        raise ValueError("You need to specify at least one metric.")

    if "group_by" in params and len(params["group_by"]) == 0:
        raise ValueError("You need to specify at least one dimension to group by.")


class DimensionValuesQueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.dimension_values`."""

    metrics: List[str]
    group_by: str
