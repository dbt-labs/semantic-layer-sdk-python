import json

from dbt_sl_client.api.shared.query_params import QueryParameters


class ADBCProtocol:
    """The protocol for the Arrow Flight dataframe API."""

    @staticmethod
    def _serialize_query_params(params: QueryParameters) -> str:
        serialized_params = ""

        def append_param_if_exists(p_str: str, p_name: str) -> str:
            p_value = params.get(p_name)
            if p_value is not None:
                p_str += f"{p_name}={json.dumps(p_value)},"
            return p_str

        serialized_params = append_param_if_exists(serialized_params, "metrics")
        serialized_params = append_param_if_exists(serialized_params, "group_by")
        serialized_params = append_param_if_exists(serialized_params, "limit")
        serialized_params = append_param_if_exists(serialized_params, "order_by")
        serialized_params = append_param_if_exists(serialized_params, "where")

        serialized_params = serialized_params.strip(",")

        return serialized_params

    @classmethod
    def get_query_sql(cls, params: QueryParameters) -> str:
        """Get the SQL that will be sent via Arrow Flight to the server based on query parameters."""
        serialized_params = cls._serialize_query_params(params)
        return f"SELECT * FROM {{{{ semantic_layer.query({serialized_params}) }}}}"
