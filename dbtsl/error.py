import json
from typing import Any, Optional


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

    def __init__(self, message: Any, status: Any, query_id: Optional[str] = None) -> None:
        """Initialize the query failed error.

        Args:
            message: The message or error details
            status: The stringified status or the response
            query_id: The query ID for GQL requests
        """
        # extract first error message if we get a list with just 1 message
        if isinstance(message, list) and len(message) == 1:  # pyright: ignore
            message = message[0]  # pyright: ignore
        self.message = str(message)  # pyright: ignore
        self.status = str(status)
        self.query_id = query_id

    def __str__(self) -> str:  # noqa: D105
        content = f'message="{self.message}"), status={self.status}'
        if self.query_id:
            content += f", query_id={self.query_id}"
        return f"{self.__class__.__name__}({content})"


class AuthError(SemanticLayerError):
    """Raise whenever there was a problem authenticating to the API."""
