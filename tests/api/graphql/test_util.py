from dbtsl.api.graphql.util import normalize_query, render_query
from dbtsl.models.base import GraphQLFragment


def test_normalize_query() -> None:
    q = """

    myQuery {
        foo {
            baz
        bar
    } }
    """

    assert normalize_query(q) == "myQuery { foo { baz bar } }"


def test_render_query() -> None:
    template = """
    myQuery {
        ...&fragment
    }
    """
    dependencies = [
        GraphQLFragment(
            name="mainFrag",
            body="""
            fragment mainFrag on Test {
                foo
                bar
                dep {
                    ...depFrag
                }
            }
            """,
        ),
        GraphQLFragment(
            name="depFrag",
            body="""
            fragment depFrag on Dep {
                baz
            }
            """,
        ),
    ]

    expect = normalize_query("""
    myQuery {
        ...mainFrag
    }
    fragment mainFrag on Test {
        foo
        bar
        dep {
            ...depFrag
        }
    }
    fragment depFrag on Dep {
        baz
    }
    """)
    rendered = render_query(template, dependencies)
    assert normalize_query(expect) == rendered
