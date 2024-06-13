# dbt Semantic Layer SDK for Python

> 🧪 This library is still experimental and it's not feature complete yet.

A library for easily accessing [dbt's Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl/) via Python.

## Installation

To install the SDK, you'll need to specify optional dependencies depending on whether you want to use it synchronously (backed by [requests](https://github.com/psf/requests/)) or via [asyncio](https://docs.python.org/3/library/asyncio.html) (backed by [aiohttp](https://github.com/aio-libs/aiohttp/)).

```
# Sync installation
pip install dbt-sl-sdk[sync]

# Async installation
pip install dbt-sl-sdk[async]
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

def main():
    with client.session():
        print(client.metrics())

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
        print(await client.metrics())

asyncio.run(main())
```

### More examples

Check out our [usage examples](./examples/) to learn more.


## Contributing

If you're interested in contributing to this project, check out our [contribution guidelines](./CONTRIBUTING.md).
