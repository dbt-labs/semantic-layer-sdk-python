import os
from abc import ABC
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator, List

from typing_extensions import Unpack

from dbt_sl_client.api.adbc.async_client import AsyncADBCClient
from dbt_sl_client.api.adbc.protocol import QueryParameters
from dbt_sl_client.api.graphql.async_client import AsyncGraphQLClient
from dbt_sl_client.models import Dimension, Measure, Metric

if TYPE_CHECKING:
    import pyarrow as pa

GRAPHQL_URL_FORMAT_OVERRIDE = os.environ.get("DBT_SL_GQL_URL_FORMAT", None)
ARROW_URL_FORMAT_OVERRIDE = os.environ.get("DBT_SL_ARROW_URL_FORMAT", None)


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
            url_format=GRAPHQL_URL_FORMAT_OVERRIDE,
        )
        self._adbc = AsyncADBCClient(
            server_host=host,
            environment_id=environment_id,
            auth_token=auth_token,
            url_format=ARROW_URL_FORMAT_OVERRIDE,
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
