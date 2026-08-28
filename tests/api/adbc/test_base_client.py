import socket
import threading
import time

from dbtsl.api.adbc.client.base import BaseADBCClient


class _StalledServer:
    """A TCP server that accepts connections but never speaks any protocol on them.

    This simulates the exact failure mode DI-5183 is about: a TCP connection that is
    established (or at least appears to be, from the OS's perspective) but on which the
    gRPC/HTTP2 handshake never progresses, so the client is left waiting forever with no
    error and no data.
    """

    def __init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    @property
    def address(self) -> str:
        host, port = self._sock.getsockname()
        return f"{host}:{port}"

    def _accept_loop(self) -> None:
        self._sock.settimeout(0.1)
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            # Accept the TCP connection, but deliberately never read from or write to
            # it. This is what leaves a client-side dial "stuck": the socket is open,
            # but nothing will ever come back on it.
            self._stop.wait()
            conn.close()

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)
        self._sock.close()


def _connect_in_background(client: BaseADBCClient) -> "threading.Thread":
    def _target() -> None:
        try:
            ctx = client._get_connection_context_manager()
            with ctx:
                pass
        except Exception:
            pass

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    return thread


def test_connect_timeout_bounds_hung_dial() -> None:
    """A stalled dial must fail within roughly `_CONNECT_TIMEOUT_SECONDS`, not hang forever.

    Without `adbc.flight.sql.rpc.timeout_seconds.connect` set in `db_kwargs`, connecting
    to a server that accepts the TCP connection but never completes the gRPC handshake
    blocks indefinitely. This test proves the configured connect timeout actually bounds
    that wait, using a fast (~1s) timeout so the test itself stays quick while exercising
    the exact same code path (`BaseADBCClient._get_connection_context_manager`) that
    production uses with a 15s timeout.
    """
    original_timeout = BaseADBCClient._CONNECT_TIMEOUT_SECONDS
    BaseADBCClient._CONNECT_TIMEOUT_SECONDS = 1

    server = _StalledServer()
    try:
        client = BaseADBCClient(
            server_host=server.address,
            environment_id=1,
            auth_token="fake-token",
            url_format="grpc://{server_host}",
        )

        start = time.monotonic()
        thread = _connect_in_background(client)

        # Give it generous headroom over the 1s connect timeout: long enough that a
        # correctly-bounded attempt always finishes, short enough that a genuine hang
        # (the pre-fix behavior) fails the test instead of blocking the suite forever.
        thread.join(timeout=10)
        elapsed = time.monotonic() - start

        assert not thread.is_alive(), (
            f"connect attempt was still hung after {elapsed:.1f}s; the connect timeout did not bound the stalled dial"
        )
        assert elapsed < 10, f"connect attempt took {elapsed:.1f}s, expected it to fail near the 1s connect timeout"
    finally:
        server.close()
        BaseADBCClient._CONNECT_TIMEOUT_SECONDS = original_timeout


def test_extra_db_kwargs_sets_only_connect_timeout() -> None:
    """`.query`/`.fetch`/`.update` must remain untouched -- only `.connect` is set.

    DI-5183 scoped this fix narrowly: query execution can legitimately take 10+ minutes,
    so only the connect/handshake step (which should be fast) gets a bound. This test
    guards against that scope silently expanding.
    """
    kwargs = BaseADBCClient._extra_db_kwargs()

    assert kwargs["adbc.flight.sql.rpc.timeout_seconds.connect"] == str(BaseADBCClient._CONNECT_TIMEOUT_SECONDS)

    unbounded_keys = [
        "adbc.flight.sql.rpc.timeout_seconds.query",
        "adbc.flight.sql.rpc.timeout_seconds.fetch",
        "adbc.flight.sql.rpc.timeout_seconds.update",
    ]
    for key in unbounded_keys:
        assert key not in kwargs, f"{key} must remain unset -- queries can legitimately run for 10+ minutes"
