"""All global environment configurations for the SDK live here."""

import os

DEFAULT_GRAPHQL_URL_FORMAT = "https://{server_host}/api/graphql"
DEFAULT_ADBC_URL_FORMAT = "grpc+tls://{server_host}:443"

GRAPHQL_URL_FORMAT = os.environ.get("DBT_SL_GRAPHQL_URL_FORMAT", DEFAULT_GRAPHQL_URL_FORMAT)
ADBC_URL_FORMAT = os.environ.get("DBT_SL_ADBC_URL_FORMAT", DEFAULT_ADBC_URL_FORMAT)
