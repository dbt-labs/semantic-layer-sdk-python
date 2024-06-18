"""All global environment configurations for the SDK live here."""

import os
import platform as pl
from dataclasses import dataclass

from dbtsl.__about__ import VERSION as DBTSL_VERSION

DEFAULT_GRAPHQL_URL_FORMAT = "https://{server_host}/api/graphql"
DEFAULT_ADBC_URL_FORMAT = "grpc+tls://{server_host}:443"

GRAPHQL_URL_FORMAT = os.environ.get("DBT_SL_GRAPHQL_URL_FORMAT", DEFAULT_GRAPHQL_URL_FORMAT)
ADBC_URL_FORMAT = os.environ.get("DBT_SL_ADBC_URL_FORMAT", DEFAULT_ADBC_URL_FORMAT)


@dataclass
class Platform:
    """Identify the current platform."""

    anonymous = False

    arch = pl.machine()
    os = pl.system()
    py_impl = pl.python_implementation()
    py_version = pl.python_version()

    @property
    def identity(self) -> str:
        """Return the identity string of the current platform."""
        if self.anonymous:
            return "anonymous"
        return f"{self.os} ({self.arch}) / Python {self.py_version} ({self.py_impl})"

    @property
    def user_agent(self) -> str:
        """Get a User-Agent header based on the current platform."""
        return f"dbt-sl-sdk-python {DBTSL_VERSION} / {self.identity}"


PLATFORM = Platform()
