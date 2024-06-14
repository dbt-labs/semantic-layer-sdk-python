from contextlib import AbstractContextManager
from typing import Iterator, List, Optional

from typing_extensions import Self

from dbtsl.models import (
    Dimension,
    Measure,
    Metric,
)

class SyncGraphQLClient:
    def __init__(
        self,
        server_host: str,
        environment_id: int,
        auth_token: str,
        url_format: Optional[str] = None,
    ) -> None: ...
    def session(self) -> AbstractContextManager[Iterator[Self]]: ...
    def metrics(self) -> List[Metric]:
        """Get a list of all available metrics."""
        ...

    def dimensions(self, metrics: List[str]) -> List[Dimension]:
        """Get a list of all available dimensions for a given metric."""
        ...

    def measures(self, metrics: List[str]) -> List[Measure]:
        """Get a list of all available measures for a given metric."""
        ...
