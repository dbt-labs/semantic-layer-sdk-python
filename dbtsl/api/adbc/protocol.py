import json
from typing import Any, FrozenSet, Mapping

from dbtsl.api.shared.query_params import DimensionValuesQueryParameters, QueryParameters, validate_query_parameters


class ADBCProtocol:
    """The protocol for the Arrow Flight dataframe API."""

    @staticmethod
    def _serialize_params_dict(params: Mapping[str, Any], param_names: FrozenSet[str]) -> str:
        param_names_sorted = list(param_names)
        param_names_sorted.sort()

        def append_param_if_exists(p_str: str, p_name: str) -> str:
            p_value = params.get(p_name)
            if p_value is not None:
                if isinstance(p_value, bool):
                    dumped = str(p_value)
                else:
                    dumped = json.dumps(p_value)
                p_str += f"{p_name}={dumped},"
            return p_str

        serialized_params = ""
        for param_name in param_names_sorted:
            serialized_params = append_param_if_exists(serialized_params, param_name)

        serialized_params = serialized_params.strip(",")

        return serialized_params

    @classmethod
    def get_query_sql(cls, params: QueryParameters) -> str:
        """Get the SQL that will be sent via Arrow Flight to the server based on query parameters."""
        validate_query_parameters(params)
        serialized_params = cls._serialize_params_dict(params, QueryParameters.__optional_keys__)
        return f"SELECT * FROM {{{{ semantic_layer.query({serialized_params}) }}}}"

    @classmethod
    def get_dimension_values_sql(cls, params: DimensionValuesQueryParameters) -> str:
        """Get the SQL that will be sent via Arrow Flight to the server based on dimension values query parameters."""
        serialized_params = cls._serialize_params_dict(params, DimensionValuesQueryParameters.__optional_keys__)
        return f"SELECT * FROM {{{{ semantic_layer.dimension_values({serialized_params}) }}}}"
