from typing import List, TypedDict

from typing_extensions import NotRequired

# NOTE: I am redefining some of the query constructs in the client because:
# 1. The models defined in the client and server serve two different purposes. The first
# creates a valid serialization of the query to be sent to the server. The latter uses
# that serialization to then compile it to SQL.
# 2. I don't want to include Metricflow as a dependency of this client to avoid bloat
# but also because the types from Metricflow aren't 100% compatible anyways.


class QueryParameters(TypedDict):
    """The parameters of `semantic_layer.query`."""

    metrics: NotRequired[List[str]]
    group_by: NotRequired[List[str]]
    limit: NotRequired[int]
    order_by: NotRequired[List[str]]
    where: NotRequired[List[str]]
    read_cache: NotRequired[bool]
