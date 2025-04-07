import inspect
import typing
import warnings
from dataclasses import dataclass, fields, is_dataclass
from dataclasses import field as dc_field
from enum import EnumMeta
from functools import cache
from types import MappingProxyType
from typing import Any, ClassVar, Dict, List, Set, Tuple, Type, Union
from typing import get_args as get_type_args
from typing import get_origin as get_type_origin

from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig

from dbtsl.api.graphql.util import normalize_query

if typing.TYPE_CHECKING:
    from dbtsl.api.graphql.client.base import BaseGraphQLClient


def snake_case_to_camel_case(s: str) -> str:
    """Convert a snake_case_string into a camelCaseString."""
    tokens = s.split("_")
    return tokens[0] + "".join(t.title() for t in tokens[1:])


class FlexibleEnumMeta(EnumMeta):
    """Makes an Enum class not break if you provide it an unknown value."""

    _subclass_registry: ClassVar[Set[str]] = set()

    UNKNOWN = "UNKNOWN"

    def __new__(
        metacls: Type["FlexibleEnumMeta"],
        name: str,
        bases: Tuple[Type[object]],
        namespace: Dict[str, Any],
        **_kwargs: object,
    ) -> "FlexibleEnumMeta":
        """Overwrite the _missing_ method of enum classes."""
        msg = f"Class {name} needs UNKNOWN attribute with 'UNKNOWN' string value"
        assert namespace.get("UNKNOWN", None) == "UNKNOWN", msg

        metacls._subclass_registry.add(name)

        newclass = super().__new__(metacls, name, bases, namespace)  # type: ignore
        setattr(newclass, "_missing_", classmethod(metacls._missing_))  # type: ignore
        return newclass

    def __getitem__(cls, name: str) -> Any:
        """Return the UNKNOWN attribute if can't find value in class."""
        try:
            return super().__getitem__(name)
        except KeyError:
            return cls.UNKNOWN

    def _missing_(cls, _name: str) -> str:
        return cls.UNKNOWN


class BaseModel(DataClassDictMixin):
    """Base class for all serializable models.

    Adds some functionality like automatically creating camelCase aliases.
    """

    DEPRECATED: ClassVar[str] = "dbtsl_deprecated"

    # Mapping of "subclass.field" to "deprecation reason"
    _deprecated_fields: ClassVar[Dict[str, str]] = dict()

    @staticmethod
    def _get_deprecation_key(class_name: str, field_name: str) -> str:
        return f"{class_name}.{field_name}"

    @classmethod
    def _warn_if_deprecated(cls, field_name: str) -> None:
        key = BaseModel._get_deprecation_key(cls.__name__, field_name)
        reason = BaseModel._deprecated_fields.get(key)
        if reason is not None:
            warnings.warn(reason, DeprecationWarning)

    class Config(BaseConfig):  # noqa: D106
        lazy_compilation = True

    @classmethod
    def _register_subclasses(cls) -> None:
        """Process fields of all subclasses.

        This will:
        - Apply camelCase aliases
        - Pre-populate the _deprecated_fields dict with the deprecated fields
        """
        for subclass in cls.__subclasses__():
            assert is_dataclass(subclass), "Subclass of BaseModel must be dataclass"

            for field in fields(subclass):
                camel_name = snake_case_to_camel_case(field.name)
                if field.name != camel_name:
                    opts = {**field_options(alias=camel_name), **field.metadata}
                    field.metadata = MappingProxyType(opts)

                if cls.DEPRECATED in field.metadata:
                    reason = field.metadata[cls.DEPRECATED]
                    key = BaseModel._get_deprecation_key(subclass.__name__, field.name)
                    cls._deprecated_fields[key] = reason

    def __getattribute__(self, name: str) -> Any:  # noqa: D105
        v = object.__getattribute__(self, name)
        if not name.startswith("__") and not callable(v):
            self._warn_if_deprecated(name)

        return v


