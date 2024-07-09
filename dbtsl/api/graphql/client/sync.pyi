from contextlib import AbstractContextManager
from typing import Iterator, List, Optional

import pyarrow as pa
from typing_extensions import Self, Unpack

from dbtsl.api.shared.query_params import QueryParameters
from dbtsl.models import (
    Dimension,
    Entity,
    Measure,
    Metric,
    SavedQuery,
)

class SyncGraphQLClient:
    def __init__(
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
    ) -> None: ...
    def session(self) -> AbstractContextManager[Iterator[Self]]: ...
    @property
    def has_session(self) -> bool: ...
    def metrics(self) -> List[Metric]:
        """Get a list of all available metrics."""
        ...

    def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """Get a list of all available dimensions for a given set of metrics."""
        ...

    def measures(self, metrics: List[str]) -> List[Measure]:
        """Get a list of all available measures for a given set of metrics."""
        ...

    def entities(self, metrics: List[str]) -> List[Entity]:
        """Get a list of all available entities for a given set of metrics."""
        ...

    def saved_queries(self) -> List[SavedQuery]:
        """Get a list of all available saved queries."""
        ...

    def query(self, **params: Unpack[QueryParameters]) -> "pa.Table": ...
