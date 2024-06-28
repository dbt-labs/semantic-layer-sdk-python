from dataclasses import fields, is_dataclass
from types import MappingProxyType

from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig


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
