from abc import ABC
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, List

from typing_extensions import Unpack

import dbtsl.env as env
from dbtsl.api.adbc.async_client import AsyncADBCClient
from dbtsl.api.adbc.protocol import QueryParameters
from dbtsl.api.graphql.async_client import AsyncGraphQLClient
from dbtsl.models import Dimension, Measure, Metric

if TYPE_CHECKING:
    import pyarrow as pa


class AsyncSemanticLayerClient(ABC):
    """A semantic layer client.

    It performs operations by using the most appropriate API depending on the
    operation. For example, dataframes are fetched via ADBC while metadata
    is fetched via GraphQL.

    If you want to override this behavior (say, get dataframes via GraphQL),
    please use the API clients directly.
    """

    def __init__(
        self,
        environment_id: int,
        auth_token: str,
        host: str,
    ) -> None:
        """Initialize the Semantic Layer client.

        Args:
            environment_id: your dbt environment ID
            auth_token: the API auth token
            host: the Semantic Layer API host
        """
        self._has_session = False

        self._gql = AsyncGraphQLClient(
            server_host=host,
            environment_id=environment_id,
            auth_token=auth_token,
            url_format=env.GRAPHQL_URL_FORMAT,
        )
        self._adbc = AsyncADBCClient(
            server_host=host,
            environment_id=environment_id,
            auth_token=auth_token,
            url_format=env.ADBC_URL_FORMAT,
        )

    def _assert_session(self) -> None:
        if not self._has_session:
            raise ValueError("Cannot perform operation without opening a session first.")

    @asynccontextmanager
    async def session(self) -> AsyncIterator["AsyncSemanticLayerClient"]:
        """Establish a connection with the dbt Semantic Layer's servers."""
        if self._has_session:
            raise ValueError("Cannot open session within session.")

        async with self._gql.session(), self._adbc.session():
            self._has_session = True
            yield self
            self._has_session = False

    def __getattribute__(self, attr: str) -> Any:
        """Get methods from the underlying APIs.

        `query` goes through ADBC, while the rest goes through GQL.
        """
        if attr == "query":
            return self._adbc.query

        return getattr(self._gql, attr)

    async def query(self, **query_params: Unpack[QueryParameters]) -> "pa.Table":
        """Query the Semantic Layer for a metric data."""
        return await self._adbc.query(**query_params)

    async def metrics(self) -> List[Metric]:
        """List all the metrics available in the Semantic Layer."""
        self._assert_session()
        return await self._gql.metrics()

    async def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """List all the dimensions available for a given set of metrics."""
        self._assert_session()
        return await self._gql.dimensions(metrics=metrics)

    async def measures(self, metrics: List[str]) -> List[Measure]:
        """List all the measures available for a given set of metrics."""
        self._assert_session()
        return await self._gql.measures(metrics=metrics)
