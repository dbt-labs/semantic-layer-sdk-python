try:
    from dbtsl.client.sync import SyncSemanticLayerClient

    SemanticLayerClient = SyncSemanticLayerClient
except ImportError:

    def err_factory(*args, **kwargs) -> None:  # noqa: D103
        raise ImportError(
            "You are trying to use the default `SemanticLayerClient`, "
            "but it looks like the necessary dependencies were not installed. "
            "Did you forget to install the 'sync' optional dependencies?"
        )

    SemanticLayerClient = err_factory

__all__ = [
    "SemanticLayerClient"
]
