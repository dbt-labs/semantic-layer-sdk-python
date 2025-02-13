from typing import Callable

import pytest

from dbtsl.api.graphql.client.asyncio import NEW_AIOHTTP  # pyright: ignore[reportAttributeAccessIssue]
from dbtsl.client.asyncio import AsyncSemanticLayerClient
from dbtsl.client.sync import SyncSemanticLayerClient
from dbtsl.error import ConnectTimeoutError, ExecuteTimeoutError, TimeoutError
from dbtsl.timeout import TimeoutOptions

from ..conftest import Credentials
from ..util import maybe_async_with, maybe_await
from .conftest import BothClients

AsyncTimeoutClientFactory = Callable[[TimeoutOptions], AsyncSemanticLayerClient]
SyncTimeoutClientFactory = Callable[[TimeoutOptions], SyncSemanticLayerClient]
TimeoutClientFactory = Callable[[TimeoutOptions], BothClients]


INF = 999999
# timeouts can't actually be zero otherwise the networking libraries break
# this shouldn't flake unless the packets somehow travel faster than light lol
ZERO = 0.0000000000001


@pytest.fixture(scope="module")
def async_client_factory(credentials: Credentials) -> TimeoutClientFactory:
    def factory(timeout: TimeoutOptions) -> AsyncSemanticLayerClient:
        return AsyncSemanticLayerClient(
            environment_id=credentials.environment_id,
            auth_token=credentials.token,
            host=credentials.host,
            timeout=timeout,
        )

    return factory


@pytest.fixture(scope="module")
def sync_client_factory(credentials: Credentials) -> TimeoutClientFactory:
    def factory(timeout: TimeoutOptions) -> SyncSemanticLayerClient:
        return SyncSemanticLayerClient(
            environment_id=credentials.environment_id,
            auth_token=credentials.token,
            host=credentials.host,
            timeout=timeout,
        )

    return factory


@pytest.fixture(scope="module")
async def client_factory(
    request: pytest.FixtureRequest,
    sync_client_factory: TimeoutClientFactory,
    async_client_factory: TimeoutClientFactory,
) -> TimeoutClientFactory:
    if request.param == "sync":
        return sync_client_factory
    return async_client_factory


pytestmark = pytest.mark.asyncio(scope="module")


# not testing async since `connect_timeout` doesn't work in aiohttp
async def test_connect_timeout(sync_client_factory: SyncTimeoutClientFactory) -> None:
    client = sync_client_factory(
        TimeoutOptions(
            connect_timeout=ZERO,
            total_timeout=INF,
            execute_timeout=INF,
            tls_close_timeout=INF,
        )
    )
    with pytest.raises(ConnectTimeoutError):
        with client.session():
            client.metrics()


async def test_execute_timeout(client_factory: TimeoutClientFactory) -> None:
    client = client_factory(
        TimeoutOptions(
            connect_timeout=INF,
            total_timeout=INF,
            execute_timeout=ZERO,
            tls_close_timeout=INF,
        )
    )
    with pytest.raises(TimeoutError) as exc_info:
        async with maybe_async_with(client.session()):
            await maybe_await(client.metrics())

    # Narrow down the error in case we can do it
    if isinstance(client, SyncSemanticLayerClient) or NEW_AIOHTTP:
        assert isinstance(exc_info.value, ExecuteTimeoutError)
