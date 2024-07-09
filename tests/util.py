import inspect
from typing import Awaitable, TypeVar, Union

T = TypeVar("T")


async def maybe_await(coro: Union[Awaitable[T], T]) -> T:
    """Await if it's a coroutine, otherwise just return."""
    if inspect.iscoroutine(coro):
        return await coro

    return coro  # type: ignore
