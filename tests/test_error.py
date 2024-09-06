from dbtsl.error import SemanticLayerError, TimeoutError


def test_error_str() -> None:
    assert str(SemanticLayerError()) == "SemanticLayerError"


def test_error_repr() -> None:
    assert repr(SemanticLayerError()) == "SemanticLayerError"


def test_timeout_error_str() -> None:
    assert str(TimeoutError(timeout_ms=1000)) == "TimeoutError(timeout_ms=1000)"
