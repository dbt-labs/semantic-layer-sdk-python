import inspect
from typing import AsyncIterator, Awaitable, Iterator, TypeVar, Union

import pytest

from dbtsl.api.graphql.client.asyncio import AsyncGraphQLClient
from dbtsl.api.graphql.client.sync import SyncGraphQLClient

from ..conftest import Credentials

BothClients = Union[SyncGraphQLClient, AsyncGraphQLClient]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "client" in metafunc.fixturenames:
        metafunc.parametrize("client", ["sync", "async"], indirect=True)


T = TypeVar("T")


async def maybe_await(coro: Union[Awaitable[T], T]) -> T:
    if inspect.iscoroutine(coro):
        return await coro

    return coro  # type: ignore


@pytest.fixture(scope="module")
async def async_client(credentials: Credentials) -> AsyncIterator[AsyncGraphQLClient]:
    client = AsyncGraphQLClient(
        environment_id=credentials.environment_id,
        auth_token=credentials.token,
        server_host=credentials.host,
    )
    async with client.session():
        yield client


@pytest.fixture(scope="module")
def sync_client(credentials: Credentials) -> Iterator[SyncGraphQLClient]:
    client = SyncGraphQLClient(
        environment_id=credentials.environment_id,
        auth_token=credentials.token,
        server_host=credentials.host,
    )
    with client.session():
        yield client


@pytest.fixture(scope="module")
async def client(
    request: pytest.FixtureRequest, sync_client: SyncGraphQLClient, async_client: AsyncGraphQLClient
) -> BothClients:
    if request.param == "sync":
        return sync_client

    return async_client


pytestmark = pytest.mark.asyncio(scope="module")


async def test_client_lists_metrics_dimensions_entities(client: BothClients) -> None:
    metrics = await maybe_await(client.metrics())
    assert len(metrics) > 0

    dims = await maybe_await(client.dimensions(metrics=[metrics[0].name]))
    assert len(dims) > 0
    assert dims == metrics[0].dimensions

    entities = await maybe_await(client.entities(metrics=[metrics[0].name]))
    assert len(entities) > 0
    assert entities == metrics[0].entities


async def test_client_lists_saved_queries(client: BothClients) -> None:
    sqs = await maybe_await(client.saved_queries())
    assert len(sqs) > 0


async def test_client_query_works(client: BothClients) -> None:
    metrics = await maybe_await(client.metrics())
    assert len(metrics) > 0
    table = await maybe_await(
        client.query(
            metrics=[metrics[0].name],
            group_by=["metric_time"],
            limit=1,
        )
    )
    assert len(table) > 0
