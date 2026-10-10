import httpx

from core.config import load_settings
from core.github.auth import installation_token
from core.github.client import upsert_summary_comment
from core.github.diff import fetch_pr_files, summarize_files


def run(payload: dict) -> None:
    """Milestone 3 + M7 part 2: real diff, idempotent summary comment (no LLM yet)."""
    s = load_settings()
    with httpx.Client(timeout=30) as client:
        token = installation_token(
            client, s.github_app_id, s.github_private_key, payload["installation_id"]
        )
        files = fetch_pr_files(
            client, token, payload["repo_full_name"], payload["pr_number"]
        )
        body = summarize_files(files, payload["head_sha"])
        upsert_summary_comment(
            client,
            token,
            payload["repo_full_name"],
            payload["pr_number"],
            body,
        )
