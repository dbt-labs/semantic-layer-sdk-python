from typing import List

from dbtsl import OrderByGroupBy
from dbtsl.api.shared.query_params import QueryParameters

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
]
