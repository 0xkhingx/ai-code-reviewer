import logging
import time

from apps.worker.jobs import review_pr
from core import queue
from db.session import connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")

HANDLERS = {"review_pr": review_pr.run}
POLL_SECONDS = 1.0


def main() -> None:
    log.info("worker started")
    while True:
        with connection() as conn:
            job = queue.claim(conn)  # committed on exit, so the claim is visible immediately
        if job is None:
            time.sleep(POLL_SECONDS)
            continue

        log.info("job %s (%s) attempt %s", job["id"], job["kind"], job["attempts"])
        try:
            HANDLERS[job["kind"]](job["payload"])
        except Exception as exc:  # noqa: BLE001 - any failure should trigger retry logic
            log.exception("job %s failed", job["id"])
            with connection() as conn:
                queue.fail(conn, job, repr(exc))
        else:
            with connection() as conn:
                queue.complete(conn, job["id"])


if __name__ == "__main__":
    main()
