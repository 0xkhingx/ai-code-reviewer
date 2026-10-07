# PROJECT.md — What We're Building and Why

> For the agent: Read this file at the start of every session, before touching any code.

---

## 1. The project in one sentence

This project is a GitHub App bot that helps developers get fast feedback on pull requests without waiting for a human reviewer.

## 2. The problem it solves

Waiting for code review is slow. A developer opens a pull request (a proposal to merge new code) and then waits. This bot posts an automatic first comment within seconds so obvious changes are visible immediately.

## 3. Who it's for

| Who | What they want to do | How technical they are |
|---|---|---|
| Solo developer / small team using GitHub | Open a PR and get an instant summary comment | Very (uses GitHub, Python, Docker) |

## 4. What "done" looks like (first version)

The smallest version that is genuinely useful (v1 = Milestone 3, deterministic, no AI cost):

1. Open a PR on a test repo → bot posts a summary comment within seconds.
2. Comment lists files changed, lines added/removed per file, and commit short hash.
3. Large PRs are truncated gracefully with a note (not crashing or spamming).

**Rule:** LLM review, static analyzers, inline comments, `.review.yml`, dashboard, deploy are NOT v1. They are Milestone 4+.

## 5. Scope

### In scope (we are building this)
- GitHub webhook verify + idempotent store + Postgres job queue (done, M1-2)
- Fetch PR diff via Files API + post deterministic summary comment (v1, M3)
- Tests for diff fetch/summary + local Docker verification

### Later (good ideas, not now)
- Static analyzers (Ruff, Bandit, ESLint, Semgrep) — M4
- LLM review behind `core/llm` — M5
- Inline comment line-mapping — M6
- Retries/stale-run hardening, `.review.yml`, eval set, dashboard, deploy — M7-11

### Out of scope (we are deliberately NOT building this)
- Paid queues/services (Redis Cloud, SQS) — we already have Postgres, free-only constraint
- Paid LLM calls in v1 — cost + secrets handling, deferred to M5

## 6. Constraints (the limits we're working inside)

| Constraint | Our situation |
|---|---|
| **Team** | Solo |
| **Time available** | Not stated — assuming nights/weekends, no hard deadline (confirm) |
| **Budget** | Free-only ($0 extra: local Docker + GitHub free tier, no LLM spend in v1) |
| **Experience level** | No prior engineering experience assumed. Explain new things once, in plain words. |
| **Devices / platforms** | GitHub web + local Docker; no mobile/offline needs |
| **Expected users** | Just me + test repo for now; dozens of PRs/day max |
| **Data sensitivity** | Holds GitHub App private key (.pem) + webhook secret — never commit, mount as secret file only |
| **Rules or regulations** | None known |
| **Deadline pressure** | Flexible |

## 7. Tech stack (what we've chosen so far)

| Part | Choice | Decision log entry |
|---|---|---|
| Language(s) | Python >=3.11 (3.12-slim in Docker) | ADR-001 |
| Back end | FastAPI + uvicorn (webhook API), standalone worker loop | ADR-001 |
| Database (where data is stored) | Postgres 16, `webhook_events` + `jobs` tables, `FOR UPDATE SKIP LOCKED` queue | ADR-002 |
| Hosting (where it runs online) | Local Docker Compose (api + worker + postgres) + tunnel (cloudflared/ngrok) for webhooks | Not logged yet |
| Other services | GitHub App (JWT → installation token), httpx client, PyJWT, psycopg pool, pytest | ADR-003 |

**Still undecided:** LLM provider/model for M5, analyzer set for M4, production hosting for M11.

## 8. Key terms specific to this project

- **review**: one automatic bot comment summarizing a PR (v1); later, findings + inline notes.
- **job**: one row in the `jobs` table meaning "review this PR".
- **diff**: line-by-line list of what a PR added/removed.

## 9. Rules for the agent on this project

- Always ask before adding a paid service or LLM spend.
- Never commit `.env` or `*.pem` files.
- Prefer free-tier/local options.
- Keep v1 deterministic — no network calls except to GitHub API.

## 10. Success checks

- Open a PR on test repo → summary comment appears in under ~10s.
- `pytest` passes locally.
- `select id,status from jobs order by id desc limit 5;` shows `done` for the PR job.

## 11. Known weak spots and open questions

- No reaper for `running` jobs stuck after crash; no jitter on retry; no cancel on new `synchronize` (M7).
- Schema init via `docker-entrypoint-initdb.d` only — breaks on schema change, needs migrations later.
- `review_pr` makes a new JWT+token per job (no caching).
- Hours/week + production hosting still unconfirmed.

---

## Change history of this file

- 2026-10-05: Created from template; filled for AI Reviewer M3 v1 (solo, free-only, diff-summary-first).
- 2026-10-07: Renamed project to firstpass (full rebrand, all lowercase).
