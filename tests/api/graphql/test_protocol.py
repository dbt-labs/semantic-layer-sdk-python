from typing import Any, Dict, List, Tuple

import pytest

from dbtsl.api.graphql.protocol import GraphQLProtocol

from ...conftest import QueryValidator
from ...query_test_cases import TEST_QUERIES

VARIABLES: dict[str, list[dict[str, Any]]] = {
    "metrics": [{}],
    "dimensions": [{"metrics": ["m"]}],
    "measures": [{"metrics": ["m"]}],
    "entities": [{"metrics": ["m"]}],
    "saved_queries": [{}],
    "get_query_result": [{"query_id": 1}],
    "create_query": TEST_QUERIES,
    "compile_sql": TEST_QUERIES,
}

TestCase = Tuple[str, Dict[str, Any]]
TEST_CASES: List[TestCase] = []

for op_name in dir(GraphQLProtocol):
    if op_name.startswith("__"):
        continue

    tested_vars = VARIABLES.get(op_name)
    assert tested_vars is not None, f"No test vars to use for testing GraphQLProtocol.{op_name}"

    for variables in tested_vars:
        TEST_CASES.append((op_name, variables))


def get_test_id(test_case: TestCase) -> str:
    return test_case[0]


@pytest.mark.parametrize("test_case", TEST_CASES, ids=get_test_id)
def test_queries_are_valid(test_case: TestCase, validate_query: QueryValidator) -> None:
    """Test all GraphQL queries in `GraphQLProtocol` are valid against the server schema.

    This test dynamically iterates over `GraphQLProtocol` so whenever a new method is
    added it will get tested automatically. The test will fail if there's no entry in VARIABLES
    for it.
    """
    op_name, raw_variables = test_case

    op = getattr(GraphQLProtocol, op_name)
    query = op.get_request_text()
    variable_values = op.get_request_variables(environment_id=123, variables=raw_variables)
    validate_query(query, variable_values)
