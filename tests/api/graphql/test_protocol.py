from pytest_subtests import SubTests

from dbt_sl_client.api.graphql.protocol import GraphQLProtocol
from dbt_sl_client.models.metric import Metric, MetricType

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


# NOTE: the following tests will validate that the client can appropriately
# parse an incoming server response. The "raw" responses were taken directly
# from an instance of metricflow-server via Postman.
def test_metrics_parses_server_respose() -> None:
    raw = {
        "metrics": [
            {"name": "A", "description": "a", "type": "CUMULATIVE"},
            {"name": "B", "description": "b", "type": "RATIO"},
        ]
    }
    parsed = GraphQLProtocol.list_metrics.parse_response(raw)
    assert parsed == [
        Metric(name="A", description="a", type=MetricType.CUMULATIVE),
        Metric(name="B", description="b", type=MetricType.RATIO),
    ]
