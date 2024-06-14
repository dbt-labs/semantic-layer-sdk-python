import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Optional, Union

import pyarrow as pa
from gql import Client, gql
from gql.client import AsyncClientSession
from gql.transport.aiohttp import AIOHTTPTransport
from typing_extensions import Unpack

import dbtsl.env as env
from dbtsl.api.graphql.protocol import (
    GetQueryResultVariables,
    GraphQLProtocol,
    ProtocolOperation,
    TResponse,
    TVariables,
)
from dbtsl.api.shared.query_params import QueryParameters
from dbtsl.backoff import ExponentialBackoff
from dbtsl.error import QueryFailedError
from dbtsl.models import (
    Dimension,
    Measure,
    Metric,
)
from dbtsl.models.query import QueryId, QueryResult, QueryStatus


class AsyncGraphQLClient:
    """An asyncio client to access semantic layer via GraphQL."""

    @classmethod
    def _default_backoff(cls) -> ExponentialBackoff:
        """Get the default backoff behavior when polling."""
        return ExponentialBackoff(
            base_interval_ms=500,
            max_interval_ms=60000,
            timeout_ms=90000,
        )

    def __init__(
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
    ):
        """Initialize the metadata client.

        Args:
            server_host: the GraphQL API host
            environment_id: Your dbt environment ID
            auth_token: The bearer token that will be used for authentication
            url_format: The full connection URL format that transforms the `server_host`
                into a full URL. If `None`, the default `https://{server_host}/api/graphql`
                will be assumed.
        """
        self.environment_id = environment_id

        url_format = url_format or env.DEFAULT_GRAPHQL_URL_FORMAT
        server_url = url_format.format(server_host=server_host)

        transport = AIOHTTPTransport(url=server_url, headers={"Authorization": f"Bearer {auth_token}"})
        self._gql = Client(transport=transport)

        self._gql_session_unsafe: Union[AsyncClientSession, None] = None

    @property
    def _gql_session(self) -> AsyncClientSession:
        """Safe accessor to `_gql_session_unsafe`.

        Raises if it is None and return the value if it is not None.
        """
        if self._gql_session_unsafe is None:
            raise ValueError("Cannot perform operation without opening a session first.")

        return self._gql_session_unsafe

    @asynccontextmanager
    async def session(self) -> AsyncIterator["AsyncGraphQLClient"]:
        """Open a session in the underlying aiohttp transport.

        A "session" is a TCP connection with the server. All operations
        performed under the same session will reuse the same TCP connection.
        """
        if self._gql_session_unsafe is not None:
            raise ValueError("A client session is already open.")

        async with self._gql as session:
            self._gql_session_unsafe = session
            yield self
            self._gql_session_unsafe = None

    async def _run(self, op: ProtocolOperation[TVariables, TResponse], **kwargs: TVariables) -> TResponse:
        """Run a `ProtocolOperation`."""
        raw_query = op.get_request_text()
        variables = op.get_request_variables(environment_id=self.environment_id, **kwargs)
        gql_query = gql(raw_query)

        res = await self._gql_session.execute(gql_query, variable_values=variables)

        return op.parse_response(res)

    # NOTE: Here comes a bunch of boilerplate just so PyRight is happy :D
    # We could generate these methods at runtime but then all the static
    # checkers would be confused and it would result in horrible UX.
    async def metrics(self) -> List[Metric]:
        """Get a list of all available metrics."""
        return await self._run(GraphQLProtocol.list_metrics)

    async def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """Get a list of all available dimensions for a given metric."""
        return await self._run(GraphQLProtocol.list_dimensions, metrics=metrics)  # type: ignore

    async def measures(self, metrics: List[str]) -> List[Measure]:
        """Get a list of all available measures for a given metric."""
        return await self._run(GraphQLProtocol.list_measures, metrics=metrics)  # type: ignore

    async def _create_query(self, **params: Unpack[QueryParameters]) -> QueryId:
        """Create a query that will run asynchronously."""
        return await self._run(GraphQLProtocol.create_query, **params)  # type: ignore

    async def _get_query_result(self, **params: Unpack[GetQueryResultVariables]) -> QueryResult:
        """Fetch a query's results'."""
        return await self._run(GraphQLProtocol.get_query_result, **params)  # type: ignore

    async def _poll_until_complete(
        self,
        query_id: QueryId,
        backoff: Optional[ExponentialBackoff] = None,
    ) -> QueryResult:
        """Poll for a query's results until it is in a completed state (SUCCESSFUL or FAILED).

        Note that this function does NOT fetch all pages in case the query is SUCCESSFUL. It only
        returns once the query is done. Callers must implement this logic themselves.
        """
        if backoff is None:
            backoff = self._default_backoff()

        for sleep_ms in backoff.iter_ms():
            # TODO: add timeout param to all requests because technically the API could hang and
            # then we don't respect timeout.
            qr = await self._get_query_result(query_id=query_id, page_num=1)
            if qr.status in (QueryStatus.SUCCESSFUL, QueryStatus.FAILED):
                return qr

            await asyncio.sleep(sleep_ms / 1000)

        # This should be unreachable
        raise ValueError()

    async def query(self, **params: Unpack[QueryParameters]) -> "pa.Table":
        """Query the Semantic Layer."""
        query_id = await self._create_query(**params)
        first_page_results = await self._poll_until_complete(query_id)
        if first_page_results.status != QueryStatus.SUCCESSFUL:
            raise QueryFailedError()

        # Server should never return None if query is SUCCESSFUL.
        # This is so pyright stops complaining
        assert first_page_results.total_pages is not None

        if first_page_results.total_pages == 1:
            return first_page_results.result_table

        tasks = [
            self._get_query_result(query_id=query_id, page_num=page)
            for page in range(2, first_page_results.total_pages + 1)
        ]
        all_page_results = [first_page_results] + await asyncio.gather(*tasks)
        tables = [r.result_table for r in all_page_results]
        final_table = pa.concat_tables(tables)
        return final_table
