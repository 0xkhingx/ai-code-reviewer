# PRIVACY.md — What happens to your code

> Shown to anyone installing the bot. Plain words, no legalese. Updated 2026-10-10.

## When no LLM key is configured (default)

Nothing leaves GitHub except API calls to fetch the diff and post the comment.
No third party sees your code. Cost: $0.

## When you plug in your own key (BYOK)

- **What leaves:** the PR diff (up to `LLM_MAX_INPUT_CHARS`, default 60,000 chars),
  after local secret scrubbing (AWS keys, GitHub/Slack tokens, PEM blocks,
  `password=`/`api_key=` assignments → `[REDACTED]`).
- **To whom:** only the provider you chose (`LLM_PROVIDER`: `openai` or `anthropic`),
  billed to **your** key. firstpass holds no billing risk and pays nothing.
- **Retention:** we set nothing custom — the provider's own policy for your
  account applies. Check it before installing:
  - OpenAI: https://developers.openai.com/api/docs/guides/your-data
  - Anthropic: https://platform.claude.com/docs/en/about-claude/data-usage
- **What we never do:** follow instructions inside the diff (treated as untrusted),
  execute model output (rendered as a comment only), log your API key or raw secrets.

## Data we store

Webhook payloads + job rows in Postgres (`webhook_events`, `jobs`) — needed for
idempotency and retries. No diffs are stored beyond the job payload metadata
(repo, PR number, commit hash).
