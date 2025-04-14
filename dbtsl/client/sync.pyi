# mypy: disable-error-code="misc"

from contextlib import AbstractContextManager
from typing import Iterator, List, Optional, Union

import pyarrow as pa
from typing_extensions import Self, Unpack, overload

from dbtsl.api.shared.query_params import OrderByGroupBy, OrderByMetric, QueryParameters
from dbtsl.models import Dimension, Entity, Measure, Metric, SavedQuery
from dbtsl.timeout import TimeoutOptions

class SyncSemanticLayerClient:
    def __init__(
        self,
        environment_id: int,
        auth_token: str,
        host: str,
        timeout: Optional[Union[TimeoutOptions, float, int]] = None,
        client_partner_source: Optional[str] = None,
    ) -> None: ...
    @overload
    def compile_sql(
        self,
        metrics: List[str],
        group_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[List[Union[str, OrderByGroupBy, OrderByMetric]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> str: ...
    @overload
    def compile_sql(
        self,
        group_by: List[str],
        limit: Optional[int] = None,
        order_by: Optional[List[Union[str, OrderByGroupBy]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> str: ...
    @overload
    def compile_sql(
        self,
        saved_query: str,
        limit: Optional[int] = None,
        order_by: Optional[List[Union[OrderByGroupBy, OrderByMetric]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> str: ...
    def compile_sql(self, **query_params: Unpack[QueryParameters]) -> str:
        """Get the compiled SQL that would be sent to the warehouse by a query."""
        ...

    @overload
    def query(
        self,
        metrics: List[str],
        group_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[List[Union[str, OrderByGroupBy, OrderByMetric]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> "pa.Table": ...
    @overload
    def query(
        self,
        group_by: List[str],
        limit: Optional[int] = None,
        order_by: Optional[List[Union[str, OrderByGroupBy]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> "pa.Table": ...
    @overload
    def query(
        self,
        saved_query: str,
        limit: Optional[int] = None,
        order_by: Optional[List[Union[OrderByGroupBy, OrderByMetric]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> "pa.Table": ...
    async def query(self, **params: Unpack[QueryParameters]) -> "pa.Table":
        """Query the Semantic Layer."""
        ...

    def metrics(self) -> List[Metric]:
        """List all the metrics available in the Semantic Layer."""
        ...

    def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """List all the dimensions available for a given set of metrics."""
        ...

    def dimension_values(self, metrics: List[str], group_by: str) -> List[str]:
        """List all the possible values for one or multiple metrics and a single dimension."""
        ...

    def measures(self, metrics: List[str]) -> List[Measure]:
        """List all the measures available for a given set of metrics."""
        ...

    def entities(self, metrics: List[str]) -> List[Entity]:
        """Get a list of all available entities for a given set of metrics."""
        ...

    def saved_queries(self) -> List[SavedQuery]:
        """Get a list of all available saved queries."""
        ...

    def session(self) -> AbstractContextManager[Iterator[Self]]:
        """Establish a connection with the dbt Semantic Layer's servers."""
        ...
