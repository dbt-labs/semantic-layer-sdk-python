from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import Generic, Optional, Protocol, TypeVar, Union

from adbc_driver_flightsql import DatabaseOptions
from adbc_driver_flightsql.dbapi import Connection
from adbc_driver_flightsql.dbapi import connect as adbc_connect
from adbc_driver_manager import AdbcStatusCode, ProgrammingError

import dbtsl.env as env
from dbtsl.api.adbc.protocol import ADBCProtocol
from dbtsl.error import AuthError, QueryFailedError


class BaseADBCClient:
    """Base class for the ADBC API client."""

    PROTOCOL = ADBCProtocol
    DEFAULT_URL_FORMAT = env.DEFAULT_ADBC_URL_FORMAT

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
                DatabaseOptions.WITH_COOKIE_MIDDLEWARE.value: "true",
            },
        )

    def _handle_error(self, err: Exception) -> None:
        if isinstance(err, ProgrammingError):
            if err.status_code in (AdbcStatusCode.UNAUTHENTICATED, AdbcStatusCode.UNAUTHORIZED):
                raise AuthError(err.args)

            if err.status_code == AdbcStatusCode.INVALID_ARGUMENT:
                raise QueryFailedError(err.args)

            # TODO: timeouts are not implemented for ADBC
            # See: https://arrow.apache.org/adbc/current/driver/flight_sql.html#timeouts
            if err.status_code == AdbcStatusCode.TIMEOUT:
                raise TimeoutError()

        raise err

    @property
    def _conn(self) -> Connection:
        """Safe accessor to `_conn_unsafe`.

        Raises if it is None and return the value if it is not None.
        """
        if self._conn_unsafe is None:
            raise ValueError("Cannot perform operation without opening a session first.")

        return self._conn_unsafe


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
