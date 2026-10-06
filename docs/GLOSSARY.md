# GLOSSARY.md — Explained-once ledger

> Per AGENTS.md §2: every new term explained once here, one line each. Check before re-explaining.

## Git / GitHub
- **Pull request (PR)**: a proposal to merge new code, with discussion attached.
- **Webhook**: GitHub calling our server automatically when something happens (like a new PR).
- **Delivery ID**: GitHub's unique ID per webhook send (`X-GitHub-Delivery`), used to ignore repeats.
- **GitHub App**: an installed identity that grants our bot scoped repo permissions.
- **Installation**: one install of the App on an account/repo, with its own numeric ID.
- **Installation token**: short-lived credential minted from the App key to call GitHub as the installation.
- **JWT (JSON Web Token)**: short signed token proving we hold the App private key, exchanged for an installation token.
- **Diff**: line-by-line list of what a PR added/removed.
- **Patch**: per-file diff text for one file in a PR.
- **Files API**: `GET /repos/{repo}/pulls/{pr}/files`, paginated per-file diff + counts.

## Web / API
- **FastAPI**: Python toolkit for building web APIs (our webhook receiver).
- **Endpoint**: one URL + method our server answers (e.g. `POST /webhooks/github`).
- **HMAC signature**: keyed hash of the raw body proving the request came from GitHub.
- **Idempotent**: repeated delivery has no extra effect (second insert ignored as duplicate).

## Database / Queue
- **Postgres**: the database storing events and jobs.
- **Table**: labeled grid of rows in the database (like a spreadsheet tab).
- **Row**: one record in a table.
- **Transaction**: a group of database steps that either all succeed or all get undone.
- **Queue**: a waiting line of tasks to be done later, in order.
- **Worker**: a separate program whose only job is to pick tasks off the queue and do them.
- **Job**: one row in the `jobs` table meaning "review this PR".
- **Claim**: worker atomically marking one `queued` job as `running` so no other worker grabs it.
- **`FOR UPDATE SKIP LOCKED`**: Postgres clause letting concurrent workers skip rows locked by each other.
- **Backoff**: waiting longer between retries (5,10,20s…) to avoid hammering a failing dependency.
- **Jitter**: small random extra delay added to backoff so many workers don't retry at the same instant.
- **Reaper**: background cleanup that resets `running` jobs stuck past a timeout back to `queued`.
- **Migration**: versioned script that changes database tables safely on an existing database.
- **Connection pool**: reused set of database connections shared by threads.

## Runtime / Tooling
- **Environment variable**: named setting outside code (like `DATABASE_URL`) so secrets aren't in files.
- **Docker Compose**: tool running api + worker + postgres together from one file.
- **Tunnel (cloudflared/ngrok)**: temporary public URL forwarding to `localhost:8000` so GitHub can reach us.
- **Deterministic summary**: fixed-format comment from counts only, no AI involved.
- **Truncation**: cutting a large diff to a size cap and noting what was omitted.
