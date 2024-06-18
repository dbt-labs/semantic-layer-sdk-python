from typing import AsyncIterator, Iterator

import pytest

from dbtsl.api.graphql.client.asyncio import AsyncGraphQLClient
from dbtsl.api.graphql.client.sync import SyncGraphQLClient

from ..conftest import Credentials


@pytest.fixture(scope="session")
async def async_client(credentials: Credentials) -> AsyncIterator[AsyncGraphQLClient]:
    client = AsyncGraphQLClient(
        environment_id=credentials.environment_id,
        auth_token=credentials.token,
        server_host=credentials.host,
    )
    async with client.session():
        yield client


@pytest.fixture(scope="session")
def sync_client(credentials: Credentials) -> Iterator[SyncGraphQLClient]:
    client = SyncGraphQLClient(
        environment_id=credentials.environment_id,
        auth_token=credentials.token,
        server_host=credentials.host,
    )
    with client.session():
        yield client


def test_sync_client_lists_metrics_and_dimensions(sync_client: SyncGraphQLClient) -> None:
    metrics = sync_client.metrics()
    assert len(metrics) > 0
    dims = sync_client.dimensions(metrics=[metrics[0].name])
    assert len(dims) > 0


async def test_async_client_lists_metrics_and_dimensions(async_client: AsyncGraphQLClient) -> None:
    metrics = await async_client.metrics()
    assert len(metrics) > 0
    dims = await async_client.dimensions(metrics=[metrics[0].name])
    assert len(dims) > 0


async def test_async_client_query_works(async_client: AsyncGraphQLClient) -> None:
    metrics = await async_client.metrics()
    assert len(metrics) > 0
    table = await async_client.query(
        metrics=[metrics[0].name],
        group_by=["metric_time"],
        limit=1,
    )
    assert len(table) > 0
