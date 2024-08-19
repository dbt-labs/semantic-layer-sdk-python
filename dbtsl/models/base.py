import inspect
from dataclasses import dataclass, fields, is_dataclass
from dataclasses import field as dc_field
from functools import cache
from types import MappingProxyType
from typing import Any, List, Set, Type, Union
from typing import get_args as get_type_args
from typing import get_origin as get_type_origin

from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig

from dbtsl.api.graphql.util import normalize_query


def snake_case_to_camel_case(s: str) -> str:
    """Convert a snake_case_string into a camelCaseString."""
    tokens = s.split("_")
    return tokens[0] + "".join(t.title() for t in tokens[1:])


class BaseModel(DataClassDictMixin):
    """Base class for all serializable models.

    Adds some functionality like automatically creating camelCase aliases.
    """

    class Config(BaseConfig):  # noqa: D106
        lazy_compilation = True

    @classmethod
    def _apply_aliases(cls) -> None:
        """Apply camelCase aliases to all subclasses."""
        for subclass in cls.__subclasses__():
            assert is_dataclass(subclass), "Subclass of BaseModel must be dataclass"

            for field in fields(subclass):
                camel_name = snake_case_to_camel_case(field.name)
                if field.name != camel_name:
                    field.metadata = MappingProxyType(field_options(alias=camel_name))


@dataclass(frozen=True, eq=True)
class GraphQLFragment:
    """Represent a model as a GraphQL fragment."""

    name: str
    body: str = dc_field(hash=False)


class GraphQLFragmentMixin:
    """Add this to any model that needs to be fetched from GraphQL."""

    @classmethod
    def gql_model_name(cls) -> str:
        """The model's name in the GraphQL schema. Defaults to same as class name."""
        return cls.__name__

    # NOTE: this will overflow the stack if we add any circular dependencies in our GraphQL schema, like
    # Metric -> Dimension -> Metric -> Dimension ...
    #
    # If we do that, we need to modify this method to memoize what fragments were already created
    # so that we exit the recursion gracefully
    @staticmethod
    def _get_fragments_for_field(type: Union[Type[Any], str], field_name: str) -> Union[str, List[GraphQLFragment]]:
        if inspect.isclass(type) and issubclass(type, GraphQLFragmentMixin):
            return type.gql_fragments()

        type_origin = get_type_origin(type)
        # Optional = Union[X, None]
        if type_origin is list or type_origin is Union:
            inner_type = get_type_args(type)[0]
            return GraphQLFragmentMixin._get_fragments_for_field(inner_type, field_name)

        return snake_case_to_camel_case(field_name)

    @classmethod
    @cache
    def gql_fragments(cls) -> List[GraphQLFragment]:
        """Get the GraphQL fragments needed to query for this model.

        The first (0th) fragment is always the fragment that represents the model itself.
        The remaining fragments are dependencies of the model, if any.
        """
        gql_model_name = cls.gql_model_name()
        fragment_name = f"fragment{cls.__name__}"

        assert is_dataclass(cls), "Subclass of GraphQLFragmentMixin must be dataclass"

        query_elements: List[str] = []
        dependencies: Set[GraphQLFragment] = set()
        for field in fields(cls):
            frag_or_field = GraphQLFragmentMixin._get_fragments_for_field(field.type, field.name)
            if isinstance(frag_or_field, str):
                query_elements.append(frag_or_field)
            else:
                frag = frag_or_field[0]
                field_query = snake_case_to_camel_case(field.name) + " { ..." + frag.name + " }"
                query_elements.append(field_query)
                dependencies.update(frag_or_field)

        query_str = "         \n".join(query_elements)

        fragment_body = normalize_query(f"""
        fragment {fragment_name} on {gql_model_name} {{
            {query_str}
        }}
        """)
        fragment = GraphQLFragment(name=fragment_name, body=fragment_body)
        return [fragment] + list(dependencies)
