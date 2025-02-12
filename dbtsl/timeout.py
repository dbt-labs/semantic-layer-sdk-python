from dataclasses import dataclass


@dataclass(frozen=True)
class TimeoutOptions:
    """Timeout options for the GraphQL API.

    All values are in seconds.

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
