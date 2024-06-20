import base64
import io
from unittest.mock import AsyncMock, call

import pyarrow as pa
from pytest_mock import MockerFixture

from dbtsl.api.graphql.client.asyncio import AsyncGraphQLClient
from dbtsl.api.graphql.client.sync import SyncGraphQLClient
from dbtsl.api.shared.query_params import QueryParameters
from dbtsl.models.query import QueryId, QueryResult, QueryStatus

# The following 2 tests are copies of each other since testing the same sync/async functionality is
# a pain. I should probably find how to fix this later

async def test_async_query_multiple_pages(mocker: MockerFixture) -> None:
    """Test that querying a dataframe with multiple pages works."""
    client = AsyncGraphQLClient(server_host="test", environment_id=0, auth_token="test")

    query_id = QueryId("test-query-id")
    table = pa.Table.from_arrays(
        [pa.array([2, 4, 6, 100]), pa.array(["Chicken", "Dog", "Ant", "Centipede"])], names=["num_legs", "animal"]
    )

    async def gqr_behavior(query_id: QueryId, page_num: int) -> QueryResult:
        """Behaves like `get_query_result` but without talking to any servers."""
        call_table = table.slice(offset=page_num - 1, length=1)

        byte_stream = io.BytesIO()
        with pa.ipc.new_stream(byte_stream, call_table.schema) as writer:
            writer.write_table(call_table)

        return QueryResult(
            query_id=query_id,
            status=QueryStatus.SUCCESSFUL,
            sql=None,
            error=None,
            total_pages=len(table),
            arrow_result=base64.b64encode(byte_stream.getvalue()).decode("utf-8"),
        )

    cq_mock = mocker.patch.object(client, "create_query", return_value=query_id, new_callable=AsyncMock)
    gqr_mock = mocker.patch.object(client, "get_query_result", side_effect=gqr_behavior, new_callable=AsyncMock)

    kwargs: QueryParameters = {"metrics": ["m1", "m2"], "group_by": ["gb"], "limit": 1}

    result_table = await client.query(**kwargs)

    cq_mock.assert_awaited_once_with(**kwargs)

    gqr_mock.assert_has_awaits(
        [
            call(query_id=query_id, page_num=1),
            call(query_id=query_id, page_num=2),
            call(query_id=query_id, page_num=3),
            call(query_id=query_id, page_num=4),
        ]
    )

    assert result_table.equals(table, check_metadata=True)


def test_sync_query_multiple_pages(mocker: MockerFixture) -> None:
    """Test that querying a dataframe with multiple pages works."""
    client = SyncGraphQLClient(server_host="test", environment_id=0, auth_token="test")

    query_id = QueryId("test-query-id")
    table = pa.Table.from_arrays(
        [pa.array([2, 4, 6, 100]), pa.array(["Chicken", "Dog", "Ant", "Centipede"])], names=["num_legs", "animal"]
    )

    def gqr_behavior(query_id: QueryId, page_num: int) -> QueryResult:
        """Behaves like `get_query_result` but without talking to any servers."""
        call_table = table.slice(offset=page_num - 1, length=1)

        byte_stream = io.BytesIO()
        with pa.ipc.new_stream(byte_stream, call_table.schema) as writer:
            writer.write_table(call_table)

        return QueryResult(
            query_id=query_id,
            status=QueryStatus.SUCCESSFUL,
            sql=None,
            error=None,
            total_pages=len(table),
            arrow_result=base64.b64encode(byte_stream.getvalue()).decode("utf-8"),
        )

    cq_mock = mocker.patch.object(client, "create_query", return_value=query_id)
    gqr_mock = mocker.patch.object(client, "get_query_result", side_effect=gqr_behavior)

    kwargs: QueryParameters = {"metrics": ["m1", "m2"], "group_by": ["gb"], "limit": 1}

    result_table = client.query(**kwargs)

    cq_mock.assert_called_once_with(**kwargs)

    gqr_mock.assert_has_calls(
        [
            call(query_id=query_id, page_num=1),
            call(query_id=query_id, page_num=2),
            call(query_id=query_id, page_num=3),
            call(query_id=query_id, page_num=4),
        ]
    )

    assert result_table.equals(table, check_metadata=True)
