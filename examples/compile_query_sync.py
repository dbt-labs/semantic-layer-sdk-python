"""Compile a query and display the SQL."""

from argparse import ArgumentParser

from dbtsl import SemanticLayerClient


def get_arg_parser() -> ArgumentParser:
    p = ArgumentParser()

    p.add_argument("metric", help="The metric to fetch")
    p.add_argument("group_by", help="A dimension to group by")
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
        sql = client.compile_sql(
            metrics=[args.metric],
            group_by=[args.group_by],
            limit=15,
        )
        print(f"Compiled SQL for {args.metric} grouped by {args.group_by}, limit 15:")
        print(sql)


if __name__ == "__main__":
    main()
