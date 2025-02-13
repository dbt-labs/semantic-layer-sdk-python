import asyncio
from typing import AsyncIterator, Union

import pytest

from dbtsl.client.asyncio import AsyncSemanticLayerClient
from dbtsl.client.sync import SyncSemanticLayerClient

BothClients = Union[SyncSemanticLayerClient, AsyncSemanticLayerClient]


# generic method of requesting client that will automatically run once for sync
# and once for async
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "client" in metafunc.fixturenames:
        metafunc.parametrize("client", ["sync", "async"], indirect=True)

    if "client_factory" in metafunc.fixturenames:
        metafunc.parametrize("client_factory", ["sync", "async"], indirect=True)


# We need to manually tear down the event loop after the tests stop running.
# See: https://github.com/pytest-dev/pytest-asyncio/issues/200
@pytest.fixture(scope="session", autouse=True)
async def teardown() -> AsyncIterator[None]:
    yield

    event_loop = asyncio.get_running_loop()
    tasks = [t for t in asyncio.all_tasks(event_loop) if not t.done()]

    for task in tasks:
        task.cancel()

    try:
        await asyncio.wait(tasks)
    except asyncio.exceptions.CancelledError:
        pass
