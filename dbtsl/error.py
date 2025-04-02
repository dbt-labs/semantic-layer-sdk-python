import json


class SemanticLayerError(RuntimeError):
    """Any errors related to the Semantic Layer inherit from this."""

    def __str__(self) -> str:
        """RuntimeError doesn't stringify itself by default, so we need to manually add this."""
        args_str = "" if len(self.args) == 0 else ", ".join(json.dumps(a) for a in self.args)
        return f"{self.__class__.__name__}({args_str})"

    def __repr__(self) -> str:
        """RuntimeError doesn't stringify itself by default, so we need to manually add this."""
        return str(self)


class TimeoutError(SemanticLayerError):
    """Raise whenever a request times out."""

    def __init__(self, *, timeout_s: float, **_kwargs: object) -> None:
        """Initialize the timeout error.

        Args:
            timeout_s: The maximum time limit that got exceeded, in seconds
            *args: any other exception args
            **kwargs: any other exception kwargs
        """
        self.timeout_s = timeout_s

    def __str__(self) -> str:  # noqa: D105
        return f"{self.__class__.__name__}(timeout_s={self.timeout_s})"


class ConnectTimeoutError(TimeoutError):
    """Raise whenever a timeout occurred while connecting to the servers."""


class ExecuteTimeoutError(TimeoutError):
    """Raise whenever a timeout occurred while executing an operation against the servers."""


class RetryTimeoutError(TimeoutError):
    """Raise whenever a timeout occurred while retrying an operation against the servers."""


class QueryFailedError(SemanticLayerError):
    """Raise whenever a query has failed."""


class AuthError(SemanticLayerError):
    """Raise whenever there was a problem authenticating to the API."""
