import itertools
import time
from dataclasses import dataclass
from typing import Iterator

from dbtsl.error import TimeoutError


@dataclass
class ExponentialBackoff:
    """Manage exponential backoff logic.

    Attributes:
        base_interval_ms: The interval to start with
        max_interval_ms: The maximum interval length
        timeout_ms: After how long should it raise a TimeoutError
        exp_factor: The exponential factor to increase wait times
    """

    base_interval_ms: int
    max_interval_ms: int
    timeout_ms: int
    exp_factor: float = 1.15

    def iter_ms(self) -> Iterator[int]:
        """Iterate over sleep times in ms until TimeoutError."""
        start_ms = int(time.time() * 1000)
        for i in itertools.count(start=0):
            curr_ms = int(time.time() * 1000)
            elapsed_ms = curr_ms - start_ms
            if elapsed_ms > self.timeout_ms:
                raise TimeoutError()

            yield min(int(self.base_interval_ms * self.exp_factor**i), self.max_interval_ms)
