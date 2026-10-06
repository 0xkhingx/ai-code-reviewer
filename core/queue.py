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
    """Retry with exponential backoff until max_attempts, then mark failed."""
    if job["attempts"] >= job["max_attempts"]:
        conn.execute(
            "UPDATE jobs SET status = 'failed', locked_at = NULL, last_error = %s, updated_at = now() WHERE id = %s",
            (error, job["id"]),
        )
        return
    delay = min(300, 5 * 2 ** job["attempts"])
    conn.execute(
        """UPDATE jobs SET status = 'queued', locked_at = NULL, last_error = %s,
           run_at = now() + make_interval(secs => %s), updated_at = now() WHERE id = %s""",
        (error, delay, job["id"]),
    )
