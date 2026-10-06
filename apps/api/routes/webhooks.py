import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from psycopg.types.json import Jsonb

from core.config import load_settings
from core.queue import enqueue
from core.security import verify_signature
from db.session import connection

router = APIRouter()

REVIEW_ACTIONS = {"opened", "synchronize", "reopened"}


def _store_and_enqueue(delivery_id: str, event: str, payload: dict) -> str:
    with connection() as conn:
        inserted = conn.execute(
            """INSERT INTO webhook_events (delivery_id, event_type, payload)
               VALUES (%s, %s, %s) ON CONFLICT (delivery_id) DO NOTHING RETURNING id""",
            (delivery_id, event, Jsonb(payload)),
        ).fetchone()
        if inserted is None:
            return "duplicate"
        if event == "pull_request" and payload.get("action") in REVIEW_ACTIONS:
            pr = payload["pull_request"]
            enqueue(
                conn,
                "review_pr",
                {
                    "installation_id": payload["installation"]["id"],
                    "repo_full_name": payload["repository"]["full_name"],
                    "pr_number": pr["number"],
                    "head_sha": pr["head"]["sha"],
                },
            )
            return "enqueued"
        return "stored"


@router.post("/webhooks/github")
async def github_webhook(request: Request):
    body = await request.body()
    settings = load_settings()
    if not verify_signature(
        settings.github_webhook_secret, body, request.headers.get("X-Hub-Signature-256")
    ):
        raise HTTPException(status_code=401, detail="invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if not delivery_id:
        raise HTTPException(status_code=400, detail="missing delivery id")
    if event == "ping":
        return {"status": "pong"}

    payload = json.loads(body)
    result = await run_in_threadpool(_store_and_enqueue, delivery_id, event, payload)
    return {"status": result}
