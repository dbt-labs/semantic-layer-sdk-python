from contextlib import AbstractAsyncContextManager
from typing import AsyncIterator, List

import pyarrow as pa
from typing_extensions import Self, Unpack

from dbtsl.api.adbc.protocol import QueryParameters
from dbtsl.models import Dimension, Entity, Measure, Metric, SavedQuery

class AsyncSemanticLayerClient:
    def __init__(
        self,
        environment_id: int,
        auth_token: str,
        host: str,
    ) -> None: ...
    async def query(self, **query_params: Unpack[QueryParameters]) -> "pa.Table":
        """Query the Semantic Layer for a metric data."""
        ...

    async def metrics(self) -> List[Metric]:
        """List all the metrics available in the Semantic Layer."""
        ...

    async def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """List all the dimensions available for a given set of metrics."""
        ...

    async def dimension_values(self, metrics: List[str], group_by: str) -> List[str]:
        """List all the possible values for one or multiple metrics and a single dimension."""
        ...

    async def measures(self, metrics: List[str]) -> List[Measure]:
        """List all the measures available for a given set of metrics."""
        ...

    async def entities(self, metrics: List[str]) -> List[Entity]:
        """Get a list of all available entities for a given set of metrics."""
        ...

    async def saved_queries(self) -> List[SavedQuery]:
        """Get a list of all available saved queries."""
        ...

    def session(self) -> AbstractAsyncContextManager[AsyncIterator[Self]]:
        """Establish a connection with the dbt Semantic Layer's servers."""
        ...
