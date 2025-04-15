# dbt Semantic Layer SDK for Python

A library for easily accessing [dbt's Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl/) via Python.

## Installation

To install the SDK, you'll need to specify optional dependencies depending on whether you want to use it synchronously (backed by [requests](https://github.com/psf/requests/)) or via [asyncio](https://docs.python.org/3/library/asyncio.html) (backed by [aiohttp](https://github.com/aio-libs/aiohttp/)).

```
# Sync installation
pip install "dbt-sl-sdk[sync]"

# Async installation
pip install "dbt-sl-sdk[async]"
```

## Usage

To run operations against the Semantic Layer APIs, just instantiate a `SemanticLayerClient` with your specific connection parameters ([learn more](https://docs.getdbt.com/docs/dbt-cloud-apis/sl-api-overview)):

```python
from dbtsl import SemanticLayerClient

client = SemanticLayerClient(
    environment_id=123,
    auth_token="<your-semantic-layer-api-token>",
    host="semantic-layer.cloud.getdbt.com",
)

# query the first metric by `metric_time`
def main():
    with client.session():
        metrics = client.metrics()
        table = client.query(
            metrics=[metrics[0].name],
            group_by=["metric_time"],
        )
        print(table)

main()
```

Note that all method calls that will reach out to the APIs need to be within a `client.session()` context manager. By using a session, the client can connect to the APIs only once, and reuse the same connection between API calls.

### asyncio

If you're using asyncio, import `AsyncSemanticLayerClient` from `dbtsl.asyncio`. The APIs of `SemanticLayerClient` and `AsyncSemanticLayerClient` are the same. The only difference is that the asyncio version has `async` methods which need to be `await`ed.

That same sync example can be converted into asyncio code like so:

```python
import asyncio
from dbtsl.asyncio import AsyncSemanticLayerClient

client = AsyncSemanticLayerClient(
    environment_id=123,
    auth_token="<your-semantic-layer-api-token>",
    host="semantic-layer.cloud.getdbt.com",
)

async def main():
    async with client.session():
        metrics = await client.metrics()
        table = await client.query(
            metrics=[metrics[0].name],
            group_by=["metric_time"],
        )
        print(table)

asyncio.run(main())
```

### Integrating with dataframe libraries

By design, the SDK returns all query data as [pyarrow](https://arrow.apache.org/docs/python/index.html) tables. If you wish to use the data with libraries like [pandas](https://pandas.pydata.org/) or [polars](https://pola.rs/), you need to manually download them and convert the data into their format.

If you're using pandas:
```python
# ... initialize client

arrow_table = client.query(...)
pandas_df = arrow_table.to_pandas()
```

If you're using polars:
```python
import polars as pl

# ... initialize client

arrow_table = client.query(...)
polars_df = pl.from_arrow(arrow_table)
```

### Lazy loading

By default, the SDK will eagerly request for lists of nested objects. For example, in the list of `Metric` returned by `client.metrics()`, each metric will contain the list of its dimensions, entities and measures. This is convenient in most cases, but can make your returned data really large in case your project is really large, which can slow things down. 

It is possible to set the client to `lazy=True`, which will make it skip populating nested object lists unless you explicitly load ask for it on a per-model basis. Check our [lazy loading example](./examples/list_metrics_lazy_sync.py) to learn more.

### More examples

Check out our [usage examples](./examples/) to learn more.


### Disabling telemetry

By default, dbt the SDK sends some [platform-related information](./dbtsl/env.py) to dbt Labs. If you'd like to opt out, do
```python
from dbtsl.env import PLATFORM
PLATFORM.anonymous = True

# ... initialize client
```


## Contributing

If you're interested in contributing to this project, check out our [contribution guidelines](./CONTRIBUTING.md).
