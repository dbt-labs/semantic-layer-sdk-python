import functools
from abc import abstractmethod
from typing import Any, Dict, Generic, Optional, Protocol, TypeVar, Union

from gql import Client
from gql.client import AsyncClientSession, SyncClientSession
from gql.transport import AsyncTransport, Transport
from gql.transport.exceptions import TransportQueryError

import dbtsl.env as env
from dbtsl.api.graphql.protocol import (
    GraphQLProtocol,
)
from dbtsl.backoff import ExponentialBackoff
from dbtsl.error import AuthError

TTransport = TypeVar("TTransport", Transport, AsyncTransport)
TSession = TypeVar("TSession", SyncClientSession, AsyncClientSession)


class BaseGraphQLClient(Generic[TTransport, TSession]):
    """Base class for the GraphQL API client.

    This tries to be as network-agnostic as possible. Concrete implementations
    will choose if IO is sync or async.
    """

    PROTOCOL = GraphQLProtocol
    DEFAULT_URL_FORMAT = env.DEFAULT_GRAPHQL_URL_FORMAT

    @classmethod
    def _default_backoff(cls) -> ExponentialBackoff:
        """Get the default backoff behavior when polling."""
        return ExponentialBackoff(
            base_interval_ms=500,
            max_interval_ms=60000,
            timeout_ms=90000,
        )

    @classmethod
    def _extra_headers(cls) -> Dict[str, str]:
        return {
            "user-agent": env.PLATFORM.user_agent,
        }

    def __init__(  # noqa: D107
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
    ):
        self.environment_id = environment_id

        url_format = url_format or self.DEFAULT_URL_FORMAT
        server_url = url_format.format(server_host=server_host)

        headers = {
            "authorization": f"bearer {auth_token}",
            **self._extra_headers(),
        }
        transport = self._create_transport(url=server_url, headers=headers)
        self._gql = Client(transport=transport)

        self._gql_session_unsafe: Union[TSession, None] = None

    @abstractmethod
    def _create_transport(self, url: str, headers: Dict[str, str]) -> TTransport:
        """Create the underlying transport to be used by the gql Client."""
        raise NotImplementedError()

    def _refine_err(self, err: Exception) -> Exception:
        """Refine a generic exception that might have happened during `_run`."""
        if (
            isinstance(err, TransportQueryError)
            and err.errors is not None
            and err.errors[0]["message"] == "User is not authorized"
        ):
            return AuthError(err.args)

        return err

    @property
    def _gql_session(self) -> TSession:
        """Safe accessor to `_gql_session_unsafe`.

        Raises if it is None and return the value if it is not None.
        """
        if self._gql_session_unsafe is None:
            raise ValueError("Cannot perform operation without opening a session first.")

        return self._gql_session_unsafe

    @property
    def has_session(self) -> bool:
        """Whether this client has an open session."""
        return self._gql_session_unsafe is not None

    def __getattr__(self, attr: str) -> Any:
        """Run an underlying GraphQLOperation if it exists in GraphQLProtocol."""
        op = getattr(self.PROTOCOL, attr)
        if op is None:
            raise AttributeError()

        return functools.partial(
            self._run,
            op=op,
        )


TClient = TypeVar("TClient", bound=BaseGraphQLClient, covariant=True)


class GraphQLClientFactory(Protocol, Generic[TClient]):  # noqa: D101
    @abstractmethod
    def __call__(self, server_host: str, environment_id: int, auth_token: str, url_format: str) -> TClient:
        """Initialize the Semantic Layer client.

        Args:
            server_host: the Semantic Layer API host
            environment_id: your dbt environment ID
            auth_token: the API auth token
            url_format: the URL format string to construct the final URL with
        """
        pass
