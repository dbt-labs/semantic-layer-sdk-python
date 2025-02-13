from dbtsl.error import SemanticLayerError, TimeoutError


def test_error_str_calls_repr() -> None:
    assert str(SemanticLayerError()) == repr(SemanticLayerError())


def test_error_repr_no_args() -> None:
    assert repr(SemanticLayerError()) == "SemanticLayerError()"


def test_error_repr_with_args() -> None:
    assert repr(SemanticLayerError(1, 2, "a")) == 'SemanticLayerError(1, 2, "a")'


def test_timeout_error_str() -> None:
    assert str(TimeoutError(timeout_s=1000)) == "TimeoutError(timeout_s=1000)"
