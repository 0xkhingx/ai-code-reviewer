import time
from datetime import datetime, timezone

import httpx
import jwt

API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# installation_id -> (token, expires_at_epoch). Single-worker process cache
# so rapid pushes on the same repo don't mint a token per job.
_TOKEN_CACHE: dict[int, tuple[str, float]] = {}
_EXPIRY_BUFFER_SECONDS = 60


def app_jwt(app_id: str, private_key: str) -> str:
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 9 * 60, "iss": str(app_id)}
    return jwt.encode(payload, private_key, algorithm="RS256")


def _parse_expiry(expires_at: str | None) -> float:
    if not expires_at:
        return time.time() + 50 * 60  # assume ~50min when API omits it
    return (
        datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .timestamp()
    )


def installation_token(
    client: httpx.Client, app_id: str, private_key: str, installation_id: int
) -> str:
    cached = _TOKEN_CACHE.get(installation_id)
    if cached and cached[1] - _EXPIRY_BUFFER_SECONDS > time.time():
        return cached[0]
    resp = client.post(
        f"{API}/app/installations/{installation_id}/access_tokens",
        headers={**HEADERS, "Authorization": f"Bearer {app_jwt(app_id, private_key)}"},
    )
    resp.raise_for_status()
    data = resp.json()
    _TOKEN_CACHE[installation_id] = (data["token"], _parse_expiry(data.get("expires_at")))
    return data["token"]
