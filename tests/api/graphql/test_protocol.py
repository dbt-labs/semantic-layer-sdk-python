from pytest_subtests import SubTests

from dbtsl.api.graphql.protocol import GraphQLProtocol

from ...conftest import QueryValidator


def test_queries_are_valid(subtests: SubTests, validate_query: QueryValidator) -> None:
    """Test all GraphQL queries in `GraphQLProtocol` are valid against the server schema.

    This test dynamically iterates over `GraphQLProtocol` sowhenever a new method is
    added it will get tested automatically.
    """
    prop_names = dir(GraphQLProtocol)
    for prop_name in prop_names:
        if prop_name.startswith("__"):
            continue

        prop_val = getattr(GraphQLProtocol, prop_name)
        with subtests.test(msg=f"GraphQLProtocol.{prop_name}"):
            query = prop_val.get_request_text()
            validate_query(query)
