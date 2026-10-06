import sys
import types

# Offline stub: db.session needs psycopg_pool which isn't installed locally.
# Stub it so webhook payload validation can be tested without a DB driver.
if "psycopg_pool" not in sys.modules:
    try:
        import psycopg_pool  # noqa: F401
    except ImportError:
        stub_pool = types.ModuleType("psycopg_pool")

        class ConnectionPool:  # minimal stand-in for import time only
            def __init__(self, *a, **k):
                raise RuntimeError("DB not available in offline tests")

        stub_pool.ConnectionPool = ConnectionPool
        sys.modules["psycopg_pool"] = stub_pool

from apps.api.routes.webhooks import extract_review_target
from core import queue


class FakeConn:
    def __init__(self, fetchall_result=None):
        self.calls = []
        self._fetchall = fetchall_result or []

    def execute(self, sql, params=None):
        self.calls.append({"sql": sql, "params": params})
        return self

    def fetchall(self):
        return self._fetchall


def test_extract_valid():
    payload = {
        "installation": {"id": 11},
        "repository": {"full_name": "o/r"},
        "pull_request": {"number": 7, "head": {"sha": "abc"}},
    }
    assert extract_review_target(payload) == {
        "installation_id": 11,
        "repo_full_name": "o/r",
        "pr_number": 7,
        "head_sha": "abc",
    }


def test_extract_invalid_returns_none():
    assert extract_review_target({}) is None
    assert extract_review_target({"pull_request": None}) is None
    assert extract_review_target({"pull_request": {"number": 1}}) is None


def test_fail_adds_jitter_within_bounds():
    conn = FakeConn()
    queue.fail(conn, {"id": 1, "attempts": 1, "max_attempts": 5}, "boom")
    delay = conn.calls[0]["params"][1]
    assert 10 <= delay <= 12  # base 10 + up to 20% jitter capped at 5


def test_fail_marks_failed_at_max():
    conn = FakeConn()
    queue.fail(conn, {"id": 2, "attempts": 5, "max_attempts": 5}, "boom")
    assert "failed" in conn.calls[0]["sql"]


def test_reaper_sql_uses_timeout():
    conn = FakeConn(fetchall_result=[{"id": 1}, {"id": 2}])
    assert queue.reap_stale_running(conn, 300) == 2
    assert conn.calls[0]["params"] == (300,)


def test_cancel_superseded_targets_same_pr():
    conn = FakeConn(fetchall_result=[{"id": 9}])
    assert queue.cancel_superseded(conn, "o/r", 7, 10) == 1
    sql, params = conn.calls[0]["sql"], conn.calls[0]["params"]
    assert "cancelled" in sql
    assert params == ("o/r", 7, 10)
