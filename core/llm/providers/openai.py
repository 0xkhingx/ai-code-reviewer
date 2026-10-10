"""OpenAI provider. Price verified 2026-10-10 at
https://developers.openai.com/api/docs/pricing — gpt-6-luna $0.10 in /
$0.50 out per 1M (short context). Re-verify before changing models.
"""
import httpx


def complete(
    client: httpx.Client, api_key: str, model: str, system: str, user: str,
    max_output_tokens: int = 1500,
) -> str:
    resp = client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_output_tokens,
            "temperature": 0.2,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
