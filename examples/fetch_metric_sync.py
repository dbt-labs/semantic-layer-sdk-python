"""Fetch the values of a particular metric over time and display it."""

from argparse import ArgumentParser

from dbtsl import SemanticLayerClient


def get_arg_parser() -> ArgumentParser:
    p = ArgumentParser()

    p.add_argument("metric", help="The metric to fetch")
    p.add_argument("--env-id", required=True, help="The dbt environment ID", type=int)
    p.add_argument("--token", required=True, help="The API auth token")
    p.add_argument("--host", required=True, help="The API host")

    return p


def main() -> None:
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    client = SemanticLayerClient(
        environment_id=args.env_id,
        auth_token=args.token,
        host=args.host,
    )

    with client.session():
        table = client.query(
            metrics=[args.metric],
            group_by=["metric_time"],
            order_by=["metric_time"],
            limit=15,
        )
        print(table)


if __name__ == "__main__":
    main()
