from abc import ABC
from typing import Any, Generic, Optional, TypeVar, Union

import dbtsl.env as env
from dbtsl.api.adbc.client.base import ADBCClientFactory, BaseADBCClient
from dbtsl.api.graphql.client.base import BaseGraphQLClient, GraphQLClientFactory
from dbtsl.timeout import TimeoutOptions

# TODO: have to type ignore, see: https://github.com/microsoft/pyright/issues/3497
TGQLClient = TypeVar("TGQLClient", bound=BaseGraphQLClient)  # type: ignore
TADBCClient = TypeVar("TADBCClient", bound=BaseADBCClient)

ADBC = "adbc"
GRAPHQL = "graphql"


class BaseSemanticLayerClient(ABC, Generic[TGQLClient, TADBCClient]):
    """Base semantic layer client.

    This class has a `__getattr__` method which is a proxy to the underlying
    GraphQL and ADBC clients, whether they are sync or async. Concrete implementations
    of this class must be accompanied by a `.pyi` file for correct typing.
    """

    _METHOD_MAP = {
        "compile_sql": GRAPHQL,
        "environment_info": GRAPHQL,
        "dimension_values": ADBC,
        "dimensions": GRAPHQL,
        "entities": GRAPHQL,
        "measures": GRAPHQL,
        "metrics": GRAPHQL,
        "query": ADBC,
        "saved_queries": GRAPHQL,
    }

    def __init__(
        self,
        environment_id: int,
        auth_token: str,
        host: str,
        gql_factory: GraphQLClientFactory[TGQLClient],
        adbc_factory: ADBCClientFactory[TADBCClient],
        timeout: Optional[Union[TimeoutOptions, float, int]] = None,
        *,
        lazy: bool,
    ) -> None:
        """Initialize the Semantic Layer client.

        Args:
            environment_id: your dbt environment ID
            auth_token: the API auth token
            host: the Semantic Layer API host
            gql_factory: class of the underlying GQL client
            adbc_factory: class of the underlying ADBC client
            timeout: `TimeoutOptions` or total timeout for the underlying GraphQL client.
            lazy: `lazy` for the underlying GraphQL client
        """
        self._has_session = False

        self._method_map = dict(self.__class__._METHOD_MAP)

        self._gql = gql_factory(
            server_host=host,
            environment_id=environment_id,
            auth_token=auth_token,
            url_format=env.GRAPHQL_URL_FORMAT,
            timeout=timeout,
            lazy=lazy,
        )
        self._adbc = adbc_factory(
            server_host=host,
            environment_id=environment_id,
            auth_token=auth_token,
            url_format=env.ADBC_URL_FORMAT,
        )

    @property
    def lazy(self) -> bool:
        """Whether metadata queries will be lazy or not."""
        return self._gql.lazy

    @lazy.setter
    def lazy(self, v: bool) -> None:
        """Set whether metadata queries will be lazy."""
        self._gql.lazy = v

    def __getattr__(self, attr: str) -> Any:
        """Get methods from the underlying APIs.

        `query` goes through ADBC, while the rest goes through GQL.

        If the requested attribute is not a function, raise AttributeError.
        """
        if not self._has_session:
            raise ValueError(f"Cannot perform `{attr}`operation without opening a session first.")

        target_str = self._method_map.get(attr, None)
        if target_str is None:
            raise AttributeError()

        assert target_str in (ADBC, GRAPHQL)
        target = self._gql if target_str == GRAPHQL else self._adbc

        attr_val = getattr(target, attr, None)  # pyright: ignore[reportUnknownArgumentType]

        if attr_val is None or not callable(attr_val):
            raise AttributeError()

        return attr_val
