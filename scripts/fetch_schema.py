import os

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from graphql import build_client_schema, get_introspection_query, print_schema

HOST = os.environ.get("SL_HOST", "semantic-layer.cloud.getdbt.com")


def main():
    """Fetch the GraphQL schema from the Semantic Layer servers."""
    transport = RequestsHTTPTransport(url=f"https://{HOST}/api/graphql", verify=True)
    client = Client(transport=transport)

    query = gql(get_introspection_query(descriptions=True))
    result = client.execute(query)

    client_schema = build_client_schema(result)  # type: ignore
    print(print_schema(client_schema))  # noqa: T201


if __name__ == "__main__":
    main()
