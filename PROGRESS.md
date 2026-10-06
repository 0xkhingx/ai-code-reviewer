# PROGRESS.md — Where We Are Right Now

> Agent memory between sessions. Keep short, readable in two minutes.

---

## 1. Current status

**Last updated:** 2026-10-05
**Overall state:** Working prototype
**One-line summary:** Webhook → queue → hardcoded comment works (M1-2); M3 diff-summary in progress.

**What works right now (verified by code read, runtime unverified):**
- Signed webhook verify (`core/security.py`), ping/delivery handling, idempotent event store (`apps/api/routes/webhooks.py`)
- Postgres queue claim with `FOR UPDATE SKIP LOCKED` + exp backoff (`core/queue.py`)
- Worker loop + GitHub App JWT → installation token → issue comment (`apps/worker/`)
- Signature tests (`tests/test_signature.py`)
- M3 diff fetch + summary (`core/github/diff.py`, 5 new tests passing; 10 passed total with `pytest`)

**What's broken or unfinished:**
- `apps/worker/jobs/review_pr.py` still posts hardcoded text — no diff fetch yet (this session adds it)
- `core/review/`, `core/llm/` are empty stubs (M5, not v1)
- No `docs/` ledger yet (this session adds it)

---

## 2. In progress

| What | Where (files/areas) | State it's in | What's left |
|---|---|---|---|
| M3 diff summary | `core/github/diff.py` (new), `apps/worker/jobs/review_pr.py`, `tests/test_diff.py` | Code to be written this session | Implement + `pytest` + Docker manual check |
| Project memory | `PROJECT.md`, `PROGRESS.md`, `docs/GLOSSARY.md`, `docs/DECISIONS.md` | Filling now | Copy review + confirm hours/hosting |

If nothing else, **M3 diff summary is the active work.**

---

## 3. Next up (in order)

1. Manual check M3: `docker compose up --build` + tunnel + open test PR → summary comment (runtime unverified)
2. M7 hardening (queued per 2026-10-06 prod review, see `docs/RISKS.md`): payload validation, jitter, `running` reaper, supersede-cancel, edit-instead-of-duplicate comments
3. M4: static analyzers (Ruff/Bandit) — needs Dockerfile + Node decisions
4. M5: LLM review behind `core/llm` (needs provider + budget decision — currently free-only, so deferred)

---

## 4. Done

- 2026-10-06: M3 diff fetch + summary (`core/github/diff.py`, `review_pr.py`, `tests/test_diff.py`) — `pytest` 10 passed
- 2026-10-06: Prod-readiness review → `docs/RISKS.md` created, NOT prod ready (dev runtime, no migrations, no reaper)
- 2026-10-05: M1-2 proven loop (webhook → queue → hardcoded comment) per README + code read (runtime re-verify pending)

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
cd C:\Users\HP\Downloads\ai-code-reviewer\ai-code-reviewer

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
- Worker makes a fresh JWT+token per job — fine for low volume, wasteful at scale.
- No `running` reaper — crashed-after-claim without rollback can stick; restart + manual `status='queued'` reset is the current workaround.
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
