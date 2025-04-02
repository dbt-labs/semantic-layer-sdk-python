from contextlib import contextmanager
from typing import Iterator, Optional

import pyarrow as pa
from typing_extensions import Self, Unpack

from dbtsl.api.adbc.client.base import BaseADBCClient
from dbtsl.api.shared.query_params import DimensionValuesQueryParameters, QueryParameters


class SyncADBCClient(BaseADBCClient):
    """A sync client to access the Semantic Layer via ADBC."""

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

    @contextmanager
    def session(self) -> Iterator[Self]:
        """Open a connection in the underlying ADBC driver.

        All requests made during the same session will reuse the same connection.
        """
        if self._conn_unsafe is not None:
            raise ValueError("A client session is already open.")

        ctx = self._get_connection_context_manager()
        with ctx as conn:
            self._conn_unsafe = conn
            yield self
            self._conn_unsafe = None

    def query(self, **query_params: Unpack[QueryParameters]) -> pa.Table:
        """Query for a dataframe in the Semantic Layer."""
        query_sql = self.PROTOCOL.get_query_sql(query_params)

        with self._conn.cursor() as cur:
            try:
                cur.execute(query_sql)  # pyright: ignore[reportUnknownMemberType]
            except Exception as err:
                self._handle_error(err)

            table = cur.fetch_arrow_table()

        return table

    def dimension_values(self, **query_params: Unpack[DimensionValuesQueryParameters]) -> pa.Table:
        """Query for the possible values of a dimension."""
        query_sql = self.PROTOCOL.get_dimension_values_sql(query_params)

        with self._conn.cursor() as cur:
            try:
                cur.execute(query_sql)  # pyright: ignore[reportUnknownMemberType]
            except Exception as err:
                self._handle_error(err)

            table = cur.fetch_arrow_table()

        return table
