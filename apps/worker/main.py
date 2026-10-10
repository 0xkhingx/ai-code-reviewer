import logging
import time

from apps.worker.jobs import review_pr
from core import queue
from db.session import connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")

HANDLERS = {"review_pr": review_pr.run}
POLL_SECONDS = 1.0
REAP_EVERY_SECONDS = 60.0
REAP_TIMEOUT_SECONDS = 300


def main() -> None:
    log.info("worker started")
    last_reap = 0.0
    while True:
        # Note: reaper resets jobs stuck in `running` (e.g. crash after claim).
        if time.time() - last_reap >= REAP_EVERY_SECONDS:
            try:
                with connection() as conn:
                    rescued = queue.reap_stale_running(conn, REAP_TIMEOUT_SECONDS)
                if rescued:
                    log.info("reaped %d stale running job(s)", rescued)
            except Exception:  # noqa: BLE001 - reaper must never kill the loop
                log.exception("reaper failed")
            last_reap = time.time()
        with connection() as conn:
            job = queue.claim(conn)  # committed on exit, so the claim is visible immediately
        if job is None:
            time.sleep(POLL_SECONDS)
            continue

        log.info("job %s (%s) attempt %s", job["id"], job["kind"], job["attempts"])
        handler = HANDLERS.get(job["kind"])
        if handler is None:
            with connection() as conn:
                queue.fail(conn, job, f"unknown job kind: {job['kind']}")
            continue
        try:
            handler(job["payload"])
        except Exception as exc:  # noqa: BLE001 - any failure should trigger retry logic
            log.exception("job %s failed", job["id"])
            with connection() as conn:
                queue.fail(conn, job, repr(exc))
        else:
            with connection() as conn:
                queue.complete(conn, job["id"])


if __name__ == "__main__":
    main()
