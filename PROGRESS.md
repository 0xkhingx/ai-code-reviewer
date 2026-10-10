# PROGRESS.md — Where We Are Right Now

> Agent memory between sessions. Keep short, readable in two minutes.

---

## 1. Current status

**Last updated:** 2026-10-07
**Overall state:** Working prototype (renamed to firstpass, pushed)
**One-line summary:** Webhook → queue → diff summary works in code (M3 + M7 part 1); live Docker check still blocked (no Docker, no App creds locally).

**What works right now (code + mocked tests, runtime unverified live):**
- Signed webhook verify (`core/security.py`), ping/delivery handling, idempotent event store + payload validation (`apps/api/routes/webhooks.py::extract_review_target`)
- Postgres queue claim with `FOR UPDATE SKIP LOCKED`, exp backoff + jitter, `reap_stale_running`, `cancel_superseded` (`core/queue.py`)
- Worker loop + GitHub App JWT → installation token → issue comment (`apps/worker/`)
- Diff fetch via Files API + deterministic summary, capped 20 files/6000 chars (`core/github/diff.py`, `apps/worker/jobs/review_pr.py`)
- 16 pytest green (`test_signature.py` + `test_diff.py` + `test_queue_hardening.py`)

**What's broken or unfinished:**
- `core/review/`, `core/llm/` are empty stubs (M5, deferred — free-only constraint)
- Duplicate-comment edit not done (needs comment-ID storage + migration story)
- No live verification: Docker not installed, no `.env` / `github-app.pem` locally
- `docs/` ledger exists (`GLOSSARY`, `DECISIONS`, `RISKS`); `PROGRESS.md` resynced this session

---

## 2. In progress

| What | Where (files/areas) | State it's in | What's left |
|---|---|---|---|
| M7 part 2 design | `review_pr.py` duplicate-comment edit, token caching | Deciding storage approach | Pick comment-ID column vs check-before-post |
| Live check | Docker + GitHub App + tunnel | Blocked: Docker not installed, no `.env`/`.pem` | Install Docker, create App, run compose, open test PR |

If nothing else, **M7 part 2 design is the active work; live check is blocked on setup.**

---

## 3. Next up (in order)

1. Live check (needs Docker + GitHub App `.env`/`.pem` + tunnel): open test PR → single comment, updated on retry; with `LLM_API_KEY` set, real LLM review
2. Grow eval set toward 20-30 from real PRs; run `--backend llm` once keyed to pick model on evidence
3. M4 time-boxed: only analyzers a model can't do reliably (secrets/rules); cut the rest
4. Per-install key store + Postgres caps when multi-install reality arrives

---

## 4. Done

- 2026-10-10: M5 core (BYOK review, eval harness with 11 seed cases, per-install/repo/global caps, redaction, injection-safe prompts, 2 verified providers) — `pytest` 29 passed, `evals/run.py` baseline 0 hits/0 FPs, pushed
- 2026-10-07: M7 part 2: idempotent summary comments (marker upsert), token cache, reaper wired into worker loop, unknown-kind guard + 4 tests — `pytest` 20 passed, pushed
- 2026-10-07: Renamed project to firstpass (code/docs/folders/GitHub repo `0xkhingx/firstpass`, remote updated, pushed)
- 2026-10-06: M7 hardening part 1: payload validation (`extract_review_target`), retry jitter, `reap_stale_running`, `cancel_superseded` + 6 mocked tests — `pytest` 16 passed, pushed
- 2026-10-06: M3 diff fetch + summary (`core/github/diff.py`, `review_pr.py`, `tests/test_diff.py`) — `pytest` 10 passed at the time
- 2026-10-05: M1-2 proven loop (webhook → queue → comment) per README + code read

---

## 5. Open questions and decisions waiting on me

- [ ] Hours/week + deadline? — Options: nights/weekends flexible vs hard date. Agent's recommendation: assume flexible until you say otherwise.
- [ ] Production hosting for M11? — Options: stay local vs free-tier cloud. Agent's recommendation: stay local for v1, decide at M11.

---

## 6. Blockers

- None yet — needs Docker + tunnel + GitHub App test repo for manual check.

---

## 7. How to pick this up again (quick restart guide)

```bash
# 1. Go to the project folder
cd C:\Users\HP\Downloads\firstpass\firstpass

# 2. Start the project
cp .env.example .env  # fill GITHUB_APP_ID + GITHUB_WEBHOOK_SECRET once
# place github-app.pem as ./github-app.pem
docker compose up --build
cloudflared tunnel --url http://localhost:8000  # or: ngrok http 8000

# 3. Run the tests
pip install -e ".[dev]"
pytest
```

**What I should see if it's working:** `pytest` passes; opening a PR posts a summary comment in seconds.
**Common problems:** schema changes ignored (volume init-only) → `docker compose down -v` to re-init (wipes data); redelivery ignored as duplicate → expected idempotency.

---

## 8. Things the next session should know

- Schema mount `./db/schema.sql:/docker-entrypoint-initdb.d/schema.sql:ro` runs only on first volume init.
- Worker makes a fresh JWT+token per job — fine for low volume, wasteful at scale (token caching planned, M7 part 2).
- `reap_stale_running()` exists in code but nothing calls it on a schedule yet — wire into worker loop or cron in M7 part 2.
- `cancel_superseded()` is called on enqueue; `cancelled` is a new status value with no index — fine at low volume.
- Docker is NOT installed on this machine; no `.env` / `github-app.pem` locally — live check blocked until both exist.
- Don't commit `.env` / `*.pem`.

---

## 9. Session log

```
### 2026-10-05
- Goal: define v1 as diff-summary-first, start M3
- Did: filled PROJECT.md, initialized PROGRESS.md/GLOSSARY/DECISIONS; scaffolding diff.py + review_pr update
- Learned: webhook, queue, diff, job (see GLOSSARY)
- Left off at: implementing core/github/diff.py + tests
```

### Older sessions (summarized)

- None yet.
