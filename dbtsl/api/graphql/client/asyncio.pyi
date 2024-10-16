from contextlib import AbstractAsyncContextManager
from typing import List, Optional, Self, Union

import pyarrow as pa
from typing_extensions import AsyncIterator, Unpack, overload

from dbtsl.api.shared.query_params import OrderByGroupBy, OrderByMetric, QueryParameters
from dbtsl.models import (
    Dimension,
    Entity,
    Measure,
    Metric,
    SavedQuery,
)

class AsyncGraphQLClient:
    def __init__(
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
    ) -> None: ...
    def session(self) -> AbstractAsyncContextManager[AsyncIterator[Self]]: ...
    @property
    def has_session(self) -> bool: ...
    async def metrics(self) -> List[Metric]:
        """Get a list of all available metrics."""
        ...

    async def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """Get a list of all available dimensions for a given set of metrics."""
        ...

    async def measures(self, metrics: List[str]) -> List[Measure]:
        """Get a list of all available measures for a given set of metrics."""
        ...

    async def entities(self, metrics: List[str]) -> List[Entity]:
        """Get a list of all available entities for a given set of metrics."""
        ...

    async def saved_queries(self) -> List[SavedQuery]:
        """Get a list of all available saved queries."""
        ...

    @overload
    async def compile_sql(
        self,
        metrics: List[str],
        group_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[List[Union[str, OrderByGroupBy, OrderByMetric]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> str: ...
    @overload
    async def compile_sql(
        self,
        saved_query: str,
        limit: Optional[int] = None,
        order_by: Optional[List[Union[OrderByGroupBy, OrderByMetric]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> str: ...
    async def compile_sql(self, **query_params: Unpack[QueryParameters]) -> str:
        """Get the compiled SQL that would be sent to the warehouse by a query."""
        ...

    @overload
    async def query(
        self,
        metrics: List[str],
        group_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[List[Union[str, OrderByGroupBy, OrderByMetric]]] = None,
        where: Optional[List[str]] = None,
        read_cache: bool = True,
    ) -> "pa.Table": ...
    @overload
    async def query(
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
