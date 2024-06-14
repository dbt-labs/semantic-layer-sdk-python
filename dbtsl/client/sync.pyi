from contextlib import AbstractContextManager
from typing import Iterator, List

import pyarrow as pa
from typing_extensions import Self, Unpack

from dbtsl.api.adbc.protocol import QueryParameters
from dbtsl.models import Dimension, Measure, Metric

class SyncSemanticLayerClient:
    def __init__(
        self,
        environment_id: int,
        auth_token: str,
        host: str,
    ) -> None: ...
    def query(self, **query_params: Unpack[QueryParameters]) -> "pa.Table":
        """Query the Semantic Layer for a metric data."""
        ...

    def metrics(self) -> List[Metric]:
        """List all the metrics available in the Semantic Layer."""
        ...

    def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """List all the dimensions available for a given set of metrics."""
        ...

    def measures(self, metrics: List[str]) -> List[Measure]:
        """List all the measures available for a given set of metrics."""
        ...

    def session(self) -> AbstractContextManager[Iterator[Self]]:
        """Establish a connection with the dbt Semantic Layer's servers."""
        ...
