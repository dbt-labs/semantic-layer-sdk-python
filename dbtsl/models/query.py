import base64
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import NewType, Optional

import pyarrow as pa

from dbtsl.models.base import BaseModel, FlexibleEnumMeta, GraphQLFragmentMixin

QueryId = NewType("QueryId", str)


class QueryStatus(Enum, metaclass=FlexibleEnumMeta):
    """All the possible states of a query."""

    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPILED = "COMPILED"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"


@dataclass
class QueryResult(BaseModel, GraphQLFragmentMixin):
    """A query result containing its status, SQL and error/results."""

    query_id: QueryId
    status: QueryStatus
    sql: Optional[str]
    error: Optional[str]
    total_pages: Optional[int]
    arrow_result: Optional[str]

    @cached_property
    def result_table(self) -> pa.Table:
        """Get the resulting pyarrow Table parsed from arrow_result."""
        if self.status != QueryStatus.SUCCESSFUL or self.arrow_result is None:
            raise ValueError("Cannot get dataframe from query if it's not SUCCESSFUL.")

        decoded = base64.b64decode(self.arrow_result)
        with pa.ipc.open_stream(decoded) as stream:
            table = pa.Table.from_batches(stream, stream.schema)

        return table
