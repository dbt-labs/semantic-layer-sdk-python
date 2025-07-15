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

    @classmethod
    def _extra_db_kwargs(cls) -> Dict[str, str]:
        return {
            DatabaseOptions.WITH_COOKIE_MIDDLEWARE.value: "true",
            f"{DatabaseOptions.RPC_CALL_HEADER_PREFIX.value}user-agent": env.PLATFORM.user_agent,
            # Increase the default max msg size in case of queries with large batches
            DatabaseOptions.WITH_MAX_MSG_SIZE.value: f"{1024 * 1024 * 512}",
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

            # TODO: timeouts are not implemented for ADBC
            # See: https://arrow.apache.org/adbc/current/driver/flight_sql.html#timeouts
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
