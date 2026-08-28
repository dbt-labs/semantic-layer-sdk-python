from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import Dict, Generic, Optional, Protocol, TypeVar, Union

from adbc_driver_flightsql import DatabaseOptions
from adbc_driver_flightsql.dbapi import Connection
from adbc_driver_flightsql.dbapi import connect as adbc_connect  # pyright: ignore[reportUnknownVariableType]
from adbc_driver_manager import AdbcStatusCode, ProgrammingError

import dbtsl.env as env
from dbtsl.api.adbc.protocol import ADBCProtocol
from dbtsl.error import AuthError, QueryFailedError


class BaseADBCClient:
    """Base class for the ADBC API client."""

    PROTOCOL = ADBCProtocol
    DEFAULT_URL_FORMAT = env.DEFAULT_ADBC_URL_FORMAT

    # `adbc_driver_flightsql.DatabaseOptions` (as vendored here) does not expose a
    # `TIMEOUT_CONNECT` member, but the underlying Go/C driver has accepted this string
    # key since before this SDK's declared minimum `adbc-driver-flightsql` version
    # (confirmed against the driver source: apache/arrow-adbc
    # go/adbc/driver/flightsql/flightsql_driver.go), so we set it as a raw string.
    #
    # This bounds ONLY the gRPC dial (raw TCP/TLS connection establishment) via
    # `grpc.WithConnectParams(...MinConnectTimeout...)` -- see
    # go/adbc/driver/flightsql/timeouts.go `connectParams()` and
    # `flightsql_database.go` `getFlightClient()`. It does NOT attach a deadline to any
    # Flight RPC, including `Handshake`: the driver's timeout interceptor
    # (`getTimeout()` in timeouts.go) only recognizes `GetFlightInfo`/`DoGet`/
    # `DoPut`/`DoAction` method suffixes, and `Handshake` isn't one of them. (For the
    # bearer-token auth this client uses, the driver never even issues a `Handshake`
    # call in the first place -- see `Open()`/`getFlightClient()` in
    # flightsql_database.go, which pass a nil `ClientAuthHandler` and skip
    # `AuthenticateBasicToken`; `Handshake` is only invoked for username/password auth.)
    # We deliberately leave `.query`/`.fetch`/`.update` unset: real customer queries can
    # legitimately take 10+ minutes (see semantic-layer-gateway's ingress.yaml, which
    # sets a 670s proxy-read-timeout for exactly this reason), so a short timeout must
    # never apply to them. Establishing the connection, in contrast, should be fast, so
    # a short bound here is safe.
    #
    # 15s was chosen with wide margin over observed latency to SLG: DI-5183's Datadog
    # investigation found the (unrelated, RPC-level) Handshake call completes in
    # ~650-810ms fleet-wide -- a reasonable proxy for normal network+TLS overhead on
    # this path -- so 15s gives roughly 20x headroom over that figure, generous enough
    # to absorb jitter while still failing far faster than the unbounded hang it
    # replaces.
    _CONNECT_TIMEOUT_SECONDS: int = 15
    _DB_KWARGS_TIMEOUT_CONNECT_KEY: str = "adbc.flight.sql.rpc.timeout_seconds.connect"

    @classmethod
    def _extra_db_kwargs(cls) -> Dict[str, str]:
        return {
            DatabaseOptions.WITH_COOKIE_MIDDLEWARE.value: "true",
            f"{DatabaseOptions.RPC_CALL_HEADER_PREFIX.value}user-agent": env.PLATFORM.user_agent,
            # Increase the default max msg size in case of queries with large batches
            DatabaseOptions.WITH_MAX_MSG_SIZE.value: f"{1024 * 1024 * 512}",
            # Bound how long we wait for the connection itself to be established. See
            # the class-level comment on `_CONNECT_TIMEOUT_SECONDS` for why only this
            # timeout (and not `.query`/`.fetch`/`.update`) is set.
            cls._DB_KWARGS_TIMEOUT_CONNECT_KEY: str(cls._CONNECT_TIMEOUT_SECONDS),
        }

    def __init__(  # noqa: D107
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
    ) -> None:
        url_format = url_format or self.DEFAULT_URL_FORMAT
        self._conn_str = url_format.format(server_host=server_host)
        self._environment_id = environment_id
        self._auth_token = auth_token

        self._conn_unsafe: Union[Connection, None] = None

    def _get_connection_context_manager(self) -> AbstractContextManager[Connection]:
        return adbc_connect(
            self._conn_str,
            db_kwargs={
                DatabaseOptions.AUTHORIZATION_HEADER.value: f"Bearer {self._auth_token}",
                f"{DatabaseOptions.RPC_CALL_HEADER_PREFIX.value}environmentid": str(self._environment_id),
                **self._extra_db_kwargs(),
            },
        )

    def _handle_error(self, err: Exception) -> None:
        if isinstance(err, ProgrammingError):
            if err.status_code in (AdbcStatusCode.UNAUTHENTICATED, AdbcStatusCode.UNAUTHORIZED):
                raise AuthError(err.args) from err

            if err.status_code == AdbcStatusCode.INVALID_ARGUMENT:
                raise QueryFailedError(err.args[0], err.status_code) from err

            # Only the connect (dial) timeout is implemented -- see
            # `_CONNECT_TIMEOUT_SECONDS` above. Query/fetch/update timeouts remain
            # intentionally unset (see: https://arrow.apache.org/adbc/current/driver/
            # flight_sql.html#timeouts), since queries can legitimately run long.
            if err.status_code == AdbcStatusCode.TIMEOUT:
                raise TimeoutError() from err

        raise err

    @property
    def _conn(self) -> Connection:
        """Safe accessor to `_conn_unsafe`.

        Raises if it is None and return the value if it is not None.
        """
        if self._conn_unsafe is None:
            raise ValueError("Cannot perform operation without opening a session first.")

        return self._conn_unsafe

    @property
    def has_session(self) -> bool:
        """Whether this client has an open session."""
        return self._conn_unsafe is not None


TClient = TypeVar("TClient", bound=BaseADBCClient, covariant=True)


class ADBCClientFactory(Protocol, Generic[TClient]):  # noqa: D101
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
