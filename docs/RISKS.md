# RISKS.md — Known weak spots, accepted risks, tech debt

> Per AGENTS.md companion file. Owner = solo unless noted. Trigger = when to fix.

## Blockers for production (do not deploy as-is)

- **Dev-only runtime (api --reload + source mounts).** `docker-compose.yml:22` uses `--reload` and `.:/app` mounts. Restarts on file writes, extra overhead. Owner: solo. Fix at M11: prod image without reload/mounts, `restart: unless-stopped`, healthchecks.
- **Secrets on disk.** `.pem` mounted from `./github-app.pem`, config via `.env` file. No manager, no rotation. Owner: solo. Fix at M11: env/secret manager, never commit (already gitignored).
- **No migrations.** `db/schema.sql` runs only on first volume init (`docker-compose.yml:12`). Schema edits ignored on existing DB. Owner: solo. Fix at M11: add migration runner (e.g. Alembic); backup before first prod deploy.
- **Stuck `running` jobs.** `apps/worker/main.py` + `core/queue.py`: no reaper for `locked_at` timeout, no jitter, no cancel on new `synchronize`. Crash-after-claim can stick. Owner: solo. Fix at M7: reaper + jitter + supersede-cancel.
- **Duplicate comments on retry.** `review_pr.py` posts a new issue comment each attempt; no update-instead-of-duplicate. Owner: solo. Fix at M7: track posted comment ID or edit existing.
- **Unvalidated webhook payload.** `apps/api/routes/webhooks.py:27-36` indexes `payload["installation"]` directly — malformed event raises `KeyError` → 500. Owner: solo. Fix at M7: validate keys, return 400 on bad shape.
- **GitHub rate limits.** Fresh JWT + installation token per job (`core/github/auth.py`), no caching, no 403-vs-401 split. OK for dozens/day, fails at scale. Owner: solo. Fix when rate-limited or jobs/min grows: cache token until `expires_at`, backoff on 403.

## Update 2026-10-06 (offline, no-data session)

- Implemented in code, live verification still pending: payload validation, jitter, reaper, supersede-cancel (`core/queue.py`, `webhooks.py`, `tests/test_queue_hardening.py`, 16 passed mocked).
- Still open: duplicate-comment edit (needs comment-ID storage + schema change), prod image, migrations, secrets manager, rate-limit caching, live PR check, `git push` (deferred to save mobile data).

## Accepted for v1 (M3 summary)

- **Truncated large PRs.** `core/github/diff.py`: cap 20 files / 6000 chars. Large PRs summarized partially with omission note. Accepted because v1 goal is plumbing, not insight. Revisit when summaries judged useless → M5 LLM or full file list.
- **Token-per-job waste.** One JWT + token per job. Accepted for low volume. Revisit as above.
- **Polling latency ~1s + light DB load.** `POLL_SECONDS=1.0`, partial index `jobs_claim_idx`. Accepted for prototype. Revisit when p95 enqueue-to-comment >30s.

## Verification debt

- Diff pagination covered by mocked tests only (`tests/test_diff.py`), not live GitHub. Verify on first real PR via tunnel.
- M1-2 loop verified by code read + old README claim; re-verify live after M3 (`pytest` currently 10 passed).
