from abc import ABC
from typing import Any, Generic, TypeVar

import dbtsl.env as env
from dbtsl.api.adbc.client.base import ADBCClientFactory, BaseADBCClient
from dbtsl.api.graphql.client.base import BaseGraphQLClient, GraphQLClientFactory

TGQLClient = TypeVar("TGQLClient", bound=BaseGraphQLClient)
TADBCClient = TypeVar("TADBCClient", bound=BaseADBCClient)


class BaseSemanticLayerClient(ABC, Generic[TGQLClient, TADBCClient]):
    """Base semantic layer client.

    This class has a `__getattr__` method which is a proxy to the underlying
    GraphQL and ADBC clients, whether they are sync or async. Concrete implementations
    of this class must be accompanied by a `.pyi` file for correct typing.
    """

    def __init__(
        self,
        environment_id: int,
        auth_token: str,
        host: str,
        gql_factory: GraphQLClientFactory[TGQLClient],
        adbc_factory: ADBCClientFactory[TADBCClient],
    ) -> None:
        """Initialize the Semantic Layer client.

        Args:
            environment_id: your dbt environment ID
            auth_token: the API auth token
            host: the Semantic Layer API host
            gql_factory: class of the underlying GQL client
            adbc_factory: class of the underlying ADBC client
        """
        self._has_session = False

        self._gql = gql_factory(
            server_host=host,
            environment_id=environment_id,
            auth_token=auth_token,
            url_format=env.GRAPHQL_URL_FORMAT,
        )
        self._adbc = adbc_factory(
            server_host=host,
            environment_id=environment_id,
            auth_token=auth_token,
            url_format=env.ADBC_URL_FORMAT,
        )

    def __getattr__(self, attr: str) -> Any:
        """Get methods from the underlying APIs.

        `query` goes through ADBC, while the rest goes through GQL.

        If the requested attribute is not a function, raise AttributeError.
        """
        if not self._has_session:
            raise ValueError(f"Cannot perform `{attr}`operation without opening a session first.")

        target = self._adbc if attr == "query" else self._gql

        attr_val = getattr(target, attr, None)

        if attr_val is None or not callable(attr_val):
            raise AttributeError()

        return attr_val
