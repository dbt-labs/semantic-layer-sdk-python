import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Union

import pyarrow as pa
from adbc_driver_flightsql import DatabaseOptions
from adbc_driver_flightsql.dbapi import Connection
from adbc_driver_flightsql.dbapi import connect as adbc_connect
from typing_extensions import Unpack

import dbtsl.env as env
from dbtsl.api.adbc.protocol import ADBCProtocol, QueryParameters


class AsyncADBCClient:
    """An asyncio client to access the Semantic Layer via ADBC."""

    def __init__(
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
    ) -> None:
        """Initialize the ADBC client.

        Args:
            server_host: the ADBC API host
            environment_id: Your dbt environment ID
            auth_token: The bearer token that will be used for authentication
            url_format: The full connection URL format that transforms the `server_host`
                into a full URL. If `None`, the default
                `grpc+tls://{server_host}:443`
                will be assumed.
        """
        self._conn_unsafe: Union[Connection, None] = None

        self._loop = asyncio.get_running_loop()

        url_format = url_format or env.DEFAULT_ADBC_URL_FORMAT
        self._conn_str = url_format.format(server_host=server_host)
        self._environment_id = environment_id
        self._auth_token = auth_token

    @property
    def _conn(self) -> Connection:
        """Safe accessor to `_conn_unsafe`.

        Raises if it is None and return the value if it is not None.
        """
        if self._conn_unsafe is None:
            raise ValueError("Cannot perform operation without opening a session first.")

        return self._conn_unsafe

    @asynccontextmanager
    async def session(self) -> AsyncIterator["AsyncADBCClient"]:
        """Open a connection in the underlying ADBC driver.

        All requests made during the same session will reuse the same connection.
        """
        if self._conn_unsafe is not None:
            raise ValueError("A client session is already open.")

        ctx = adbc_connect(
            self._conn_str,
            db_kwargs={
                DatabaseOptions.AUTHORIZATION_HEADER.value: f"Bearer {self._auth_token}",
                f"{DatabaseOptions.RPC_CALL_HEADER_PREFIX.value}environmentid": str(self._environment_id),
                DatabaseOptions.WITH_COOKIE_MIDDLEWARE.value: "true",
            },
        )
        self._conn_unsafe = await self._loop.run_in_executor(None, ctx.__enter__)

        yield self

        await self._loop.run_in_executor(None, ctx.__exit__, None, None, None)
        self._conn_unsafe = None

    async def query(self, **query_params: Unpack[QueryParameters]) -> pa.Table:
        """Query for a dataframe in the Semantic Layer."""
        query_sql = ADBCProtocol.get_query_sql(query_params)

        # NOTE: We don't need to wrap this in a `loop.run_in_executor` since
        # just creating the cursor object doesn't perform any blocking IO.
        with self._conn.cursor() as cur:
            await self._loop.run_in_executor(None, cur.execute, query_sql)
            table = await self._loop.run_in_executor(None, cur.fetch_arrow_table)

        return table
