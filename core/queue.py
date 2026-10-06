import random

from psycopg.types.json import Jsonb

CLAIM_SQL = """
UPDATE jobs
SET status = 'running', locked_at = now(), attempts = attempts + 1, updated_at = now()
WHERE id = (
    SELECT id FROM jobs
    WHERE status = 'queued' AND run_at <= now()
    ORDER BY run_at, id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING id, kind, payload, attempts, max_attempts
"""


def enqueue(conn, kind: str, payload: dict) -> int:
    row = conn.execute(
        "INSERT INTO jobs (kind, payload) VALUES (%s, %s) RETURNING id",
        (kind, Jsonb(payload)),
    ).fetchone()
    return row["id"]


def claim(conn) -> dict | None:
    return conn.execute(CLAIM_SQL).fetchone()


def complete(conn, job_id: int) -> None:
    conn.execute(
        "UPDATE jobs SET status = 'done', locked_at = NULL, updated_at = now() WHERE id = %s",
        (job_id,),
    )


def fail(conn, job: dict, error: str) -> None:
    """Retry with exponential backoff + jitter until max_attempts, then mark failed."""
    if job["attempts"] >= job["max_attempts"]:
        conn.execute(
            "UPDATE jobs SET status = 'failed', locked_at = NULL, last_error = %s, updated_at = now() WHERE id = %s",
            (error, job["id"]),
        )
        return
    base = min(300, 5 * 2 ** job["attempts"])
    # Note: jitter spreads retries so many workers don't wake at the same instant.
    delay = base + random.uniform(0, min(5, base * 0.2))
    conn.execute(
        """UPDATE jobs SET status = 'queued', locked_at = NULL, last_error = %s,
           run_at = now() + make_interval(secs => %s), updated_at = now() WHERE id = %s""",
        (error, delay, job["id"]),
    )


def reap_stale_running(conn, timeout_seconds: int = 300) -> int:
    """Reset `running` jobs stuck past timeout back to `queued`. Returns count."""
    row = conn.execute(
        """UPDATE jobs SET status = 'queued', locked_at = NULL,
           run_at = now(), updated_at = now()
           WHERE status = 'running' AND locked_at < now() - make_interval(secs => %s)
           RETURNING id""",
        (timeout_seconds,),
    ).fetchall()
    return len(row)


def cancel_superseded(conn, repo_full_name: str, pr_number: int, keep_id: int) -> int:
    """Mark older queued jobs for the same PR as cancelled. Returns count."""
    rows = conn.execute(
        """UPDATE jobs SET status = 'cancelled', updated_at = now()
           WHERE status = 'queued' AND kind = 'review_pr'
           AND payload->>'repo_full_name' = %s
           AND (payload->>'pr_number')::int = %s
           AND id != %s RETURNING id""",
        (repo_full_name, pr_number, keep_id),
    ).fetchall()
    return len(rows)
