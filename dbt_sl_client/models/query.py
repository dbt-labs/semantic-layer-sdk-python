import base64
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import NewType, Optional

import pyarrow as pa
from mashumaro import DataClassDictMixin, field_options

QueryId = NewType("QueryId", str)


class QueryStatus(str, Enum):
    """All the possible states of a query."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPILED = "COMPILED"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"


@dataclass(frozen=True)
class QueryResult(DataClassDictMixin):
    """A query result containing its status, SQL and error/results."""

    query_id: QueryId = field(metadata=field_options(alias="queryId"))
    status: QueryStatus
    sql: Optional[str]
    error: Optional[str]
    total_pages: Optional[int] = field(metadata=field_options(alias="totalPages"))
    arrow_result: Optional[str] = field(metadata=field_options(alias="arrowResult"))

    @cached_property
    def result_table(self) -> pa.Table:
        """Get the resulting pyarrow Table parsed from arrow_result."""
        if self.status != QueryStatus.SUCCESSFUL or self.arrow_result is None:
            raise ValueError("Cannot get dataframe from query if it's not SUCCESSFUL.")

        decoded = base64.b64decode(self.arrow_result)
        with pa.ipc.open_stream(decoded) as stream:
            table = pa.Table.from_batches(stream, stream.schema)

        return table
