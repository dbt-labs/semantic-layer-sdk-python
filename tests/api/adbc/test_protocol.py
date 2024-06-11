from dbt_sl_client.api.adbc.protocol import ADBCProtocol


def test_serialize_query_params_simple_query() -> None:
    params = ADBCProtocol._serialize_query_params(params={"metrics": ["a", "b"]})

    expected = 'metrics=["a", "b"]'
    assert params == expected


def test_serialize_query_params_complete_query() -> None:
    params = ADBCProtocol._serialize_query_params(
        params={
            "metrics": ["a", "b"],
            "group_by": ["dim_c"],
            "limit": 1,
            "order_by": ["dim_c"],
            "where": ['{{ Dimension("metric_time").grain("month") }} >= \'2017-03-09\''],
        }
    )

    expected = (
        'metrics=["a", "b"],group_by=["dim_c"],limit=1,order_by=["dim_c"],'
        'where=["{{ Dimension(\\"metric_time\\").grain(\\"month\\") }} >= \'2017-03-09\'"]'
    )
    assert params == expected


def test_get_query_sql_simple_query() -> None:
    sql = ADBCProtocol.get_query_sql(params={"metrics": ["a", "b"]})
    expected = 'SELECT * FROM {{ semantic_layer.query(metrics=["a", "b"]) }}'
    assert sql == expected
