# type: ignore
try:
    from dbtsl.client.asyncio import AsyncSemanticLayerClient
except ImportError:

    def err_factory(*_args: object, **_kwargs: object) -> None:  # noqa: D103
        raise ImportError(
            "You are trying to use the asyncio `AsyncSemanticLayerClient`, "
            "but it looks like the necessary dependencies were not installed. "
            "Did you forget to install the 'async' optional dependencies?"
        )

    AsyncSemanticLayerClient = err_factory

import dbtsl.models  # noqa: F401

__all__ = [
    "AsyncSemanticLayerClient",
]
