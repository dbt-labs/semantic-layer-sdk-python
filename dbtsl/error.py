class SemanticLayerError(RuntimeError):
    """Any errors related to the Semantic Layer inherit from this."""

    def __str__(self) -> str:
        """RuntimeError doesn't stringify itself by default, so we need to manually add this."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """RuntimeError doesn't stringify itself by default, so we need to manually add this."""
        return str(self)


class TimeoutError(SemanticLayerError):
    """Raise whenever a request times out."""

    def __init__(self, *args, timeout_ms: int, **kwargs) -> None:
        """Initialize the timeout error.

        Args:
            timeout_ms: The maximum time limit that got exceeded, in milliseconds
            *args: any other exception args
            **kwargs: any other exception kwargs
        """
        self.timeout_ms = timeout_ms

    def __str__(self) -> str:  # noqa: D105
        return f"{self.__class__.__name__}(timeout_ms={self.timeout_ms})"


class QueryFailedError(SemanticLayerError):
    """Raise whenever a query has failed."""


class AuthError(SemanticLayerError):
    """Raise whenever there was a problem authenticating to the API."""
