from typing import List, TypedDict


class QueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.query`."""

    metrics: List[str]
    group_by: List[str]
    limit: int
    order_by: List[str]
    where: List[str]
    read_cache: bool


class DimensionValuesQueryParameters(TypedDict, total=False):
    """The parameters of `semantic_layer.dimension_values`."""

    metrics: List[str]
    group_by: str
