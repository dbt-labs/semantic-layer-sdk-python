import base64
import io
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call

import pyarrow as pa
import pytest
from pytest_mock import MockerFixture

from dbtsl.api.graphql.client.asyncio import AsyncGraphQLClient
from dbtsl.api.graphql.client.sync import SyncGraphQLClient
from dbtsl.api.graphql.protocol import GetQueryResultVariables, GraphQLProtocol, ProtocolOperation
from dbtsl.error import RetryTimeoutError
from dbtsl.models.query import QueryId, QueryResult, QueryStatus

# The following 2 tests are copies of each other since testing the same sync/async functionality is
# a pain. I should probably find how to fix this later
#
# These tests are so bad and test a bunch of internals, I hate my life


async def test_async_query_multiple_pages(mocker: MockerFixture) -> None:
    """Test that querying a dataframe with multiple pages works."""
    client = AsyncGraphQLClient(server_host="test", environment_id=0, auth_token="test", lazy=False)

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

    async def run_behavior(op: ProtocolOperation[Any, Any], raw_variables: GetQueryResultVariables) -> QueryResult:
        return await gqr_behavior(raw_variables["query_id"], raw_variables.get("page_num"))

    cq_mock = mocker.patch.object(client, "create_query", return_value=query_id, new_callable=AsyncMock)

    run_mock = AsyncMock(side_effect=run_behavior)
    mocker.patch.object(client, "_run", new=run_mock)
    gqr_mock = AsyncMock(side_effect=gqr_behavior)
    mocker.patch.object(client, "get_query_result", new=gqr_mock)

    gql_mock = mocker.patch.object(client, "_gql")
    mocker.patch.object(gql_mock, "__aenter__", new_callable=AsyncMock)
    mocker.patch("dbtsl.api.graphql.client.asyncio.isinstance", return_value=True)

    kwargs = {"metrics": ["m1", "m2"], "group_by": ["gb"], "limit": 1}
    async with client.session():
        result_table = await client.query(**kwargs)  # pyright: ignore[reportUnknownVariableType]

    cq_mock.assert_awaited_once_with(**kwargs)

    run_mock.assert_has_awaits(
        [
            call(op=GraphQLProtocol.get_query_result, raw_variables={"query_id": query_id, "page_num": 1}),
        ]
    )

    gqr_mock.assert_has_awaits(
        [
            call(query_id=query_id, page_num=2),
            call(query_id=query_id, page_num=3),
            call(query_id=query_id, page_num=4),
        ]
    )

    assert result_table.equals(table, check_metadata=True)


# avoid raising mock warning related to mocking a context manager
@pytest.mark.filterwarnings("ignore::pytest_mock.PytestMockWarning")
def test_sync_query_multiple_pages(mocker: MockerFixture) -> None:
    """Test that querying a dataframe with multiple pages works."""
    client = SyncGraphQLClient(server_host="test", environment_id=0, auth_token="test", lazy=False)

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

    def run_behavior(op: ProtocolOperation[Any, Any], raw_variables: GetQueryResultVariables) -> QueryResult:
        return gqr_behavior(raw_variables["query_id"], raw_variables.get("page_num"))

    cq_mock = mocker.patch.object(client, "create_query", return_value=query_id)

    run_mock = MagicMock(side_effect=run_behavior)
    mocker.patch.object(client, "_run", new=run_mock)
    gqr_mock = MagicMock(side_effect=gqr_behavior)
    mocker.patch.object(client, "get_query_result", new=gqr_mock)

    gql_mock = mocker.patch.object(client, "_gql")
    mocker.patch.object(gql_mock, "__aenter__")
    mocker.patch("dbtsl.api.graphql.client.sync.isinstance", return_value=True)

    kwargs = {"metrics": ["m1", "m2"], "group_by": ["gb"], "limit": 1}

    with client.session():
        result_table = client.query(**kwargs)  # pyright: ignore[reportUnknownVariableType]

    cq_mock.assert_called_once_with(**kwargs)

    run_mock.assert_has_calls(
        [
            call(op=GraphQLProtocol.get_query_result, raw_variables={"query_id": query_id, "page_num": 1}),
        ]
    )

    gqr_mock.assert_has_calls(
        [
            call(query_id=query_id, page_num=2),
            call(query_id=query_id, page_num=3),
            call(query_id=query_id, page_num=4),
        ]
    )

    assert result_table.equals(table, check_metadata=True)


# avoid raising mock warning related to mocking a context manager
@pytest.mark.filterwarnings("ignore::pytest_mock.PytestMockWarning")
def test_sync_poll_timeout_includes_status(mocker: MockerFixture) -> None:
    """Test that RetryTimeoutError includes the last known query status."""
    client = SyncGraphQLClient(server_host="test", environment_id=0, auth_token="test", timeout=0.001, lazy=False)

    compiled_result = QueryResult(
        query_id=QueryId("test-query-id"),
        status=QueryStatus.COMPILED,
        sql=None,
        error=None,
        total_pages=None,
        arrow_result=None,
    )

    run_mock = MagicMock(return_value=compiled_result)
    mocker.patch.object(client, "_run", new=run_mock)

    mocker.patch.object(client, "create_query", return_value=QueryId("test-query-id"))

    gql_mock = mocker.patch.object(client, "_gql")
    mocker.patch.object(gql_mock, "__aenter__")
    mocker.patch("dbtsl.api.graphql.client.sync.isinstance", return_value=True)

    with client.session():
        with pytest.raises(RetryTimeoutError) as exc_info:
            client.query(metrics=["m1"])

    assert exc_info.value.status == "COMPILED"


async def test_async_poll_timeout_includes_status(mocker: MockerFixture) -> None:
    """Test that RetryTimeoutError includes the last known query status (async)."""
    client = AsyncGraphQLClient(server_host="test", environment_id=0, auth_token="test", timeout=0.001, lazy=False)

    compiled_result = QueryResult(
        query_id=QueryId("test-query-id"),
        status=QueryStatus.COMPILED,
        sql=None,
        error=None,
        total_pages=None,
        arrow_result=None,
    )

    run_mock = AsyncMock(return_value=compiled_result)
    mocker.patch.object(client, "_run", new=run_mock)

    mocker.patch.object(client, "create_query", return_value=QueryId("test-query-id"), new_callable=AsyncMock)

    gql_mock = mocker.patch.object(client, "_gql")
    mocker.patch.object(gql_mock, "__aenter__", new_callable=AsyncMock)
    mocker.patch("dbtsl.api.graphql.client.asyncio.isinstance", return_value=True)

    async with client.session():
        with pytest.raises(RetryTimeoutError) as exc_info:
            await client.query(metrics=["m1"])

    assert exc_info.value.status == "COMPILED"
