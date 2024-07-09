from dbtsl.api.adbc.protocol import ADBCProtocol
from dbtsl.api.shared.query_params import DimensionValuesQueryParameters, QueryParameters


def test_serialize_query_params_simple_query() -> None:
    params = ADBCProtocol._serialize_params_dict({"metrics": ["a", "b"]}, QueryParameters.__optional_keys__)

    expected = 'metrics=["a", "b"]'
    assert params == expected


def test_serialize_query_params_dimensions_query() -> None:
    params = ADBCProtocol._serialize_params_dict(
        {"metrics": ["a", "b"], "group_by": "c"}, DimensionValuesQueryParameters.__optional_keys__
    )

    expected = 'group_by="c",metrics=["a", "b"]'
    assert params == expected


def test_serialize_query_params_complete_query() -> None:
    params = ADBCProtocol._serialize_params_dict(
        {
            "metrics": ["a", "b"],
            "group_by": ["dim_c"],
            "limit": 1,
            "order_by": ["dim_c"],
            "where": ['{{ Dimension("metric_time").grain("month") }} >= \'2017-03-09\''],
            "read_cache": False,
        },
        QueryParameters.__optional_keys__,
    )

    expected = (
        'group_by=["dim_c"],limit=1,metrics=["a", "b"],order_by=["dim_c"],read_cache=False,'
        'where=["{{ Dimension(\\"metric_time\\").grain(\\"month\\") }} >= \'2017-03-09\'"]'
    )
    assert params == expected


def test_get_query_sql_simple_query() -> None:
    sql = ADBCProtocol.get_query_sql(params={"metrics": ["a", "b"]})
    expected = 'SELECT * FROM {{ semantic_layer.query(metrics=["a", "b"]) }}'
    assert sql == expected


def test_get_query_sql_dimension_values_query() -> None:
    sql = ADBCProtocol.get_dimension_values_sql(params={"metrics": ["a", "b"]})
    expected = 'SELECT * FROM {{ semantic_layer.dimension_values(metrics=["a", "b"]) }}'
    assert sql == expected
