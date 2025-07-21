import dataclasses
import json
from typing import Any, List, Mapping

from dbtsl.api.shared.query_params import (
    DimensionValuesQueryParameters,
    GroupByParam,
    GroupByType,
    OrderByGroupBy,
    OrderByMetric,
    QueryParameters,
    validate_query_parameters,
)


class ADBCProtocol:
    """The protocol for the Arrow Flight dataframe API."""

    @classmethod
    def _serialize_val(cls, val: Any) -> str:
        if isinstance(val, bool):
            return str(val)

        if isinstance(val, list):
            list_str = ",".join(cls._serialize_val(list_val) for list_val in val)  # pyright: ignore[reportUnknownVariableType]
            return f"[{list_str}]"

        if isinstance(val, OrderByMetric):
            m = f'Metric("{val.name}")'
            if val.descending:
                m += ".descending(True)"
            return m

        if isinstance(val, OrderByGroupBy):
            d = f'Dimension("{val.name}")'
            if val.grain:
                grain_str = val.grain.lower()
                d += f'.grain("{grain_str}")'
            if val.descending:
                d += ".descending(True)"
            return d

        if isinstance(val, GroupByParam):
            g: str = ""
            if val.type == GroupByType.DIMENSION:
                g = f'Dimension("{val.name}")'
            elif val.type == GroupByType.ENTITY:
                g = f'Entity("{val.name}")'
            else:  # val.type == GroupByType.TIME_DIMENSION
                return f'TimeDimension("{val.name}", "{val.grain}")'
            if val.grain:
                grain_str = val.grain.lower()
                g += f'.grain("{grain_str}")'
            return g

        return json.dumps(val)

    @classmethod
    def _serialize_params_dict(cls, params: Mapping[str, Any], param_names: List[str]) -> str:
        param_names_sorted = list(param_names)
        param_names_sorted.sort()

        def append_param_if_exists(p_str: str, p_name: str) -> str:
            p_value = params.get(p_name)
            if p_value is not None:
                serialized = cls._serialize_val(p_value)
                p_str += f"{p_name}={serialized},"
            return p_str

        serialized_params = ""
        for param_name in param_names_sorted:
            serialized_params = append_param_if_exists(serialized_params, param_name)

        serialized_params = serialized_params.strip(",")

        return serialized_params

    @classmethod
    def get_query_sql(cls, params: QueryParameters) -> str:
        """Get the SQL that will be sent via Arrow Flight to the server based on query parameters."""
        strict_params = validate_query_parameters(params)
        params_fields = [f.name for f in dataclasses.fields(strict_params)]
        strict_params_dict = {field: getattr(strict_params, field) for field in params_fields}

        serialized_params = cls._serialize_params_dict(strict_params_dict, params_fields)
        return f"{{{{ semantic_layer.query({serialized_params}) }}}}"

    @classmethod
    def get_dimension_values_sql(cls, params: DimensionValuesQueryParameters) -> str:
        """Get the SQL that will be sent via Arrow Flight to the server based on dimension values query parameters."""
        serialized_params = cls._serialize_params_dict(params, list(DimensionValuesQueryParameters.__optional_keys__))
        return f"{{{{ semantic_layer.dimension_values({serialized_params}) }}}}"
