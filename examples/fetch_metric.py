"""Fetch the values of a particular metric over time and display it."""

import asyncio
from argparse import ArgumentParser

from dbtsl.async_client import AsyncSemanticLayerClient


def get_arg_parser() -> ArgumentParser:
    p = ArgumentParser()

    p.add_argument("--env-id", required=True, help="The dbt environment ID", type=int)
    p.add_argument("--token", required=True, help="The API auth token")
    p.add_argument("--host", required=True, help="The API host")

    return p


async def main() -> None:
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    client = AsyncSemanticLayerClient(
        environment_id=args.env_id,
        auth_token=args.token,
        host=args.host,
    )

    async with client.session():
        df = await client.query(
            metrics=["customers_with_orders"],
            group_by=["metric_time"],
            order_by=["metric_time"],
            limit=15,
        )
        print(df)


if __name__ == "__main__":
    asyncio.run(main())
