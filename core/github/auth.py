import time

import httpx
import jwt

API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def app_jwt(app_id: str, private_key: str) -> str:
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 9 * 60, "iss": str(app_id)}
    return jwt.encode(payload, private_key, algorithm="RS256")


def installation_token(
    client: httpx.Client, app_id: str, private_key: str, installation_id: int
) -> str:
    resp = client.post(
        f"{API}/app/installations/{installation_id}/access_tokens",
        headers={**HEADERS, "Authorization": f"Bearer {app_jwt(app_id, private_key)}"},
    )
    resp.raise_for_status()
    return resp.json()["token"]
