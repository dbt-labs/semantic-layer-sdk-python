from dataclasses import dataclass
from enum import Enum

from dbtsl.models.base import BaseModel


class MetricType(str, Enum):
    """The type of a Metric."""

    SIMPLE = "SIMPLE"
    RATIO = "RATIO"
    CUMULATIVE = "CUMULATIVE"
    DERIVED = "DERIVED"
    CONVERSION = "CONVERSION"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def missing(cls, _: str) -> "MetricType":
        """Return UNKNOWN by default.

        Prevents client from breaking in case a new unknown type is introduced
        by the server.
        """
        return cls.UNKNOWN


@dataclass(frozen=True)
class Metric(BaseModel):
    """A metric."""

    name: str
    description: str
    type: MetricType
