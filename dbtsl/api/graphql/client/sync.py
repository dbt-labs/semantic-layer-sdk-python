from contextlib import contextmanager
from typing import Dict, Iterator, Optional, Self, override

from gql import gql
from gql.client import SyncClientSession
from gql.transport.requests import RequestsHTTPTransport

from dbtsl.api.graphql.client.base import BaseGraphQLClient
from dbtsl.api.graphql.protocol import (
    ProtocolOperation,
    TResponse,
    TVariables,
)


class SyncGraphQLClient(BaseGraphQLClient[RequestsHTTPTransport, SyncClientSession]):
    """A sync client to access semantic layer via GraphQL, backed by requests."""

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
        super().__init__(server_host, environment_id, auth_token, url_format)

    @override
    def _create_transport(self, url: str, headers: Dict[str, str]) -> RequestsHTTPTransport:
        return RequestsHTTPTransport(url=url, headers=headers)

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

        res = self._gql_session.execute(gql_query, variable_values=variables)

        return op.parse_response(res)

    # TODO: sync transport doesn't have `query` method. This should be OK since ADBC
    # is the go-to method anyways. If people request it, we can implement later.
