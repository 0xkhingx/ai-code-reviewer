# DECISIONS.md — Architecture Decision Records

Keep entries to two minutes each. Never delete; supersede with new ADRs.

## ADR-001: Python + FastAPI + worker split
- **Date:** 2026-10-05
- **Status:** Accepted
- **Reversibility:** One-way door (rewrites all handlers)
- **Context:** Solo, free-only prototype needing GitHub webhooks + long review jobs. Existing code already uses FastAPI/uvicorn + `python -m apps.worker.main`.
- **Decision:** Keep Python 3.11+ with FastAPI for webhooks and a separate polling worker process.
- **Mechanism:** `apps/api` verifies HMAC then enqueues in Postgres; `apps/worker` polls `jobs` every 1s and dispatches `HANDLERS`. Shared `core/`, `db/` packages via `pyproject.toml`.
- **Alternatives considered:** Single-process inline handling — zero ops but webhook timeouts on long reviews; Node/Express — viable but rewrites existing Python.
- **Consequences:** + Simple local Docker; - polling latency ~1s + constant light DB load.
- **Revisit when:** Sustained queue depth grows or p95 enqueue-to-comment >30s.
- **Links:** `apps/api/main.py`, `apps/worker/main.py`, `docker-compose.yml`

## ADR-002: Postgres as queue instead of Redis/managed queue
- **Date:** 2026-10-05
- **Status:** Accepted
- **Reversibility:** Two-way door (migrate claim logic, moderate)
- **Context:** Solo, free-only, Postgres already required for event log. Volume is dozens of PRs/day.
- **Decision:** Store `webhook_events` + `jobs` in Postgres; claim with `UPDATE ... WHERE id=(SELECT ... FOR UPDATE SKIP LOCKED)`.
- **Mechanism:** Enqueue + event insert in one transaction; `SKIP LOCKED` lets concurrent workers skip each other; `fail()` uses exp backoff `min(300, 5*2^attempts)`, `complete()` marks done. Partial index `jobs_claim_idx WHERE status='queued'`.
- **Alternatives considered:** Redis+RQ/Celery — higher throughput but second service + drift; SQS/Cloud Tasks — no ops but IAM + dual-write + cost; inline — timeouts/lost work.
- **Consequences:** + One source of truth, transactional enqueue; - table bloat/vacuum pressure at high churn, no built-in DLQ UI, no jitter yet.
- **Revisit when:** Jobs/min in low thousands sustained, or need pub-sub/delayed scheduling.
- **Links:** `db/schema.sql`, `core/queue.py`

## ADR-003: GitHub App JWT → installation token per job
- **Date:** 2026-10-05
- **Status:** Accepted
- **Reversibility:** Two-way door
- **Context:** Need least-privilege repo access for comments + diff fetch, free tier.
- **Decision:** Mint `app_jwt` (`iat-60s`, `exp+9m`, RS256) from `.pem`, `POST /app/installations/{id}/access_tokens` per job via httpx.
- **Mechanism:** `core/github/auth.py`; key from `GITHUB_PRIVATE_KEY` or file `GITHUB_PRIVATE_KEY_PATH` (mounted `/run/secrets/github-app.pem`).
- **Alternatives considered:** PAT/OAuth token — simpler but personal, broad, no expiry scoping; caching tokens — saves calls but adds refresh logic.
- **Consequences:** + Scoped, expiring; - new JWT+token per job (wasteful at scale).
- **Revisit when:** Rate limits hit or jobs/min grows; then cache by installation_id until `expires_at`.
- **Links:** `core/github/auth.py`, `core/github/client.py`

## ADR-004: Fetch PR diff via Files API for v1 summary
- **Date:** 2026-10-05
- **Status:** Accepted
- **Reversibility:** Two-way door
- **Context:** v1 = deterministic summary (files + counts), solo, free-only, no LLM. Need structured counts without parsing raw patches.
- **Decision:** Use `GET /repos/{repo}/pulls/{pr}/files?per_page=100&page=N` with token, cap 10 pages / 20 files / 60k chars in summary.
- **Mechanism:** New `core/github/diff.py::fetch_pr_files` + `summarize_files`; `review_pr.run` posts result via existing issues-comments endpoint.
- **Alternatives considered:** Raw diff accept header — one request but manual parse, better for M6 inline; do nothing — fails v1 goal.
- **Consequences:** + No new deps, testable; - truncated on huge PRs, extra pages on large PRs.
- **Revisit when:** Need hunk positions for inline comments (M6) or summaries judged useless → add raw diff + LLM.
- **Links:** `core/github/diff.py`, `apps/worker/jobs/review_pr.py`
