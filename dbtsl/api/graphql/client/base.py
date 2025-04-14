import warnings
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
from dbtsl.models.base import GraphQLFragmentMixin
from dbtsl.timeout import TimeoutOptions

TTransport = TypeVar("TTransport", Transport, AsyncTransport)
TSession = TypeVar("TSession", SyncClientSession, AsyncClientSession)


class BaseGraphQLClient(Generic[TTransport, TSession]):
    """Base class for the GraphQL API client.

    This tries to be as network-agnostic as possible. Concrete implementations
    will choose if IO is sync or async.
    """

    PROTOCOL = GraphQLProtocol
    DEFAULT_URL_FORMAT = env.DEFAULT_GRAPHQL_URL_FORMAT
    DEFAULT_TIMEOUT = TimeoutOptions(
        total_timeout=60,
        # Ideally, connect timeouts are a little more than a multiple of 3, which
        # is the default packet retransmission window for TCP
        # See: https://datatracker.ietf.org/doc/html/rfc2988
        connect_timeout=4,
        execute_timeout=60,
        tls_close_timeout=5,
    )

    @classmethod
    def _default_backoff(cls) -> ExponentialBackoff:
        """Get the default backoff behavior when polling."""
        return ExponentialBackoff(
            base_interval_ms=500,
            max_interval_ms=60000,
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
        timeout: Optional[Union[TimeoutOptions, float, int]] = None,
        *,
        lazy: bool,
    ):
        self.environment_id = environment_id
        self.lazy = lazy

        url_format = url_format or self.DEFAULT_URL_FORMAT
        server_url = url_format.format(server_host=server_host)

        if isinstance(timeout, int) or isinstance(timeout, float):
            timeout = float(timeout)
            timeout = TimeoutOptions(
                total_timeout=timeout,
                connect_timeout=timeout,
                execute_timeout=timeout,
                tls_close_timeout=timeout,
            )

        self.timeout = timeout or self.DEFAULT_TIMEOUT

        headers = {
            "authorization": f"bearer {auth_token}",
            **self._extra_headers(),
        }
        transport = self._create_transport(url=server_url, headers=headers)
        self._gql = Client(transport=transport, execute_timeout=self.timeout.execute_timeout)

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

    def _attach_self_to_parsed_response(self, resp: object) -> None:
        # NOTE: we're setting the _client_unchecked here instead of making a public property
        # because we don't want end-users to be aware of this. You can consider _client_unchecked
        # as public to the module but not to end users
        if isinstance(resp, GraphQLFragmentMixin):
            resp._client_unchecked = self  # type: ignore
            return

        if isinstance(resp, list):
            for v in resp:  # pyright: ignore[reportUnknownVariableType]
                self._attach_self_to_parsed_response(v)  # pyright: ignore[reportUnknownArgumentType]

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

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            def wrapped(**kwargs: Any) -> Any:
                return self._run(op=op, raw_variables=kwargs)

            return wrapped


# TODO: have to type ignore, see: https://github.com/microsoft/pyright/issues/3497
TClient = TypeVar("TClient", bound=BaseGraphQLClient, covariant=True)  # type: ignore


class GraphQLClientFactory(Protocol, Generic[TClient]):  # noqa: D101
    @abstractmethod
    def __call__(
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
        timeout: Optional[Union[TimeoutOptions, float, int]] = None,
        *,
        lazy: bool,
    ) -> TClient:
        """Initialize the Semantic Layer client.

        Args:
            server_host: the Semantic Layer API host
            environment_id: your dbt environment ID
            auth_token: the API auth token
            url_format: the URL format string to construct the final URL with
            timeout: `TimeoutOptions` or total timeout
            lazy: lazy load large fields
        """
        pass
