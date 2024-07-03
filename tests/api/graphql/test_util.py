from dbtsl.api.graphql.util import normalize_query


def test_normalize_query() -> None:
    q = """

    myQuery {
        foo {
            baz
        bar
    } }
    """

    assert normalize_query(q) == "myQuery { foo { baz bar } }"
