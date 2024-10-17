from enum import Enum

from typing_extensions import override

from dbtsl.models.base import DeprecatedMixin


class TimeGranularity(str, DeprecatedMixin, Enum):
    """A time granularity."""

    @override
    @classmethod
    def _deprecation_message(cls) -> str:
        return (
            "Since the introduction of custom time granularity, the `TimeGranularity` enum is deprecated. "
            "Please just use strings to represent time grains."
        )

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


class DatePart(str, Enum):
    """Date part."""

    DOY = "DOY"
    DOW = "DOW"
    DAY = "DAY"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"
