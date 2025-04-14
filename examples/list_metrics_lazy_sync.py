"""Lazily fetch all available metrics from the metadata API display only the dimensions of certain metrics."""

from argparse import ArgumentParser

from dbtsl import SemanticLayerClient


def get_arg_parser() -> ArgumentParser:
    p = ArgumentParser()

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
        lazy=True,
    )

    with client.session():
        metrics = client.metrics()
        for i, m in enumerate(metrics):
            print(f"📈 {m.name}")
            print(f"     type={m.type}")
            print(f"     description={m.description}")

            assert len(m.dimensions) == 0

            # skip if index is odd
            if i & 1:
                print("     dimensions=skipped")
                continue

            # load dimensions only if even
            m.load_dimensions()

            print("     dimensions=[")
            for dim in m.dimensions:
                print(f"        {dim.name},")
            print("     ]")


if __name__ == "__main__":
    main()
