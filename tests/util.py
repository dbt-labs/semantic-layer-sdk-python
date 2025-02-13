import inspect
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager
from typing import Awaitable, TypeVar, Union

T = TypeVar("T")


async def maybe_await(coro: Union[Awaitable[T], T]) -> T:
    """Await if it's a coroutine, otherwise just return.

    This is useful for reusing tests for async/sync logic by just treating everything as
    async.
    """
    if inspect.iscoroutine(coro):
        return await coro

    return coro  # type: ignore


def maybe_async_with(
    ctx: Union[AbstractAsyncContextManager[T], AbstractContextManager[T]],
) -> AbstractAsyncContextManager[T]:
    """Always get an async context manager from any input context manager.

    This allows you to run regular context managers in `async with` blocks.
    """
    if isinstance(ctx, AbstractAsyncContextManager):
        return ctx

    @asynccontextmanager
    async def async_ctx():
        with ctx as r:
            yield r

    return async_ctx()
