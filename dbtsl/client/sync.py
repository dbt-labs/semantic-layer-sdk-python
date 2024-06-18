from contextlib import contextmanager
from typing import Iterator

from typing_extensions import Self

from dbtsl.api.adbc.client.sync import SyncADBCClient
from dbtsl.api.graphql.client.sync import SyncGraphQLClient
from dbtsl.client.base import BaseSemanticLayerClient


class SyncSemanticLayerClient(BaseSemanticLayerClient[SyncGraphQLClient, SyncADBCClient]):  # type: ignore
    """A sync semantic layer client, backed by requests.

    It performs operations by using the most appropriate API depending on the
    operation. For example, dataframes are fetched via ADBC while metadata
    is fetched via GraphQL.

    If you want to override this behavior (say, get dataframes via GraphQL),
    please use the API clients directly.
    """

    def __init__(
        self,
        environment_id: int,
        auth_token: str,
        host: str,
    ) -> None:
        """Initialize the Semantic Layer client.

        Args:
            environment_id: your dbt environment ID
            auth_token: the API auth token
            host: the Semantic Layer API host
        """
        super().__init__(
            environment_id=environment_id,
            auth_token=auth_token,
            host=host,
            gql_factory=SyncGraphQLClient,
            adbc_factory=SyncADBCClient,
        )

    @contextmanager
    def session(self) -> Iterator[Self]:
        """Establish a connection with the dbt Semantic Layer's servers."""
        if self._has_session:
            raise ValueError("Cannot open session within session.")

        with self._gql.session(), self._adbc.session():
            self._has_session = True
            yield self
            self._has_session = False
