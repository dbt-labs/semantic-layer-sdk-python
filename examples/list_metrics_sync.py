"""Fetch all available metrics from the metadata API and display them."""

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
    )

    with client.session():
        metrics = client.metrics()
        for m in metrics:
            print(f"📈 {m.name}")
            print(f"     type={m.type}")
            print(f"     description={m.description}")

            print("     dimensions=[")
            for dim in m.dimensions:
                print(f"        {dim.name},")
            print("     ]")

            print("     measures=[")
            for measure in m.measures:
                print(f"        {measure.name},")
            print("     ]")

            print("     entities=[")
            for entity in m.entities:
                print(f"        {entity.name},")
            print("     ]")


if __name__ == "__main__":
    main()
