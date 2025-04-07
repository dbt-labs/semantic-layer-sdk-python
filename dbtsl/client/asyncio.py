from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Union

from typing_extensions import Self

from dbtsl.api.adbc.client.asyncio import AsyncADBCClient
from dbtsl.api.graphql.client.asyncio import AsyncGraphQLClient
from dbtsl.client.base import BaseSemanticLayerClient
from dbtsl.timeout import TimeoutOptions


class AsyncSemanticLayerClient(BaseSemanticLayerClient[AsyncGraphQLClient, AsyncADBCClient]):  # type: ignore
    """An asyncio semantic layer client, backed by aiohttp.

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
        timeout: Optional[Union[TimeoutOptions, float, int]] = None,
        *,
        lazy: bool = False,
    ) -> None:
        """Initialize the Semantic Layer client.

        Args:
            environment_id: your dbt environment ID
            auth_token: the API auth token
            host: the Semantic Layer API host
            timeout: `TimeoutOptions` or total timeout for the underlying GraphQL client.
            lazy: if true, nested metadata queries will be need to be explicitly populated on-demand.
        """
        super().__init__(
            environment_id=environment_id,
            auth_token=auth_token,
            host=host,
            gql_factory=AsyncGraphQLClient,
            adbc_factory=AsyncADBCClient,
            timeout=timeout,
            lazy=lazy,
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Self]:
        """Establish a connection with the dbt Semantic Layer's servers."""
        if self._has_session:
            raise ValueError("Cannot open session within session.")

        async with self._gql.session(), self._adbc.session():
            self._has_session = True
            yield self
            self._has_session = False
