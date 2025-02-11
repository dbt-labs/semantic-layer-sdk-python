import time
from contextlib import contextmanager
from typing import Dict, Iterator, Optional

import pyarrow as pa
from gql import gql
from gql.client import SyncClientSession
from gql.transport.requests import RequestsHTTPTransport
from typing_extensions import Self, Unpack, override

from dbtsl.api.graphql.client.base import BaseGraphQLClient
from dbtsl.api.graphql.protocol import (
    ProtocolOperation,
    TJobStatusResult,
    TJobStatusVariables,
    TResponse,
    TVariables,
)
from dbtsl.api.shared.query_params import QueryParameters
from dbtsl.backoff import ExponentialBackoff
from dbtsl.error import QueryFailedError
from dbtsl.models.query import QueryId, QueryStatus


class SyncGraphQLClient(BaseGraphQLClient[RequestsHTTPTransport, SyncClientSession]):
    """A sync client to access semantic layer via GraphQL, backed by requests."""

    def __init__(
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ):
        """Initialize the metadata client.

        Args:
            server_host: the GraphQL API host
            environment_id: Your dbt environment ID
            auth_token: The bearer token that will be used for authentication
            url_format: The full connection URL format that transforms the `server_host`
                into a full URL. If `None`, the default `https://{server_host}/api/graphql`
                will be assumed.
            timeout_ms: Timeout (in milliseconds) for all GraphQL requests.
        """
        super().__init__(server_host, environment_id, auth_token, url_format, timeout_ms)

    @override
    def _create_transport(self, url: str, headers: Dict[str, str], timeout_ms: int) -> RequestsHTTPTransport:
        timeout_s = int(timeout_ms / 1_000)
        return RequestsHTTPTransport(url=url, headers=headers, timeout=timeout_s)

    @contextmanager
    def session(self) -> Iterator[Self]:
        """Open a session in the underlying requests transport.

        A "session" is a TCP connection with the server. All operations
        performed under the same session will reuse the same TCP connection.
        """
        if self._gql_session_unsafe is not None:
            raise ValueError("A client session is already open.")

        with self._gql as session:
            assert isinstance(session, SyncClientSession)
            self._gql_session_unsafe = session
            yield self
            self._gql_session_unsafe = None

    def _run(self, op: ProtocolOperation[TVariables, TResponse], **kwargs: TVariables) -> TResponse:
        """Run a `ProtocolOperation`."""
        raw_query = op.get_request_text()
        variables = op.get_request_variables(environment_id=self.environment_id, **kwargs)
        gql_query = gql(raw_query)

        try:
            res = self._gql_session.execute(gql_query, variable_values=variables)
        except Exception as err:
            raise self._refine_err(err)

        return op.parse_response(res)

    def _poll_until_complete(
        self,
        query_id: QueryId,
        poll_op: ProtocolOperation[TJobStatusVariables, TJobStatusResult],
        backoff: Optional[ExponentialBackoff] = None,
        **kwargs,
    ) -> TJobStatusResult:
        """Poll for a query's results until it is in a completed state (SUCCESSFUL or FAILED).

        Note that this function does NOT fetch all pages in case the query is SUCCESSFUL. It only
        returns once the query is done. Callers must implement this logic themselves.
        """
        if backoff is None:
            backoff = self._default_backoff()

        for sleep_ms in backoff.iter_ms():
            # TODO: add timeout param to all requests because technically the API could hang and
            # then we don't respect timeout.
            kwargs["query_id"] = query_id
            qr = self._run(poll_op, **kwargs)
            if qr.status in (QueryStatus.SUCCESSFUL, QueryStatus.FAILED):
                return qr

            time.sleep(sleep_ms / 1000)

        # This should be unreachable
        raise ValueError()

    def query(self, **params: Unpack[QueryParameters]) -> "pa.Table":
        """Query the Semantic Layer."""
        query_id = self.create_query(**params)
        first_page_results = self._poll_until_complete(query_id, self.PROTOCOL.get_query_result, page_num=1)
        if first_page_results.status != QueryStatus.SUCCESSFUL:
            raise QueryFailedError()

        assert first_page_results.total_pages is not None

        if first_page_results.total_pages == 1:
            return first_page_results.result_table

        results = [
            self.get_query_result(query_id=query_id, page_num=page)
            for page in range(2, first_page_results.total_pages + 1)
        ]
        all_page_results = [first_page_results] + results
        tables = [r.result_table for r in all_page_results]
        final_table = pa.concat_tables(tables)
        return final_table
