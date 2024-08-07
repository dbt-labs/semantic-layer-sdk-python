from contextlib import AbstractAsyncContextManager
from typing import List, Optional, Self

import pyarrow as pa
from typing_extensions import AsyncIterator, Unpack

from dbtsl.api.shared.query_params import QueryParameters
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

    async def query(self, **params: Unpack[QueryParameters]) -> "pa.Table": ...
