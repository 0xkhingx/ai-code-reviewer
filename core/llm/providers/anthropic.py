"""Anthropic provider. Price verified 2026-10-10 at
https://platform.claude.com/docs/en/about-claude/pricing — claude-haiku-5-5
$0.10/$0.50 up to 100k-token prompts, $0.50/$2.50 above. Re-verify before
changing models. Note: 4.7+ tokenizers emit ~30% more tokens per text.
"""
import httpx


def complete(
    client: httpx.Client, api_key: str, model: str, system: str, user: str,
    max_output_tokens: int = 1500,
) -> str:
    resp = client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_output_tokens,
            "temperature": 0.2,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    blocks = resp.json()["content"]
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
