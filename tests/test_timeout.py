from dbtsl.timeout import TimeoutOptions


def test_timeout_options_is_upper_bounded_by_total_timeout() -> None:
    t = TimeoutOptions(
        connect_timeout=10,
        execute_timeout=10,
        tls_close_timeout=10,
        total_timeout=1,
    )
    expected = TimeoutOptions(
        connect_timeout=1,
        execute_timeout=1,
        tls_close_timeout=1,
        total_timeout=1,
    )
    assert t == expected
