import os
from dataclasses import dataclass
from typing import Callable, Union, cast

import pytest
from gql import Client, gql


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--server-schema",
        action="store",
        required=True,
        help="The GraphQL server schema file",
    )


@pytest.fixture(scope="session")
def server_schema_path(pytestconfig: pytest.Config) -> Union[str, None]:
    # the typing on this is weird...
    return cast(Union[str, None], pytestconfig.getoption("server_schema"))


@pytest.fixture(scope="session")
def server_schema(server_schema_path: str) -> str:
    with open(server_schema_path, "r") as schema_file:
        schema_str = schema_file.read()

    return schema_str


QueryValidator = Callable[[str], None]


@pytest.fixture(scope="session")
def validate_query(server_schema: str) -> QueryValidator:
    """Returns a validator function which ensures the query is valid against the server schema."""
    gql_client = Client(schema=server_schema)

    def validator(query_str: str) -> None:
        query_doc = gql(query_str)
        gql_client.validate(document=query_doc)

    return validator


@dataclass
class Credentials:
    """Credentials used for integration testing."""

    host: str
    environment_id: int
    token: str

    @classmethod
    def from_env(cls) -> "Credentials":
        """Get test credentials from environment variables.

        The following environment variables will be consumed:
        - SL_HOST
        - SL_TOKEN
        - SL_ENV_ID
        """
        return cls(
            host=os.environ["SL_HOST"],
            token=os.environ["SL_TOKEN"],
            environment_id=int(os.environ["SL_ENV_ID"]),
        )


@pytest.fixture(scope="session")
def credentials() -> Credentials:
    return Credentials.from_env()
