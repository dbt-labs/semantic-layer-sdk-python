class SemanticLayerError(RuntimeError):
    """Any errors related to the Semantic Layer inherit from this."""


class TimeoutError(SemanticLayerError):
    """Raise whenever a request times out."""


class QueryFailedError(SemanticLayerError):
    """Raise whenever a query has failed."""


class AuthError(SemanticLayerError):
    """Raise whenever there was a problem authenticating to the API."""
