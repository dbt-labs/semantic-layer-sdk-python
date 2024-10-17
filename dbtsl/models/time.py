from enum import Enum
from typing import Union


class TimeGranularity(str, Enum):
    """A time granularity."""

    NANOSECOND = "NANOSECOND"
    MICROSECOND = "MICROSECOND"
    MILLISECOND = "MILLISECOND"
    SECOND = "SECOND"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


Grain = Union[TimeGranularity, str]
"""Either a standard TimeGranularity or a custom grain."""


class DatePart(str, Enum):
    """Date part."""

    DOY = "DOY"
    DOW = "DOW"
    DAY = "DAY"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"