class DeprecatedMixin:
    """Add this to any deprecated model."""

    @classmethod
    def _deprecation_message(cls) -> str:
        """The deprecation message that will get displayed."""
        return f"{cls.__name__} is deprecated"

    def __init__(self, *_args: object, **_kwargs: object) -> None:  # noqa: D107
        warnings.warn(self._deprecation_message(), DeprecationWarning)
        super(DeprecatedMixin, self).__init__()


@dataclass(frozen=True, eq=True)
class GraphQLFragment:
    """Represent a model as a GraphQL fragment."""

    name: str
    body: str = dc_field(hash=False)
    lazy: bool


@dataclass
class GraphQLFragmentMixin:
    """Add this to any model that needs to be fetched from GraphQL."""

    # mark fields that should not be lazy with this
    NOT_LAZY: ClassVar[str] = "dbtsl_notlazy"

    _subclass_registry: ClassVar[Set[Type["GraphQLFragmentMixin"]]] = set()

    _client: "BaseGraphQLClient[Any, Any]"

    def __init_subclass__(cls) -> None:
        """Add subclasses to the subclass registry.

        This registry is used by some tests.
        """
        GraphQLFragmentMixin._subclass_registry.add(cls)

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
    def _get_fragments_for_field(
        type: Union[Type[Any], str],
        field_name: str,
        *,
        field_lazy: bool,
        global_lazy: bool,
    ) -> Union[str, List[GraphQLFragment], None]:
        # field is a GraphQLFragmentMixin
        if inspect.isclass(type) and issubclass(type, GraphQLFragmentMixin):
            return type.gql_fragments(lazy=global_lazy)

        # field is an Optional, Union or List
        type_origin = get_type_origin(type)
        if type_origin is list or type_origin is Union:
            inner_type = get_type_args(type)[0]

            if (
                global_lazy
                and field_lazy
                and inspect.isclass(inner_type)
                and issubclass(inner_type, GraphQLFragmentMixin)
            ):
                return None

            return GraphQLFragmentMixin._get_fragments_for_field(
                inner_type,
                field_name,
                field_lazy=field_lazy,
                global_lazy=global_lazy,
            )

        return snake_case_to_camel_case(field_name)

    @classmethod
    @cache
    def gql_fragments(cls, *, lazy: bool) -> List[GraphQLFragment]:
        """Get the GraphQL fragments needed to query for this model.

        The first (0th) fragment is always the fragment that represents the model itself.
        The remaining fragments are dependencies of the model, if any.

        Dependencies only be returned if `lazy=False`. If `lazy=True`, the returned GraphQL
        query won't include child models.

        Arguments:
            lazy: whether to fetch nested models.
        """
        gql_model_name = cls.gql_model_name()
        fragment_name = f"fragment{cls.__name__}"

        assert is_dataclass(cls), "Subclass of GraphQLFragmentMixin must be dataclass"

        query_elements: List[str] = []
        dependencies: Set[GraphQLFragment] = set()
        for field in fields(cls):
            if field.name == "_client":
                continue

            field_lazy = lazy and GraphQLFragmentMixin.NOT_LAZY not in field.metadata
            frag_or_field = GraphQLFragmentMixin._get_fragments_for_field(
                field.type,
                field.name,
                field_lazy=field_lazy,
                global_lazy=lazy,
            )
            if isinstance(frag_or_field, str):
                query_elements.append(frag_or_field)
            elif frag_or_field is not None:
                frag = frag_or_field[0]
                field_query = snake_case_to_camel_case(field.name) + " { ..." + frag.name + " }"
                query_elements.append(field_query)
                dependencies.update(frag_or_field)
            else:
                assert lazy

        query_str = "         \n".join(query_elements)

        fragment_body = normalize_query(f"""
        fragment {fragment_name} on {gql_model_name} {{
            {query_str}
        }}
        """)
        fragment = GraphQLFragment(
            name=fragment_name,
            body=fragment_body,
            lazy=lazy,
        )
        return [fragment] + list(dependencies)


NOT_LAZY_META = {GraphQLFragmentMixin.NOT_LAZY: True}
