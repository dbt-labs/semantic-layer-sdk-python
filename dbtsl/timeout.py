from dataclasses import dataclass


@dataclass(frozen=True)
class TimeoutOptions:
    """Timeout options for the GraphQL API.

    All values are in seconds.

    All timeouts are upper-bounded by `total_timeout`. For example, if you provide `total_timeout=1` and
    `connect_timeout=3`, the actual value of `connect_timeout` will be 1, since the connect timeout cannot
    be bigger than the total timeout.

    Properties:
        total_timeout: total timeout for executing operations against the Semantic Layer, including
            connecting, executing (and retrying) operations, and closing the connection.
        connect_timeout: timeout for establishing a connection with the Semantic Layer services
        execute_timeout: timeout for executing operations against the Semantic Layer services
        tls_close_timeout: timeout for closing the TLS connection with the Semantic Layer services
    """

    total_timeout: float
    connect_timeout: float
    execute_timeout: float
    tls_close_timeout: float

    def __post_init__(self) -> None:  # noqa: D105
        object.__setattr__(self, "execute_timeout", min(self.execute_timeout, self.total_timeout))
        object.__setattr__(self, "connect_timeout", min(self.connect_timeout, self.total_timeout))
        object.__setattr__(self, "tls_close_timeout", min(self.tls_close_timeout, self.total_timeout))
