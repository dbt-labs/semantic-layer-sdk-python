from dbtsl.api.adbc.protocol import ADBCProtocol
from dbtsl.api.shared.query_params import OrderByGroupBy, OrderByMetric
from dbtsl.models.time import TimeGranularity


def test_serialize_val_basic_values() -> None:
    assert ADBCProtocol._serialize_val(1) == "1"
    assert ADBCProtocol._serialize_val("a") == '"a"'
    assert ADBCProtocol._serialize_val(True) == "True"
    assert ADBCProtocol._serialize_val(False) == "False"
    assert ADBCProtocol._serialize_val(["a", "b"]) == '["a","b"]'


def test_serialize_val_OrderByMetric() -> None:
    assert ADBCProtocol._serialize_val(OrderByMetric(name="m", descending=False)) == 'Metric("m")'
    assert ADBCProtocol._serialize_val(OrderByMetric(name="m", descending=True)) == 'Metric("m").descending(True)'


def test_serialize_val_OrderByGroupBy() -> None:
    assert ADBCProtocol._serialize_val(OrderByGroupBy(name="m", grain=None, descending=False)) == 'Dimension("m")'
    assert (
        ADBCProtocol._serialize_val(OrderByGroupBy(name="m", grain=None, descending=True))
        == 'Dimension("m").descending(True)'
    )
    assert (
        ADBCProtocol._serialize_val(OrderByGroupBy(name="m", grain=TimeGranularity.DAY, descending=False))
        == 'Dimension("m").grain("day")'
    )
    assert (
        ADBCProtocol._serialize_val(OrderByGroupBy(name="m", grain=TimeGranularity.WEEK, descending=True))
        == 'Dimension("m").grain("week").descending(True)'
    )
    assert (
        ADBCProtocol._serialize_val(OrderByGroupBy(name="m", grain="custom_grain"))
        == 'Dimension("m").grain("custom_grain")'
    )


def test_serialize_query_params_metrics() -> None:
    params = ADBCProtocol._serialize_params_dict({"metrics": ["a", "b"]}, ["metrics"])

    expected = 'metrics=["a","b"]'
    assert params == expected


def test_serialize_query_params_metrics_group_by() -> None:
    params = ADBCProtocol._serialize_params_dict({"metrics": ["a", "b"], "group_by": "c"}, ["metrics", "group_by"])

    expected = 'group_by="c",metrics=["a","b"]'
    assert params == expected


def test_serialize_query_params_complete_query() -> None:
    params = ADBCProtocol._serialize_params_dict(
        {
            "metrics": ["a", "b"],
            "group_by": ["dim_c"],
            "limit": 1,
            "order_by": [OrderByMetric(name="a"), OrderByGroupBy(name="dim_c", grain=None)],
            "where": ['{{ Dimension("metric_time").grain("month") }} >= \'2017-03-09\''],
            "read_cache": False,
        },
        ["metrics", "group_by", "limit", "order_by", "where", "read_cache"],
    )

    expected = (
        'group_by=["dim_c"],limit=1,metrics=["a","b"],order_by=[Metric("a"),Dimension("dim_c")],read_cache=False,'
        'where=["{{ Dimension(\\"metric_time\\").grain(\\"month\\") }} >= \'2017-03-09\'"]'
    )
    assert params == expected


def test_get_query_sql_simple_query() -> None:
    sql = ADBCProtocol.get_query_sql(params={"metrics": ["a", "b"], "order_by": ["-a"]})
    expected = (
        'SELECT * FROM {{ semantic_layer.query(metrics=["a","b"],'
        'order_by=[Metric("a").descending(True)],read_cache=True) }}'
    )
    assert sql == expected


def test_get_query_sql_dimension_values_query() -> None:
    sql = ADBCProtocol.get_dimension_values_sql(params={"metrics": ["a", "b"]})
    expected = 'SELECT * FROM {{ semantic_layer.dimension_values(metrics=["a","b"]) }}'
    assert sql == expected
