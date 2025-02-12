import itertools
import warnings
from dataclasses import dataclass
from typing import Iterator, Optional

TIMEOUT_MS_DEPRECATION = """
Since the introduction of `TimeoutOptions`, the `timeout_ms` parameter on `ExponentialBackoff` has been deprecated.
While it will still work, it might be removed in the future. Please migrate to setting the `total_timeout` on the
global `TimeoutOptions` object.
""".strip().replace("\n", " ")


@dataclass(frozen=True)
class ExponentialBackoff:
    """Manage exponential backoff logic.

    Attributes:
        base_interval_ms: The interval to start with
        max_interval_ms: The maximum interval length
        exp_factor: The exponential factor to increase wait times
        [deprecated] timeout_ms: After how long should it raise a TimeoutError
    """

    base_interval_ms: int
    max_interval_ms: int
    exp_factor: float = 1.15

    timeout_ms: Optional[int] = None

    def __post_init__(self) -> None:  # noqa: D105
        if self.timeout_ms is not None:
            warnings.warn(TIMEOUT_MS_DEPRECATION, DeprecationWarning)

    def iter_ms(self) -> Iterator[int]:
        """Iterate over sleep times in ms according to the backoff configuration."""
        for i in itertools.count(start=0):
            yield min(int(self.base_interval_ms * self.exp_factor**i), self.max_interval_ms)
