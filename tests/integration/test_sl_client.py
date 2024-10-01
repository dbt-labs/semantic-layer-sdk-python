from typing import AsyncIterator, Iterator, Union

import pytest
from pytest_subtests import SubTests

from dbtsl import OrderByDimension
from dbtsl.client.asyncio import AsyncSemanticLayerClient
from dbtsl.client.base import ADBC, GRAPHQL
from dbtsl.client.sync import SyncSemanticLayerClient

from ..conftest import Credentials
from ..util import maybe_await

BothClients = Union[SyncSemanticLayerClient, AsyncSemanticLayerClient]


@pytest.fixture(scope="module")
async def async_client(credentials: Credentials) -> AsyncIterator[AsyncSemanticLayerClient]:
    client = AsyncSemanticLayerClient(
        environment_id=credentials.environment_id,
        auth_token=credentials.token,
        host=credentials.host,
    )
    async with client.session():
        yield client


@pytest.fixture(scope="module")
def sync_client(credentials: Credentials) -> Iterator[SyncSemanticLayerClient]:
    client = SyncSemanticLayerClient(
        environment_id=credentials.environment_id,
        auth_token=credentials.token,
        host=credentials.host,
    )
    with client.session():
        yield client


@pytest.fixture(scope="module")
async def client(
    request: pytest.FixtureRequest, sync_client: SyncSemanticLayerClient, async_client: AsyncSemanticLayerClient
) -> BothClients:
    if request.param == "sync":
        return sync_client

    return async_client


pytestmark = pytest.mark.asyncio(scope="module")


# NOTE: grouping all these tests in one because they depend on each other, i.e
# dimensions depends on metrics etc
async def test_client_metadata(subtests: SubTests, client: BothClients) -> None:
    with subtests.test("metrics"):
        metrics = await maybe_await(client.metrics())
        assert len(metrics) > 0

    metric = metrics[0]

    with subtests.test("dimensions"):
        dims = await maybe_await(client.dimensions(metrics=[metric.name]))
        assert len(dims) > 0
        assert dims == metric.dimensions

    with subtests.test("entities"):
        entities = await maybe_await(client.entities(metrics=[metric.name]))
        assert len(entities) > 0
        assert entities == metric.entities

    with subtests.test("dimension_values"):
        dimension = metric.dimensions[0]
        dim_values = await maybe_await(client.dimension_values(metrics=[metric.name], group_by=dimension.name))
        assert len(dim_values) > 0

    with subtests.test("saved_queries"):
        sqs = await maybe_await(client.saved_queries())
        assert len(sqs) > 0


@pytest.mark.parametrize("api", [ADBC, GRAPHQL])
async def test_client_query_adhoc(api: str, client: BothClients) -> None:
    client._method_map["query"] = api  # type: ignore

    metrics = await maybe_await(client.metrics())
    assert len(metrics) > 0
    table = await maybe_await(
        client.query(
            metrics=[metrics[0].name],
            group_by=["metric_time"],
            order_by=["metric_time"],
            where=["1=1"],
            limit=1,
            read_cache=True,
        )
    )
    assert len(table) > 0


@pytest.mark.parametrize("api", [ADBC, GRAPHQL])
async def test_client_query_saved_query(api: str, client: BothClients) -> None:
    client._method_map["query"] = api  # type: ignore

    metrics = await maybe_await(client.metrics())
    assert len(metrics) > 0
    table = await maybe_await(
        client.query(
            saved_query="order_metrics",
            order_by=["metric_time"],
            where=["1=1"],
            limit=1,
            read_cache=True,
        )
    )
    assert len(table) > 0


async def test_client_compile_sql_adhoc_query(client: BothClients) -> None:
    metrics = await maybe_await(client.metrics())
    assert len(metrics) > 0

    sql = await maybe_await(
        client.compile_sql(
            metrics=[metrics[0].name],
            group_by=[metrics[0].dimensions[0].name],
            order_by=[metrics[0].dimensions[0].name],
            where=["1=1"],
            limit=1,
            read_cache=True,
        )
    )
    assert len(sql) > 0
    assert "SELECT" in sql


async def test_client_compile_sql_saved_query(client: BothClients) -> None:
    metrics = await maybe_await(client.metrics())
    assert len(metrics) > 0

    sql = await maybe_await(
        client.compile_sql(
            saved_query="order_metrics",
            order_by=["metric_time"],
            where=["1=1"],
            limit=1,
            read_cache=True,
        )
    )
    assert len(sql) > 0
    assert "SELECT" in sql
