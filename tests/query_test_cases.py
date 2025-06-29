from typing import List

from dbtsl import OrderByGroupBy
from dbtsl.api.shared.query_params import GroupByParam, GroupByType, QueryParameters

TEST_QUERIES: List[QueryParameters] = [
    # ad hoc query, all parameters
    {
        "metrics": ["order_total"],
        "group_by": ["customer__customer_type"],
        "order_by": ["customer__customer_type"],
        "where": ["1=1"],
        "limit": 1,
        "read_cache": True,
    },
    # ad hoc query, only metric
    {
        "metrics": ["order_total"],
    },
    # ad hoc query, only group by
    {
        "group_by": ["customer__customer_type"],
    },
    # ad hoc query, metric and group by
    {
        "metrics": ["order_total"],
        "group_by": ["customer__customer_type"],
    },
    # saved query, all parameters
    {
        "saved_query": "order_metrics",
        "order_by": [OrderByGroupBy(name="metric_time", grain="day")],
        "where": ["1=1"],
        "limit": 1,
        "read_cache": True,
    },
    # saved query, no parameters
    {
        "saved_query": "order_metrics",
    },
    # group by param object
    {
        "metrics": ["order_total"],
        "group_by": [GroupByParam(name="customer__customer_type", grain="month", type=GroupByType.DIMENSION)],
    },
    # multiple group by param objects
    {
        "metrics": ["order_total"],
        "group_by": [
            GroupByParam(name="metric_time", grain="month", type=GroupByType.DIMENSION),
            GroupByParam(name="metric_time", grain="week", type=GroupByType.DIMENSION),
        ],
    },
]
