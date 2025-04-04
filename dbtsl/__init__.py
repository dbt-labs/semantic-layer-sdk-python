# type: ignore
try:
    from dbtsl.client.sync import SyncSemanticLayerClient

    SemanticLayerClient = SyncSemanticLayerClient
except ImportError:

    def err_factory(*_args: object, **_kwargs: object) -> None:  # noqa: D103
        raise ImportError(
            "You are trying to use the default `SemanticLayerClient`, "
            "but it looks like the necessary dependencies were not installed. "
            "Did you forget to install the 'sync' optional dependencies?"
        )

    SemanticLayerClient = err_factory

import dbtsl.models  # noqa: F401
from dbtsl.api.shared.query_params import OrderByGroupBy, OrderByMetric

__all__ = ["SemanticLayerClient", "OrderByMetric", "OrderByGroupBy"]
