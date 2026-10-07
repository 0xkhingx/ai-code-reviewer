# firstpass

GitHub App → FastAPI webhook → Postgres job queue → worker → PR comments.

Current state: **milestones 1–2**. A signed `pull_request` webhook is verified, stored
(idempotent on delivery ID), turned into a Postgres job, claimed by a worker with
`FOR UPDATE SKIP LOCKED`, and the worker posts a hardcoded comment on the PR.
No LLM yet, on purpose: this proves every integration point first.

## 1. Create the GitHub App
GitHub → Settings → Developer settings → GitHub Apps → New GitHub App.

- **Webhook URL:** your tunnel URL + `/webhooks/github` (see step 3)
- **Webhook secret:** any random string (goes in `.env`)
- **Repository permissions:** Pull requests: Read & write · Contents: Read · Metadata: Read
- **Subscribe to events:** Pull request
- After creating: note the **App ID**, generate a **private key** (.pem), then **Install App** on a test repo.

## 2. Configure
```bash
cp .env.example .env          # fill in GITHUB_APP_ID and GITHUB_WEBHOOK_SECRET
mv ~/Downloads/<your-key>.pem ./github-app.pem
```

## 3. Run
```bash
docker compose up --build
cloudflared tunnel --url http://localhost:8000   # or ngrok http 8000
```
Paste the tunnel URL (+ `/webhooks/github`) into the App's webhook settings.
Open a PR on the test repo. Within a couple of seconds the bot comments.

## 4. Test
```bash
pip install -e ".[dev]"
pytest
```

## Debugging
- GitHub App → Advanced → Recent Deliveries shows each webhook and lets you redeliver it
  (redelivery is ignored as a duplicate, which is the idempotency check working).
- `docker compose exec postgres psql -U reviewer -c "select id,status,attempts,last_error from jobs order by id desc limit 5;"`

## Next milestones
3. Fetch the PR diff · 4. Static analyzers (Ruff, Bandit, ESLint, Semgrep) · 5. LLM review behind
`core/llm` · 6. Inline comment line-mapping · 7. Retries/stale-run cancellation hardening ·
8. `.review.yml` · 9. Evaluation set · 10. Dashboard · 11. Deploy.
