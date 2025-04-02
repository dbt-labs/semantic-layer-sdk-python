import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import pyarrow as pa
from typing_extensions import Self, Unpack

from dbtsl.api.adbc.client.base import BaseADBCClient
from dbtsl.api.shared.query_params import DimensionValuesQueryParameters, QueryParameters


class AsyncADBCClient(BaseADBCClient):
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
        super().__init__(server_host, environment_id, auth_token, url_format)
        self._loop = asyncio.get_running_loop()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Self]:
        """Open a connection in the underlying ADBC driver.

        All requests made during the same session will reuse the same connection.
        """
        if self._conn_unsafe is not None:
            raise ValueError("A client session is already open.")

        ctx = self._get_connection_context_manager()
        self._conn_unsafe = await self._loop.run_in_executor(None, ctx.__enter__)

        yield self

        await self._loop.run_in_executor(None, ctx.__exit__, None, None, None)
        self._conn_unsafe = None

    async def query(self, **query_params: Unpack[QueryParameters]) -> pa.Table:
        """Query for a dataframe in the Semantic Layer."""
        query_sql = self.PROTOCOL.get_query_sql(query_params)

        # NOTE: We don't need to wrap this in a `loop.run_in_executor` since
        # just creating the cursor object doesn't perform any blocking IO.
        with self._conn.cursor() as cur:
            try:
                await self._loop.run_in_executor(None, cur.execute, query_sql)  # pyright: ignore[reportUnknownArgumentType,reportUnknownMemberType]
            except Exception as err:
                self._handle_error(err)
            table = await self._loop.run_in_executor(None, cur.fetch_arrow_table)

        return table

    async def dimension_values(self, **query_params: Unpack[DimensionValuesQueryParameters]) -> pa.Table:
        """Query for the possible values of a dimension."""
        query_sql = self.PROTOCOL.get_dimension_values_sql(query_params)

        # NOTE: We don't need to wrap this in a `loop.run_in_executor` since
        # just creating the cursor object doesn't perform any blocking IO.
        with self._conn.cursor() as cur:
            try:
                await self._loop.run_in_executor(None, cur.execute, query_sql)  # pyright: ignore[reportUnknownArgumentType,reportUnknownMemberType]

            except Exception as err:
                self._handle_error(err)
            table = await self._loop.run_in_executor(None, cur.fetch_arrow_table)

        return table
