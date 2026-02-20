from dbtsl.error import RetryTimeoutError, SemanticLayerError, TimeoutError


def test_error_str_calls_repr() -> None:
    assert str(SemanticLayerError()) == repr(SemanticLayerError())


def test_error_repr_no_args() -> None:
    assert repr(SemanticLayerError()) == "SemanticLayerError()"


def test_error_repr_with_args() -> None:
    assert repr(SemanticLayerError(1, 2, "a")) == 'SemanticLayerError(1, 2, "a")'


def test_timeout_error_str() -> None:
    assert str(TimeoutError(timeout_s=1000)) == "TimeoutError(timeout_s=1000)"


def test_retry_timeout_error_without_status() -> None:
    err = RetryTimeoutError(timeout_s=60)
    assert err.timeout_s == 60
    assert err.status is None
    assert str(err) == "RetryTimeoutError(timeout_s=60)"


def test_retry_timeout_error_with_status() -> None:
    err = RetryTimeoutError(timeout_s=30, status="COMPILED")
    assert err.timeout_s == 30
    assert err.status == "COMPILED"
    assert str(err) == "RetryTimeoutError(timeout_s=30, status=COMPILED)"
