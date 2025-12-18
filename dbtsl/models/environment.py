from dataclasses import dataclass
from enum import Enum

from dbtsl.models.base import BaseModel, FlexibleEnumMeta, GraphQLFragmentMixin


class SqlDialect(Enum, metaclass=FlexibleEnumMeta):
    """The SQL dialect of the semantic layer."""

    UNKNOWN = "UNKNOWN"
    SNOWFLAKE = "SNOWFLAKE"
    BIGQUERY = "BIGQUERY"
    POSTGRES = "POSTGRES"
    REDSHIFT = "REDSHIFT"
    DATABRICKS = "DATABRICKS"
    APACHE_SPARK = "APACHE_SPARK"
    DATABRICKS_SPARK = "DATABRICKS_SPARK"
    TRINO = "TRINO"
    ATHENA = "ATHENA"
    FABRIC = "FABRIC"
    SYNAPSE = "SYNAPSE"
    TERADATA = "TERADATA"


class SqlEngine(Enum, metaclass=FlexibleEnumMeta):
    """The SQL engine/warehouse type."""

    UNKNOWN = "UNKNOWN"
    BIGQUERY = "BIGQUERY"
    DUCKDB = "DUCKDB"
    REDSHIFT = "REDSHIFT"
    POSTGRES = "POSTGRES"
    SNOWFLAKE = "SNOWFLAKE"
    DATABRICKS = "DATABRICKS"
    TRINO = "TRINO"


@dataclass
class EnvironmentInfo(BaseModel, GraphQLFragmentMixin):
    """Information about the dbt Semantic Layer environment."""

    sql_dialect: SqlDialect
    has_metrics_defined: bool
    dialect: SqlEngine
    dialect_supported_by_slg: bool
